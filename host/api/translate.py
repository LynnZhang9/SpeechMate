# host/api/translate.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.config_store import ConfigStore
from services.glm_client import GLMClient

router = APIRouter(prefix="/api", tags=["translate"])


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"  # "en" or "zh"


class TranslateResponse(BaseModel):
    translated_text: str


class ErrorResponse(BaseModel):
    error: str
    code: str


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text using GLM API"""
    store = ConfigStore()

    # Check API key
    if not store.has_api_key():
        raise HTTPException(
            status_code=400,
            detail={"error": "API Key 未设置，请在 Web Admin 中配置", "code": "API_KEY_NOT_SET"}
        )

    # Handle empty text
    if not request.text:
        return TranslateResponse(translated_text="")

    # Call GLM API
    try:
        glm_client = GLMClient(api_key=store.get_api_key())
        translated_text = await glm_client.translate(request.text, request.target_lang)
        await glm_client.close()
        return TranslateResponse(translated_text=translated_text)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={"error": "API Key 无效或已过期", "code": "API_KEY_INVALID"}
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"GLM API 调用失败: {str(e)}", "code": "TRANSLATION_FAILED"}
        )
