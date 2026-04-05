# host/api/config.py
from fastapi import APIRouter
from pydantic import BaseModel
from services.config_store import ConfigStore

router = APIRouter(prefix="/api", tags=["config"])

class ConfigRequest(BaseModel):
    api_key: str

class ConfigResponse(BaseModel):
    api_key: str

class ConfigSaveResponse(BaseModel):
    success: bool

@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration (API key masked)"""
    store = ConfigStore()
    return ConfigResponse(api_key=store.get_masked_api_key())

@router.put("/config", response_model=ConfigSaveResponse)
async def save_config(config: ConfigRequest):
    """Save configuration"""
    store = ConfigStore()
    store.save_config({"api_key": config.api_key})
    return ConfigSaveResponse(success=True)
