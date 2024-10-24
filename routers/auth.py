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
import tumeryk_guardrails
from .user_data import get_user_data
from .bot_client import bot_client
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/creds/")
templates = Jinja2Templates(directory="templates")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "abc1234")

@router.post("/login")
def login_test(username: str = Form(), password: str = Form()):
    """Authenticate user and redirect to portal if successful."""
    try:
        tumeryk_guardrails.set_base_url(os.getenv("TUMERYK_BASE_URL", "https://chat.tmryk.com"))
        tumeryk_guardrails.login(username, password)
            # Get user data for session management
        user_data = get_user_data(username)
        user_data.username = username
        
        # Create JWT token for session
        token = jwt.encode(
            {"sub": username},
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Initialize bot client with token
        bot_client.set_token(token, username)
        policies = tumeryk_guardrails.get_policies()
        user_data.configs = policies
        
        # Redirect to portal with token
        resp = RedirectResponse(url="/portal", status_code=status.HTTP_302_FOUND)
        resp.set_cookie("proxy", value=token)
        return resp
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home (login) page."""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/creds/")
async def login(user: OAuth2PasswordRequestForm = Depends()):
    """Endpoint for user login, returning an access token."""
    try:
        # Login with tumeryk_guardrails
        tumeryk_guardrails.login(user.username, user.password)
        
        # Create JWT token
        token = jwt.encode(
            {"sub": user.username},
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Initialize bot client with token
        bot_client.set_token(token, user.username)
        
        return {"access_token": token}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Retrieve and validate the current user based on the token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_active_user(current_user: str = Depends(get_current_user)):
    """Return the current active user."""
    return current_user
