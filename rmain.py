import os
import csv
import uvicorn
import requests
from fastapi import (
    FastAPI,
    Form,
    Depends,
    BackgroundTasks,
    Request,
    status,
    HTTPException,
)
from pydantic import BaseModel, SecretStr
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_community.llms import Cohere, Anthropic, HuggingFaceHub
from langchain.prompts import PromptTemplate
import asyncio
import jwt
import logging
from datetime import datetime

LOG_DIRECTORY = './logs'

def setup_logger(user: str):
    """Set up and return a logger configured to write to a user-specific file."""
    today = datetime.now().strftime('%Y-%m-%d')
    user_log_dir = os.path.join(LOG_DIRECTORY, user)
    os.makedirs(user_log_dir, exist_ok=True)
    
    log_file_path = os.path.join(user_log_dir, f"{today}.log")
    
    # Create a custom logger
    logger = logging.getLogger(user)
    logger.setLevel(logging.INFO)

    # Create handlers
    file_handler = logging.FileHandler(log_file_path)

    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    
    return logger

class UserData:
    """Class to store data associated with each user."""
    def __init__(self):
        self.chat_log = []
        self.chat_responses = []
        self.guard = []
        self.guard_log = []
        self.guard_log_response = []

db_dict = {}

def get_user_data(username: str) -> UserData:
    """Retrieve or create the UserData for the specified user."""
    if username not in db_dict:
        db_dict[username] = UserData()
    return db_dict[username]



url = "http://chat-dev.tmryk.com"  # customer input value

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/creds/")


class User(BaseModel):
    """Model for user credentials."""
    username: str
    passwd: SecretStr


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Retrieve and validate the current user based on the token."""
    if token is None or len(token) <= 20:
        raise HTTPException(status_code=400, detail="Incorrect User Credentials")
    return token

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    """Return the current active user."""
    return current_user

def guard_notification(guard_chat_note: str, cookie=None, config_id=None, username=None):
    """Send an input to the GuardAI service."""
    token = cookie
    header = {"Authorization": f"Bearer {token}"}
    guard_url = f"{url}/v1/chat/completions"
    if not config_id:
        return {"error": "Config ID is required"} 
    
    role = {"role": "user", "content": guard_chat_note}
    payload = {"config_id": config_id, "messages": [role], "stream": False}
    
    user_data = get_user_data(username)
    
    try:
        response = requests.post(guard_url, json=payload, headers=header)
        msg = response.json()
        user_data.guard_log.append({"config_id": config_id, "log": msg.get("messages")[-1].get("content")})
    except Exception as err:
        print(str(err))

def response_notification(guard_chat_note: str, cookie=None, config_id=None, username=None):
    """Send a bot response to the GuardAI service."""
    token = cookie
    header = {"Authorization": f"Bearer {token}"}
    guard_url = f"{url}/v1/chat/completions"
    if not config_id:
        return {"error": "Config ID is required"} 
    
    role = {"role": "user", "content": guard_chat_note}
    payload = {"config_id": config_id, "messages": [role], "stream": False}
    
    user_data = get_user_data(username)
    
    try:
        response = requests.post(guard_url, json=payload, headers=header)
        msg = response.json()
        user_data.guard_log_response.append({"config_id": config_id, "log": msg.get("messages")[-1].get("content")})
    except Exception as err:
        print(str(err))

@app.post("/login")
def login_test(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    """Authenticate user and redirect to portal if successful."""
    payload = {"grant_type": "password", "username": username, "password": password}
    try:
        response = requests.post(f"{url}/auth/token", data=payload)
        res = response.json()
        if res.get("access_token") is not None:
            tok = res.get("access_token")
            user_data = get_user_data(username)  # Retrieve or create UserData for the user
            
            # Update user data with token and credentials
            db_dict[username].access_token = tok
            db_dict[username].username = username
            db_dict[username].password = password
            
            try:
                configs_response = requests.get(
                    f"{url}/v1/rails/configs",
                    headers={
                        "accept": "application/json",
                        "Authorization": f"Bearer {tok}",
                    },
                )
                configs_response.raise_for_status()
                configs_list = [config.get("id") for config in configs_response.json() if config.get("id")]
                db_dict[username].configs = configs_list  # Ensure configs are stored in UserData

                resp = RedirectResponse(url="/portal", status_code=status.HTTP_302_FOUND)
                resp.set_cookie("proxy", value=tok)
                return resp
            except requests.exceptions.RequestException as e:
                raise HTTPException(status_code=500, detail="Error fetching configs")
    except Exception as err:
        return {"error": str(err)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home (login) page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/creds/")
async def login(user: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Endpoint for user login, returning an access token."""
    payload = {
        "grant_type": "password",
        "username": user.username,
        "password": user.password,
    }
    try:
        response = requests.post(f"{url}/auth/token", data=payload)
        res = response.json()
        if res.get("access_token") is not None:
            db_dict[user.username] = {
                "access_token": res.get("access_token"),
                "username": user.username,
                "password": user.password,
            }
            return {"access_token": res.get("access_token")}
        raise HTTPException(status_code=400, detail="User Does not exist")
    except Exception as err:
        print(err)


