#Copyright © 2024 Tumeryk, Inc.

from fastapi import APIRouter, Form, BackgroundTasks, Request, HTTPException
from fastapi.responses import HTMLResponse
import time
import jwt
import os
from tumeryk_proxy.user_data import get_user_data
from tumeryk_proxy.logger import log_interaction
from tumeryk_proxy.api_client import client
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from fastapi.responses import RedirectResponse
from tumeryk_proxy.logger import fetch_logs
import re

load_dotenv()  # Load environment variables from .env

templates = Jinja2Templates(directory="templates")
router = APIRouter()
api_client = client
# Move the JWT secret key to an environment variable
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY","abc1234")


def measure_time(func, *args, **kwargs):
    """
    Utility function to measure the execution time of a function in  seconds.
    """
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
    request: Request, background_tasks: BackgroundTasks, user_input: str = Form()
):
    """Handle chat input and generate a response using the selected model."""
    post_cookie = request.cookies.get("proxy")

    if not post_cookie:
        raise HTTPException(status_code=403, detail="Authentication cookie missing")

    try:
        decode = jwt.decode(post_cookie, algorithms="HS256", key=JWT_SECRET_KEY)
        user = decode.get("sub")
        user_data = get_user_data(user)
        api_client.token = post_cookie  # Set the token for the API client

        chat_response, bot_response_time = measure_time(api_client.chat, user_input)
        user_data.chat_log.append(user_input)
        user_data.chat_responses.append(chat_response.choices[0].message.content)
        bot_tokens = chat_response.usage.completion_tokens
        background_tasks.add_task(
            runasync, user_input, user, user_data, chat_response.choices[0].message.content, bot_response_time,bot_tokens
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


def runasync(user_input, user_name, user_data, chat_response, bot_response_time, bot_tokens):

    # Measure guard response time
    guard_response, guard_response_time = measure_time(
        api_client.chat_guard, user_input
    )
    message  = guard_response['messages'][0]['content']
    stats = guard_response['messages'][0]['Stats']
    guard_tokens =  int(re.search(r'(\d+) total completion tokens', stats).group(1))

    violation = guard_response['messages'][0]['violation']

    # Append logs to user_data
    user_data.guard.append(user_input)
    user_data.guard_log.append(guard_response)

    # Log the interaction
    log_interaction(
        user=user_name,
        message=user_input,
        bot_response_time=f"{bot_response_time:.2f}",
        guard_response_time=f"{guard_response_time:.2f}",
        engine=api_client.user_data.models[api_client.user_data.config_id]["engine"],
        model=api_client.user_data.models[api_client.user_data.config_id]["model"],
        config_id=api_client.user_data.config_id,
        bot_response=chat_response,
        guard_response=message,
        violation=violation,
        bot_tokens = bot_tokens,
        guard_tokens=guard_tokens
    )


@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    """Render the reports page showing logs and responses."""
    cookie = request.cookies.get("proxy")
    if cookie:
        try:
            decode = jwt.decode(cookie, algorithms="HS256", key=JWT_SECRET_KEY)
            user = decode.get("sub")
            user_data = get_user_data(user)
            
            # Fetch log data
            logs = fetch_logs(user)
            print(logs)
            
            return templates.TemplateResponse(
                "report.html",
                {
                    "request": request,
                    "logs": logs,
                    "config_id": api_client.user_data.config_id,
                },
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=403, detail="Invalid token")
    
    raise HTTPException(status_code=403, detail="Authentication required")