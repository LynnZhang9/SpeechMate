# host/api/speech.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.config_store import ConfigStore
from services.glm_client import GLMClient

router = APIRouter(prefix="/api", tags=["speech"])


class SpeechResponse(BaseModel):
    text: str


class ErrorResponse(BaseModel):
    error: str
    code: str


@router.post("/speech", response_model=SpeechResponse)
async def transcribe_speech(audio: UploadFile = File(...)):
    """Transcribe audio file to text using GLM Whisper API"""
    store = ConfigStore()

    # Check API key
    if not store.has_api_key():
        raise HTTPException(
            status_code=400,
            detail={"error": "API Key 未设置，请在 Web Admin 中配置", "code": "API_KEY_NOT_SET"}
        )

    # Read audio data
    audio_data = await audio.read()

    # Check if audio is empty
    if len(audio_data) == 0:
        raise HTTPException(
            status_code=400,
            detail={"error": "上传的音频文件为空", "code": "AUDIO_EMPTY"}
        )

    # Call GLM API
    try:
        glm_client = GLMClient(api_key=store.get_api_key())
        text = await glm_client.transcribe_audio(audio_data)
        await glm_client.close()
        return SpeechResponse(text=text)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={"error": "API Key 无效或已过期", "code": "API_KEY_INVALID"}
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"GLM API 调用失败: {str(e)}", "code": "SPEECH_RECOGNITION_FAILED"}
        )