@app.get("/portal", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render the chat portal page if the user is authenticated."""
    cookie = request.cookies.get("proxy")
    if cookie:
        decode = jwt.decode(cookie, algorithms="HS256", key="abc1234")
        user = decode.get("sub")
        user_data = get_user_data(user)
        if user in db_dict.keys():
            configs_list = user_data.configs if hasattr(user_data, 'configs') else []  # Access configs directly
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "chat_responses": user_data.chat_responses,
                    "guard_log": user_data.guard_log,
                    "configs_list": configs_list,
                },
            )
        
    return templates.TemplateResponse(
        "login.html", {"request": request}
    )
def log_interaction(user: str, role: str, message: str, bot_response_time: float, guard_response_time: float, 
                    model: str, config_id: str, bot_response: str, guard_response: str, violation: bool):
    """Log the interaction using Python's logging library in a modified key-value format."""
    logger = setup_logger(user)
    
    # Prepare the log message with quoted string values and a unique delimiter
    log_message = f'role="{role}" | message="{message}" | bot_response_time={bot_response_time} | ' \
                  f'guard_response_time={guard_response_time} | model="{model}" | config_id="{config_id}" | ' \
                  f'bot_response="{bot_response}" | guard_response="{guard_response}" | violation={violation}'
    
    # Log the interaction
    logger.info(log_message)
def process_interaction(user, user_input, bot_response_time, config_id, bot_response,cookie):
    """Process interaction after guard notification completes."""
    guard_notification(
        guard_chat_note=user_input,
        cookie=cookie,  # Pass the appropriate cookie if needed
        config_id=config_id,
        username=user,
    )

    user_data = get_user_data(user)
    guard_response = user_data.guard_log[-1] if user_data.guard_log else {"log": ""}
    violation = bool(guard_response["log"])

    log_interaction(
        user=user,
        role="user",
        message=user_input,
        bot_response_time=bot_response_time,
        guard_response_time=0,
        model="gpt-3.5-turbo",
        config_id=config_id,
        bot_response=bot_response,
        guard_response=guard_response["log"],
        violation=violation,
    )

@app.post("/portal", response_class=HTMLResponse)
async def chat(
    request: Request,
    user_input: Annotated[str, Form()],
    background_tasks: BackgroundTasks,
    model_config: Annotated[dict, Form()] = None
):
    """Handle chat input and generate a response using the selected model."""
    post_cookie = request.cookies.get("proxy")
    decode = jwt.decode(post_cookie, algorithms="HS256", key="abc1234")
    user = decode.get("sub")

    if user not in db_dict:
        raise HTTPException(status_code=400, detail="User not found")

    user_data = get_user_data(user)
    config_id = getattr(user_data, "config_id", None)  # Use getattr to safely access config_id

    if not config_id:
        raise HTTPException(status_code=400, detail="Config ID not set")

    configs_list = getattr(user_data, "configs", [])
    bot_start_time = datetime.now()
    chain = get_llm_chain(user, config_id, post_cookie)
    response = chain.run(question=user_input)
    bot_response_time = (datetime.now() - bot_start_time).total_seconds()

    user_data.chat_log.append({"role": "user", "content": user_input})
    user_data.guard.append(user_input)
    user_data.chat_responses.append(response)


    background_tasks.add_task(
        process_interaction,
        user=user,
        user_input=user_input,
        bot_response_time=bot_response_time,
        config_id=config_id,
        bot_response=response,
        cookie=post_cookie
    )

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "chat_responses": user_data.chat_responses,
            "configs_list": configs_list,
        },
    )


@app.get("/reports", response_class=HTMLResponse)
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

@app.get("/debug")
async def debug_info():
    """Return debugging information."""
    return db_dict

@app.get("/config_id")
async def set_config(config_id: str, request: Request):
    """Set the configuration ID to be used by the user."""
    cookie = request.cookies.get("proxy")
    if cookie:
        try:
            decode = jwt.decode(cookie, algorithms="HS256", key="abc1234")
            user_info = decode.get("sub")
            user_data = get_user_data(user_info)  # Get the UserData instance

            # Assign the config_id directly to the UserData instance
            user_data.config_id = config_id
            
            return {"config": f"config to use in proxy: {config_id}"}
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}
    return {"error": "missing credential info or could not find config"}

