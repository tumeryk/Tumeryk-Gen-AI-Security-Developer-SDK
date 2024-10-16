#Copyright © 2024 Tumeryk, Inc.

from fastapi import (
    APIRouter,
    Form,
    Depends,
    Request,
    status,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from tumeryk_proxy.api_client import client
from tumeryk_proxy.user_data import get_user_data
import requests
import os

router = APIRouter()
api_client = client
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/creds/")
templates = Jinja2Templates(directory="templates")
url = os.getenv("BASE_URL","https://chat.tmryk.com")


@router.post("/login")
def login_test(username: str = Form(), password: str = Form()):
    """Authenticate user and redirect to portal if successful."""
    token_response = api_client.login(username, password)
    if token_response.get("access_token"):
        api_client.token = token_response["access_token"]
        user_data = get_user_data(username)

        user_data.access_token = api_client.token
        user_data.username = username
        user_data.password = password

        try:
            configs_response = requests.get(
                f"{url}/v1/rails/configs",
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {user_data.access_token}",
                },
            )
            configs_response.raise_for_status()

            configs_list = [
                config.get("id")
                for config in configs_response.json()
                if config.get("id")
            ]
            # print(configs_list)
            user_data.configs = configs_list  # Ensure configs are stored in UserData
            print(user_data.configs)
            resp = RedirectResponse(url="/portal", status_code=status.HTTP_302_FOUND)
            resp.set_cookie("proxy", value=user_data.access_token)
            return resp
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail="Error fetching configs")

    raise HTTPException(status_code=400, detail="User does not exist")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home (login) page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/creds/")
async def login(user: OAuth2PasswordRequestForm = Depends()):
    """Endpoint for user login, returning an access token."""
    token_response = api_client.login(user.username, user.password)
    if token_response.get("access_token"):
        api_client.token = token_response["access_token"]
        user_data = get_user_data(user.username)
        user_data.access_token = api_client.token
        return {"access_token": api_client.token}

    raise HTTPException(status_code=400, detail="User does not exist")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Retrieve and validate the current user based on the token."""
    if not token or len(token) <= 20:
        raise HTTPException(status_code=400, detail="Incorrect User Credentials")
    return token


async def get_current_active_user(current_user: str = Depends(get_current_user)):
    """Return the current active user."""
    return current_user
