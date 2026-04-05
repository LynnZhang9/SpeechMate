# host/tests/test_api_translate.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import sys
sys.path.insert(0, ".")
from main import app

client = TestClient(app)


class TestTranslateAPI:
    def test_translate_no_api_key(self, tmp_path, monkeypatch):
        """Should return error when API key not configured"""
        monkeypatch.setenv("HOME", str(tmp_path))

        response = client.post(
            "/api/translate",
            json={"text": "你好", "target_lang": "en"}
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "API_KEY_NOT_SET"

    def test_translate_empty_text(self, tmp_path, monkeypatch):
        """Should return empty translated_text when text is empty"""
        monkeypatch.setenv("HOME", str(tmp_path))
        # Set up API key
        client.put("/api/config", json={"api_key": "sk-test123"})

        response = client.post(
            "/api/translate",
            json={"text": "", "target_lang": "en"}
        )
        assert response.status_code == 200
        assert response.json() == {"translated_text": ""}

    @patch("api.translate.GLMClient")
    def test_translate_to_english_success(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should translate Chinese to English successfully"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        # Mock GLMClient
        mock_client = MagicMock()
        mock_client.translate = AsyncMock(return_value="Hello World")
        mock_client.close = AsyncMock()
        mock_glm_client_class.return_value = mock_client

        response = client.post(
            "/api/translate",
            json={"text": "你好世界", "target_lang": "en"}
        )
        assert response.status_code == 200
        assert response.json() == {"translated_text": "Hello World"}
        mock_client.translate.assert_called_once_with("你好世界", "en")

    @patch("api.translate.GLMClient")
    def test_translate_to_chinese_success(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should translate English to Chinese successfully"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        # Mock GLMClient
        mock_client = MagicMock()
        mock_client.translate = AsyncMock(return_value="你好世界")
        mock_client.close = AsyncMock()
        mock_glm_client_class.return_value = mock_client

        response = client.post(
            "/api/translate",
            json={"text": "Hello World", "target_lang": "zh"}
        )
        assert response.status_code == 200
        assert response.json() == {"translated_text": "你好世界"}
        mock_client.translate.assert_called_once_with("Hello World", "zh")

    @patch("api.translate.GLMClient")
    def test_translate_api_key_invalid(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should return error when API key is invalid"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-invalid"})

        # Mock GLMClient to raise ValueError (invalid API key)
        mock_client = MagicMock()
        mock_client.translate = AsyncMock(side_effect=ValueError("API key is invalid or expired"))
        mock_client.close = AsyncMock()
        mock_glm_client_class.return_value = mock_client

        response = client.post(
            "/api/translate",
            json={"text": "Hello", "target_lang": "zh"}
        )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "API_KEY_INVALID"

    @patch("api.translate.GLMClient")
    def test_translate_api_failure(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should return error when API call fails"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        # Mock GLMClient to raise RuntimeError (API failure)
        mock_client = MagicMock()
        mock_client.translate = AsyncMock(side_effect=RuntimeError("GLM API error: Rate limit exceeded"))
        mock_client.close = AsyncMock()
        mock_glm_client_class.return_value = mock_client

        response = client.post(
            "/api/translate",
            json={"text": "Hello", "target_lang": "zh"}
        )
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "TRANSLATION_FAILED"