@app.post("/chat")
async def chat(
    user_input: Annotated[str, Form()],
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_active_user)],
    model_name="openAI"
):
    """Handle chat input and generate a response for API-only requests."""
    config_id = None
    if user:
        decode = jwt.decode(user, algorithms="HS256", key="abc1234")
        user_info = decode.get("sub")
        user_data = get_user_data(user_info)
        if user_info in db_dict.keys():
            config_id = user_data.get("config_id")
            if not config_id:
                raise HTTPException(status_code=400, detail="Config ID not set")
            user_data.chat_log.append({"role": "user", "content": user_input})
            user_data.guard.append(user_input)

            chain = get_llm_chain(user_info, config_id, user)
            response = chain.run(question=user_input)

            bot_response = response
            user_data.chat_responses.append(bot_response)
            background_tasks.add_task(
                guard_notification,
                guard_chat_note=user_input,
                cookie=user,
                config_id=config_id,
            )
            background_tasks.add_task(
                response_notification,
                guard_chat_note=bot_response,
                cookie=user,
                config_id=config_id,
            )
            return bot_response
    return {"error": "guard credential errors"}


@app.post("/guard")
async def chat(guard_chat: str, config: str):
    """Send a chat message to GuardAI using the provided configuration."""
    token = db_dict.get("access_token")
    header = {"Authorization": f"Bearer {token}"}
    guard_url = f"{url}/v1/chat/completions"
    role = {"role": "user", "content": guard_chat}
    payload = {"config_id": config, "messages": [role], "stream": False}
    try:
        response = requests.post(guard_url, json=payload, headers=header)
        return response.text
    except Exception as err:
        return str(err)

def get_llm(model_name: str, api_key_value: str, **kwargs):
    """Return the appropriate LLM based on the model name, including a request for the API key."""
    # Select the LLM based on the model name
    if model_name == "openai":
        return ChatOpenAI(model=kwargs.get("model", "gpt-3.5-turbo"), temperature=kwargs.get("temperature", 0.6), openai_api_key=api_key_value)
    elif model_name == "cohere":
        return Cohere(api_key=api_key_value)
    elif model_name == "anthropic":
        return Anthropic(api_key=api_key_value)
    elif model_name == "huggingface":
        return HuggingFaceHub(repo_id="gpt2", huggingfacehub_api_token=api_key_value)
    else:
        raise ValueError("Unsupported model name")

def get_llm_chain(username: str, config: str, cookie: str):
    """Create and return an LLM chain with a prompt template, using db_dict for caching."""

    # Ensure the user's cache exists in db_dict
    user_data = get_user_data(username)

    # Check if the API key is already cached for this config
    api_key_data = None
    if hasattr(user_data, 'api_key_data') and config in user_data.api_key_data:
        api_key_data = user_data.api_key_data[config]
    else:
        # Make the synchronous API request to get the API key and model name
        headers = {"Authorization": f"Bearer {cookie}"}
        response = requests.get(f"{url}/llm_api_key", headers=headers, params={"config_id": config})
        response.raise_for_status()
        api_key_data = response.json().get("api_key_value_pair")
        
        if not api_key_data:
            raise RuntimeError("API response did not contain 'api_key_value_pair'.")

        # Cache the API key data in the UserData object
        if not hasattr(user_data, 'api_key_data'):
            user_data.api_key_data = {}
        user_data.api_key_data[config] = api_key_data

    api_key_name = api_key_data.get("api_key_name")
    api_key_value = api_key_data.get("api_key_value")
    
    if not api_key_name or not api_key_value:
        raise RuntimeError("API key name or value missing in the response.")

    # Extract model_name from api_key_name
    model_name = api_key_name.split("_")[0]  # Example: "openai_api_key" -> "openai"

    # Check if the model is already cached for this user and config
    llm = None
    if hasattr(user_data, 'models') and config in user_data.models:
        llm = user_data.models[config]
    else:
        # Get the LLM based on the model name and API key value
        llm = get_llm(model_name, api_key_value)
        # Cache the model in the UserData object
        if not hasattr(user_data, 'models'):
            user_data.models = {}
        user_data.models[config] = llm

    # Define the prompt template
    prompt_template = PromptTemplate(
        input_variables=["question"],
        template="You are a helpful assistant. Answer the following question: {question}",
    )

    # Return the LLMChain with the LLM and prompt template
    return LLMChain(llm=llm, prompt=prompt_template)

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8002, reload=True)