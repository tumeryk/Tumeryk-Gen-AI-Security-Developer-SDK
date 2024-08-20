from fastapi import APIRouter, Form, BackgroundTasks, Request, HTTPException
from fastapi.responses import HTMLResponse
import time
import jwt
import os
from utils.user_data import get_user_data
from utils.logger import log_interaction
from utils.api_client import client
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from fastapi.responses import RedirectResponse

load_dotenv()  # Load environment variables from .env

templates = Jinja2Templates(directory="templates")
router = APIRouter()
api_client = client
# Move the JWT secret key to an environment variable
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


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
        user_data.chat_responses.append(chat_response)

        background_tasks.add_task(
            runasync, user_input, user, user_data, chat_response, bot_response_time
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


def runasync(user_input, user_name, user_data, chat_response, bot_response_time):

    # Measure guard response time
    guard_response, guard_response_time = measure_time(
        api_client.chat_guard, user_input
    )

    # Assume that a violation is determined based on the guard's response
    violation = False
    if guard_response == "Sorry, I can't assist with that.":
        violation = True

    # Append logs to user_data
    user_data.guard.append(user_input)
    user_data.guard_log.append(chat_response)

    # Log the interaction
    log_interaction(
        user=user_name,
        role="user",
        message=user_input,
        bot_response_time=f"{bot_response_time:.2f}",
        guard_response_time=f"{guard_response_time:.2f}",
        model=api_client.user_data.models[user_data.config_id]["model_name"],
        config_id=user_data.config_id,
        bot_response=chat_response,
        guard_response=guard_response,
        violation=violation,
    )


@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    """Render the reports page showing logs and responses."""
    config_id = None
    cookie = request.cookies.get("proxy")
    user_data = None  # Initialize user_data to None

    if cookie:
        try:
            decode = jwt.decode(cookie, algorithms="HS256", key=JWT_SECRET_KEY)
            user = decode.get("sub")
            user_data = get_user_data(user)  # Retrieve the UserData object
            # Directly access the config_id attribute
            config_id = getattr(user_data, "config_id", None)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=403, detail="Invalid token")

    if user_data is None:
        raise HTTPException(status_code=403, detail="User data not found")

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
