import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/config/runtime-config.json")
def runtime_config():
    api_base = os.getenv("PUBLIC_API_URL")
    if not api_base:
        return {"error": "PUBLIC_API_URL not set"}

    return {
        "API_BASE_URL": api_base
    }
