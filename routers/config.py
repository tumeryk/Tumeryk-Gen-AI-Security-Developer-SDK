from fastapi import APIRouter, Request
from proxy_core.api_client import client

router = APIRouter()


@router.get("/config_id")
async def set_config(config_id: str, request: Request):
    """Set the configuration ID to be used by the user."""
    cookie = request.cookies.get("proxy")
    if cookie:
        result = client.set_config(config_id=config_id)
        return result
    return {"error": "Missing credential info or could not find config"}
