#Copyright © 2024 Tumeryk, Inc.

from fastapi import (
    APIRouter,
    Form,
    Depends,
    Request,
    status,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
import tumeryk_guardrails
from .user_data import get_user_data
from .bot_client import bot_client
import jwt
import os
from dotenv import load_dotenv
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client import OAuthError
import httpx
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import time

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/creds/")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "abc1234")

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")

REDIRECT_URI_BASE = os.getenv("REDIRECT_URI_BASE", "http://localhost:8500")

# OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"

APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"

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

# Google OAuth Routes
@router.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth login."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    redirect_uri = f"{REDIRECT_URI_BASE}/auth/google/callback"
    
    client = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope="openid email profile"
    )
    
    authorization_url, state = client.create_authorization_url(GOOGLE_AUTH_URL)
    
    # Store state in session for security
    response = RedirectResponse(authorization_url)
    response.set_cookie("oauth_state", state, httponly=True, secure=True)
    return response

@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    # Verify state parameter
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        redirect_uri = f"{REDIRECT_URI_BASE}/auth/google/callback"
        
        client = OAuth2Session(
            GOOGLE_CLIENT_ID,
            redirect_uri=redirect_uri
        )
        
        # Exchange code for token
        token = client.fetch_token(
            GOOGLE_TOKEN_URL,
            code=code,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Get user info
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )
            user_info = response.json()
        
        # Create user session
        username = user_info.get("email")
        if not username:
            raise HTTPException(status_code=400, detail="Unable to get user email from Google")
        
        # Create JWT token
        jwt_token = jwt.encode(
            {
                "sub": username,
                "provider": "google",
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "exp": int(time.time()) + 86400  # 24 hours
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Initialize user data and bot client
        user_data = get_user_data(username)
        user_data.username = username
        bot_client.set_token(jwt_token, username)
        
        # Redirect with token
        response = RedirectResponse(url="/portal", status_code=status.HTTP_302_FOUND)
        response.set_cookie("proxy", value=jwt_token, httponly=True, secure=True)
        response.delete_cookie("oauth_state")
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

# GitHub OAuth Routes
@router.get("/auth/github")
async def github_login(request: Request):
    """Initiate GitHub OAuth login."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    redirect_uri = f"{REDIRECT_URI_BASE}/auth/github/callback"
    
    client = OAuth2Session(
        GITHUB_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope="user:email"
    )
    
    authorization_url, state = client.create_authorization_url(GITHUB_AUTH_URL)
    
    response = RedirectResponse(authorization_url)
    response.set_cookie("oauth_state", state, httponly=True, secure=True)
    return response

@router.get("/auth/github/callback")
async def github_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle GitHub OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        redirect_uri = f"{REDIRECT_URI_BASE}/auth/github/callback"
        
        client = OAuth2Session(
            GITHUB_CLIENT_ID,
            redirect_uri=redirect_uri
        )
        
        # Exchange code for token
        token = client.fetch_token(
            GITHUB_TOKEN_URL,
            code=code,
            client_secret=GITHUB_CLIENT_SECRET
        )
        
        # Get user info
        async with httpx.AsyncClient() as http_client:
            headers = {
                "Authorization": f"Bearer {token['access_token']}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get user profile
            user_response = await http_client.get(GITHUB_USERINFO_URL, headers=headers)
            user_info = user_response.json()
            
            # Get user emails (primary email might be private)
            email_response = await http_client.get(
                "https://api.github.com/user/emails",
                headers=headers
            )
            emails = email_response.json()
            primary_email = next((email['email'] for email in emails if email['primary']), None)
        
        username = primary_email or user_info.get("email") or user_info.get("login")
        if not username:
            raise HTTPException(status_code=400, detail="Unable to get user identifier from GitHub")
        
        # Create JWT token
        jwt_token = jwt.encode(
            {
                "sub": username,
                "provider": "github",
                "name": user_info.get("name") or user_info.get("login"),
                "avatar": user_info.get("avatar_url"),
                "github_id": user_info.get("id"),
                "exp": int(time.time()) + 86400
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Initialize user data and bot client
        user_data = get_user_data(username)
        user_data.username = username
        bot_client.set_token(jwt_token, username)
        
        # Redirect with token
        response = RedirectResponse(url="/portal", status_code=status.HTTP_302_FOUND)
        response.set_cookie("proxy", value=jwt_token, httponly=True, secure=True)
        response.delete_cookie("oauth_state")
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

# Apple OAuth Routes
def create_apple_client_secret():
    """Create Apple client secret JWT."""
    if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise ValueError("Apple OAuth configuration incomplete")
    
    headers = {
        "alg": "ES256",
        "kid": APPLE_KEY_ID
    }
    
    payload = {
        "iss": APPLE_TEAM_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 180,  # 6 months
        "aud": "https://appleid.apple.com",
        "sub": APPLE_CLIENT_ID
    }
    
    # Load private key
    try:
        # Handle both raw key and base64 encoded key
        private_key_data = APPLE_PRIVATE_KEY
        if not private_key_data.startswith("-----BEGIN"):
            private_key_data = base64.b64decode(private_key_data).decode('utf-8')
        
        private_key = load_pem_private_key(private_key_data.encode(), password=None)
    except Exception:
        raise ValueError("Invalid Apple private key format")
    
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

@router.get("/auth/apple")
async def apple_login(request: Request):
    """Initiate Apple OAuth login."""
    if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise HTTPException(status_code=500, detail="Apple OAuth not configured")
    
    redirect_uri = f"{REDIRECT_URI_BASE}/auth/apple/callback"
    
    # Generate state for security
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Apple Sign In parameters
    params = {
        "client_id": APPLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "scope": "name email",
        "response_mode": "form_post"
    }
    
    auth_url = APPLE_AUTH_URL + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    response = RedirectResponse(auth_url)
    response.set_cookie("oauth_state", state, httponly=True, secure=True)
    return response

@router.post("/auth/apple/callback")
async def apple_callback(
    request: Request, 
    code: str = Form(None), 
    state: str = Form(None), 
    error: str = Form(None),
    user: str = Form(None)
):
    """Handle Apple OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        redirect_uri = f"{REDIRECT_URI_BASE}/auth/apple/callback"
        client_secret = create_apple_client_secret()
        
        # Exchange code for token
        token_data = {
            "client_id": APPLE_CLIENT_ID,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as http_client:
            token_response = await http_client.post(
                APPLE_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_result = token_response.json()
        
        if "error" in token_result:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_result['error']}")
        
        # Decode ID token to get user info
        id_token = token_result.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="No ID token received")
        
        # Decode without verification for development (in production, verify the signature)
        user_info = jwt.decode(id_token, options={"verify_signature": False})
        
        # Get user data from the user parameter if available (first-time sign-in)
        user_data_from_form = None
        if user:
            try:
                user_data_from_form = json.loads(user)
            except json.JSONDecodeError:
                pass
        
        username = user_info.get("email")
        if not username:
            raise HTTPException(status_code=400, detail="Unable to get user email from Apple")
        
        # Create JWT token
        jwt_token = jwt.encode(
            {
                "sub": username,
                "provider": "apple",
                "name": user_data_from_form.get("name", {}).get("firstName", "") + " " + 
                       user_data_from_form.get("name", {}).get("lastName", "") if user_data_from_form else "",
                "apple_id": user_info.get("sub"),
                "exp": int(time.time()) + 86400
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Initialize user data and bot client
        user_data = get_user_data(username)
        user_data.username = username
        bot_client.set_token(jwt_token, username)
        
        # Redirect with token
        response = RedirectResponse(url="/portal", status_code=status.HTTP_302_FOUND)
        response.set_cookie("proxy", value=jwt_token, httponly=True, secure=True)
        response.delete_cookie("oauth_state")
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

# OAuth Status Routes
@router.get("/auth/status")
async def auth_status():
    """Get OAuth provider availability status."""
    return {
        "google": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "github": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET),
        "apple": bool(all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]))
    }

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
