# host/tests/test_glm_client.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.glm_client import GLMClient

class TestGLMClient:
    def test_init_with_api_key(self):
        """Should initialize with API key"""
        client = GLMClient(api_key="sk-test123")
        assert client.api_key == "sk-test123"

    def test_init_without_api_key(self):
        """Should raise error without API key"""
        with pytest.raises(ValueError, match="API key is required"):
            GLMClient(api_key="")

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self):
        """Should transcribe audio and return text"""
        client = GLMClient(api_key="sk-test123")

        with patch.object(client, '_call_whisper_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "你好世界"
            audio_data = b"fake audio data"
            result = await client.transcribe_audio(audio_data)
            assert result == "你好世界"

    @pytest.mark.asyncio
    async def test_translate_success(self):
        """Should translate text"""
        client = GLMClient(api_key="sk-test123")

        with patch.object(client, '_call_translate_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Hello World"
            result = await client.translate("你好世界", target_lang="en")
            assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_translate_to_chinese(self):
        """Should translate to Chinese"""
        client = GLMClient(api_key="sk-test123")

        with patch.object(client, '_call_translate_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "你好世界"
            result = await client.translate("Hello World", target_lang="zh")
            assert result == "你好世界"
