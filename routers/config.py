from fastapi import APIRouter, Request, HTTPException
from utils.api_client import client
from utils.user_data import get_user_data

router = APIRouter()

@router.get("/config_id")
async def set_config(config_id: str, request: Request):
    """Set the configuration ID to be used by the user."""
    cookie = request.cookies.get("proxy")
    if cookie:
        result = client.set_config(config_id=config_id)
        return result
    return {"error": "Missing credential info or could not find config"}
