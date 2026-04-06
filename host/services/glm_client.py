# host/services/glm_client.py
import httpx
import base64
from typing import Optional

class GLMClient:
    """Client for GLM API (智谱 AI) for speech recognition and translation"""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        # Disable proxy to avoid connection issues with local API calls
        self.client = httpx.AsyncClient(timeout=60.0, proxy=None)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def _get_headers(self) -> dict:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio using GLM Whisper API

        Args:
            audio_data: Raw audio bytes (WAV format, 16kHz, mono)

        Returns:
            Transcribed text
        """
        return await self._call_whisper_api(audio_data)

    async def _call_whisper_api(self, audio_data: bytes) -> str:
        """Call GLM Whisper API for speech recognition"""
        url = f"{self.BASE_URL}/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Use multipart form data
        files = {
            "file": ("audio.wav", audio_data, "audio/wav")
        }
        data = {
            "model": "glm-asr"  # 智谱 ASR 模型
        }

        print(f"[DEBUG] GLM API call: {url}, audio size: {len(audio_data)} bytes")

        try:
            response = await self.client.post(url, headers=headers, files=files, data=data)
            print(f"[DEBUG] GLM API response: {response.status_code}")
        except httpx.RemoteProtocolError as e:
            print(f"[DEBUG] RemoteProtocolError: {e}")
            raise RuntimeError(f"GLM API connection error: {e}")
        except httpx.ConnectError as e:
            print(f"[DEBUG] ConnectError: {e}")
            raise RuntimeError(f"Cannot connect to GLM API: {e}")
        except Exception as e:
            print(f"[DEBUG] Unexpected error: {type(e).__name__}: {e}")
            raise

        if response.status_code == 401:
            raise ValueError("API key is invalid or expired")
        elif response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_msg = response.text or "Unknown error"
            raise RuntimeError(f"GLM API error: {error_msg}")

        result = response.json()
        return result.get("text", "")

    async def translate(self, text: str, target_lang: str = "en") -> str:
        """
        Translate text using GLM API

        Args:
            text: Text to translate
            target_lang: Target language ('en' or 'zh')

        Returns:
            Translated text
        """
        return await self._call_translate_api(text, target_lang)

    async def _call_translate_api(self, text: str, target_lang: str) -> str:
        """Call GLM Chat API for translation"""
        if target_lang == "en":
            system_prompt = "You are a translator. Translate the following Chinese text to English. Only output the translation, no explanations."
        else:
            system_prompt = "You are a translator. Translate the following English text to Chinese. Only output the translation, no explanations."

        url = f"{self.BASE_URL}/chat/completions"
        headers = self._get_headers()
        payload = {
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.1
        }

        response = await self.client.post(url, headers=headers, json=payload)

        if response.status_code == 401:
            raise ValueError("API key is invalid or expired")
        elif response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            raise RuntimeError(f"GLM API error: {error_msg}")

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
