from fastapi import APIRouter, Form, BackgroundTasks, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
import time
import jwt

from utils.user_data import get_user_data
from utils.logger import log_interaction
from utils.api_client import client
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()
api_client = client

@router.get("/portal", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render the chat portal page if the user is authenticated."""
    cookie = request.cookies.get("proxy")
    if cookie:
        decode = jwt.decode(cookie, algorithms="HS256", key="abc1234")
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
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/portal", response_class=HTMLResponse)
async def chat(
    request: Request,
    background_tasks: BackgroundTasks,
    user_input: str = Form()
):
    """Handle chat input and generate a response using the selected model."""
    post_cookie = request.cookies.get("proxy")
    decode = jwt.decode(post_cookie, algorithms="HS256", key="abc1234")
    user = decode.get("sub")

    user_data = get_user_data(user)



    api_client.token = post_cookie  # Set the token for the API client

    background_tasks.add_task(runasync,user_input,user,user_data)
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "chat_responses": user_data.chat_responses,
            "configs_list": user_data.configs,
        },
    )

def runasync(input,user_name,user_data):


    start_bot_time = time.time()
    chat_response = api_client.chat(input)
    end_bot_time = time.time()
    bot_response_time = end_bot_time - start_bot_time

    # Start timing the guard response
    start_guard_time = time.time()
    guard_response = api_client.chat_guard(input)
    end_guard_time = time.time()
    guard_response_time = end_guard_time - start_guard_time

    # Assume that a violation is determined based on the guard's response
    violation = False
    if guard_response == "Sorry, I can't assist with that.":
        violation = True
    
    user_data.chat_log.append(input)
    user_data.chat_responses.append(chat_response)
    user_data.guard.append(input)
    user_data.guard_log.append(chat_response)
    # Log the interaction
    log_interaction(
        user=user_name,
        role="user", 
        message=input, 
        bot_response_time=bot_response_time, 
        guard_response_time=guard_response_time, 
        model = api_client.user_data.models[user_data.config_id]["model_name"],
        config_id= user_data.config_id,
        bot_response=chat_response, 
        guard_response=guard_response, 
        violation=violation
    )

@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    """Render the reports page showing logs and responses."""
    config_id = None
    cookie = request.cookies.get("proxy")
    if cookie:
        decode = jwt.decode(cookie, algorithms="HS256", key="abc1234")
        user = decode.get("sub")
        user_data = get_user_data(user)  # Retrieve the UserData object

        # Directly access the config_id attribute
        config_id = getattr(user_data, "config_id", None)
    print(user_data.chat_responses,user_data.guard_log)
    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "chat_log": user_data.chat_log,
            "chat_log_responses": user_data.chat_responses,
            "guard": user_data.guard,
            "guard_log": user_data.guard_log,
            "guard_log_responses": user_data.guard_log_response,
            "config_id": config_id,
        },
    )
