#Copyright © 2024 Tumeryk, Inc.

from fastapi import APIRouter, Request, HTTPException
import tumeryk_guardrails
import jwt
import os
from .bot_client import bot_client
from .user_data import get_user_data

router = APIRouter()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "abc1234")

@router.get("/config_id")
async def set_config(config_id: str, request: Request):
    """Set the configuration ID to be used by the user."""
    cookie = request.cookies.get("proxy")
    if not cookie:
        return {"error": "Missing credential info"}
        
    try:
        # Validate JWT token
        decode = jwt.decode(cookie, algorithms="HS256", key=JWT_SECRET_KEY)
        username = decode.get("sub")
        
        # Set policy in tumeryk_guardrails
        result = tumeryk_guardrails.set_policy(config_id)
        
        # Update bot client token and user data
        bot_client.set_token(cookie, username)
        
        return result
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e:
        return {"error": str(e)}
