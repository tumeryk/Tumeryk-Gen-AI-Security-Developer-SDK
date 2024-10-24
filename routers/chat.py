#Copyright © 2024 Tumeryk, Inc.

from fastapi import APIRouter, Form, BackgroundTasks, Request, HTTPException
from fastapi.responses import HTMLResponse
import time
import jwt
import os
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import tumeryk_guardrails
from .user_data import get_user_data, log_interaction, fetch_logs
from .bot_client import bot_client

load_dotenv()

templates = Jinja2Templates(directory="templates")
router = APIRouter()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "abc1234")

def measure_time(func, *args, **kwargs):
    """Utility function to measure the execution time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return result, elapsed_time

@router.get("/portal", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render the chat portal page if the user is authenticated."""
    cookie = request.cookies.get("proxy")
    if cookie:
        try:
            decode = jwt.decode(cookie, algorithms="HS256", key=JWT_SECRET_KEY)
            user = decode.get("sub")
            user_data = get_user_data(user)
            
            # Get available policies
            policies = tumeryk_guardrails.get_policies()
            user_data.configs = policies
            
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "chat_responses": user_data.chat_responses,
                    "configs_list": user_data.configs,
                },
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=403, detail="Invalid token")
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/portal", response_class=HTMLResponse)
async def chat(
    request: Request, 
    background_tasks: BackgroundTasks, 
    user_input: str = Form(),
    config_name: str = Form()
):
    """Handle chat input and generate a response using both bot and guard."""
    post_cookie = request.cookies.get("proxy")

    if not post_cookie:
        raise HTTPException(status_code=403, detail="Authentication cookie missing")

    try:
        decode = jwt.decode(post_cookie, algorithms="HS256", key=JWT_SECRET_KEY)
        user = decode.get("sub")
        user_data = get_user_data(user)

        # Format messages
        messages = [{"role": "user", "content": user_input}]
        
        # Get bot response using configured model
        bot_response, bot_response_time = measure_time(
            bot_client.get_completion,
            messages=messages,
            config_id=config_name
        )
        
        # Get guard response using tumeryk_guardrails
        guard_response, guard_response_time = measure_time(
            tumeryk_guardrails.tumeryk_completions,
            messages=messages
        )

        # Extract guard response details
        guard_message = guard_response['messages'][0]['content']
        stats = guard_response['messages'][0]['stats']  # Updated stats path
        violation = guard_response['messages'][0]['violation']
        guard_tokens = stats['total_completion_tokens']  # Get tokens from new stats structure
        
        # Update user data
        user_data.chat_log.append(user_input)
        user_data.chat_responses.append(bot_response.choices[0].message.content)
        user_data.guard_log.append(guard_response)
        user_data.guard.append(user_input)

        # Get model info for logging
        model_info = user_data.models[config_name]

        # Log the interaction in background
        background_tasks.add_task(
            log_interaction,
            user=user,
            message=user_input,
            bot_response_time=f"{bot_response_time:.2f}",
            guard_response_time=f"{guard_response_time:.2f}",
            engine=model_info["engine"],
            model=model_info["model"],
            config_id=config_name,
            bot_response=bot_response.choices[0].message.content,
            guard_response=guard_message,
            violation=violation,
            bot_tokens=bot_response.usage.completion_tokens,
            guard_tokens=guard_tokens
        )

        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "chat_responses": user_data.chat_responses,
                "configs_list": user_data.configs,
            },
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    """Render the reports page showing logs and responses."""
    cookie = request.cookies.get("proxy")
    if cookie:
        try:
            decode = jwt.decode(cookie, algorithms="HS256", key=JWT_SECRET_KEY)
            user = decode.get("sub")
            
            # Fetch log data
            logs = fetch_logs(user)
            
            return templates.TemplateResponse(
                "report.html",
                {
                    "request": request,
                    "logs": logs
                },
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token has expired")

    
    raise HTTPException(status_code=403, detail="Authentication required")
