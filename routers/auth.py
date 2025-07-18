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

# Get templates directory - try multiple locations to ensure it works everywhere
import pathlib

def get_templates_directory():
    """Find the templates directory from multiple possible locations."""
    possible_paths = [
        # Relative to current file (normal case)
        pathlib.Path(__file__).parent.parent / "templates",
        # Relative to current working directory
        pathlib.Path.cwd() / "templates",
        # Direct path if we're already in project root
        pathlib.Path("templates"),
        # If running from a subdirectory
        pathlib.Path("../templates"),
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            # Verify it contains expected template files
            if (path / "login.html").exists():
                return str(path.resolve())
    
    # Fallback: create error message
    raise FileNotFoundError(
        f"Could not find templates directory. Searched in: {[str(p) for p in possible_paths]}"
    )

templates_dir = get_templates_directory()
print(f"INFO: Using templates directory: {templates_dir}")
templates = Jinja2Templates(directory=templates_dir)

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

# Redirect URIs
REDIRECT_URI_BASE = os.getenv("REDIRECT_URI_BASE", "http://localhost:8500")
GOOGLE_REDIRECT_URI = f"{REDIRECT_URI_BASE}/auth/google/callback"
GITHUB_REDIRECT_URI = f"{REDIRECT_URI_BASE}/auth/github/callback"
APPLE_REDIRECT_URI = f"{REDIRECT_URI_BASE}/auth/apple/callback"

# OAuth Scopes
GOOGLE_SCOPES = ["openid", "email", "profile"]
GITHUB_SCOPES = ["user:email"]
APPLE_SCOPES = ["name", "email"]

def create_apple_client_secret():
    """Create Apple client secret JWT."""
    if not all([APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise ValueError("Apple OAuth configuration incomplete")
    
    # Load private key
    try:
        # Handle both raw key and base64 encoded key
        private_key_data = APPLE_PRIVATE_KEY
        if not private_key_data.startswith("-----BEGIN"):
            private_key_data = base64.b64decode(private_key_data).decode('utf-8')
        
        private_key = load_pem_private_key(private_key_data.encode(), password=None)
    except Exception:
        raise ValueError("Invalid Apple private key format")
    
    # Create JWT payload
    now = int(time.time())
    payload = {
        "iss": APPLE_TEAM_ID,
        "iat": now,
        "exp": now + 3600,  # 1 hour
        "aud": "https://appleid.apple.com",
        "sub": APPLE_CLIENT_ID,
    }
    
    # Create JWT header
    headers = {
        "kid": APPLE_KEY_ID,
        "alg": "ES256"
    }
    
    # Generate JWT
    client_secret = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return client_secret

@router.get("/auth/google")
async def google_login():
    """Initiate Google OAuth login."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    oauth = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=GOOGLE_REDIRECT_URI,
        scope=GOOGLE_SCOPES
    )
    
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/v2/auth',
        access_type="offline",
        prompt="select_account"
    )
    
    response = RedirectResponse(authorization_url)
    response.set_cookie("oauth_state", state, httponly=True, secure=True, samesite="lax")
    return response

@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None):
    """Handle Google OAuth callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    # Verify state parameter
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        oauth = OAuth2Session(
            GOOGLE_CLIENT_ID,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        # Exchange code for token
        token = oauth.fetch_token(
            'https://oauth2.googleapis.com/token',
            code=code,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Get user info
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token["access_token"]}'}
            )
            user_info = response.json()
        
        # Create JWT token for the user
        jwt_token = jwt.encode(
            {
                "sub": user_info["email"],
                "name": user_info["name"],
                "provider": "google",
                "provider_id": user_info["id"]
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Redirect to success page or dashboard
        response = RedirectResponse("/portal")
        response.set_cookie("access_token", jwt_token, httponly=True, secure=True, samesite="lax")
        response.delete_cookie("oauth_state")
        return response
        
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/github")
async def github_login():
    """Initiate GitHub OAuth login."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")
    
    oauth = OAuth2Session(
        GITHUB_CLIENT_ID,
        redirect_uri=GITHUB_REDIRECT_URI,
        scope=GITHUB_SCOPES
    )
    
    authorization_url, state = oauth.authorization_url(
        'https://github.com/login/oauth/authorize'
    )
    
    response = RedirectResponse(authorization_url)
    response.set_cookie("oauth_state", state, httponly=True, secure=True, samesite="lax")
    return response

@router.get("/auth/github/callback")
async def github_callback(request: Request, code: str = None, state: str = None):
    """Handle GitHub OAuth callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    # Verify state parameter
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        oauth = OAuth2Session(
            GITHUB_CLIENT_ID,
            redirect_uri=GITHUB_REDIRECT_URI
        )
        
        # Exchange code for token
        token = oauth.fetch_token(
            'https://github.com/login/oauth/access_token',
            code=code,
            client_secret=GITHUB_CLIENT_SECRET
        )
        
        # Get user info
        async with httpx.AsyncClient() as client:
            # Get basic user info
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {token["access_token"]}'}
            )
            user_info = user_response.json()
            
            # Get user email (might be private)
            email_response = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {token["access_token"]}'}
            )
            emails = email_response.json()
            
            # Find primary email
            primary_email = None
            for email in emails:
                if email.get('primary', False):
                    primary_email = email['email']
                    break
            
            if not primary_email and emails:
                primary_email = emails[0]['email']
        
        # Create JWT token for the user
        jwt_token = jwt.encode(
            {
                "sub": primary_email or user_info["login"],
                "name": user_info.get("name", user_info["login"]),
                "provider": "github",
                "provider_id": user_info["id"]
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Redirect to success page or dashboard
        response = RedirectResponse("/portal")
        response.set_cookie("access_token", jwt_token, httponly=True, secure=True, samesite="lax")
        response.delete_cookie("oauth_state")
        return response
        
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/apple")
async def apple_login():
    """Initiate Apple OAuth login."""
    if not all([APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise HTTPException(status_code=400, detail="Apple OAuth not configured")
    
    # Apple Sign In uses form POST, so we create a simple form
    import urllib.parse
    
    params = {
        'client_id': APPLE_CLIENT_ID,
        'redirect_uri': APPLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(APPLE_SCOPES),
        'response_mode': 'form_post',
        'state': base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    }
    
    authorization_url = 'https://appleid.apple.com/auth/authorize?' + urllib.parse.urlencode(params)
    
    response = RedirectResponse(authorization_url)
    response.set_cookie("oauth_state", params['state'], httponly=True, secure=True, samesite="lax")
    return response

@router.post("/auth/apple/callback")
async def apple_callback(request: Request):
    """Handle Apple OAuth callback (POST)."""
    form_data = await request.form()
    code = form_data.get('code')
    state = form_data.get('state')
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    # Verify state parameter
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        # Generate client secret
        client_secret = create_apple_client_secret()
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://appleid.apple.com/auth/token',
                data={
                    'client_id': APPLE_CLIENT_ID,
                    'client_secret': client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': APPLE_REDIRECT_URI
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
            token_data = token_response.json()
            id_token = token_data.get('id_token')
            
            if not id_token:
                raise HTTPException(status_code=400, detail="No ID token received")
            
            # Decode the ID token (Apple's JWT)
            # Note: In production, you should verify the signature
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Create JWT token for the user
            jwt_token = jwt.encode(
                {
                    "sub": payload.get("email", payload.get("sub")),
                    "name": f"{payload.get('name', {}).get('firstName', '')} {payload.get('name', {}).get('lastName', '')}".strip() or "Apple User",
                    "provider": "apple",
                    "provider_id": payload.get("sub")
                },
                JWT_SECRET_KEY,
                algorithm="HS256"
            )
            
            # Redirect to success page or dashboard
            response = RedirectResponse("/portal")
            response.set_cookie("access_token", jwt_token, httponly=True, secure=True, samesite="lax")
            response.delete_cookie("oauth_state")
            return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/status")
async def auth_status():
    """Get OAuth provider configuration status."""
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
        
        return {"access_token": token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    """Example protected route."""
    return {"message": f"Hello {current_user}, you are authenticated!"}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})
