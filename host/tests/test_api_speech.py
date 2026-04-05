# host/tests/test_api_speech.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import sys
sys.path.insert(0, ".")
from main import app

client = TestClient(app)


class TestSpeechAPI:
    def test_speech_no_api_key(self, tmp_path, monkeypatch):
        """Should return error when API key not configured"""
        monkeypatch.setenv("HOME", str(tmp_path))

        audio_data = b"fake wav data"
        response = client.post(
            "/api/speech",
            files={"audio": ("test.wav", audio_data, "audio/wav")}
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "API_KEY_NOT_SET"

    def test_speech_empty_audio(self, tmp_path, monkeypatch):
        """Should return error when audio is empty"""
        monkeypatch.setenv("HOME", str(tmp_path))
        # Set up API key
        client.put("/api/config", json={"api_key": "sk-test123"})

        response = client.post(
            "/api/speech",
            files={"audio": ("test.wav", b"", "audio/wav")}
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "AUDIO_EMPTY"

    @patch("api.speech.GLMClient")
    def test_speech_success(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should transcribe audio successfully"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        # Mock GLMClient
        mock_client = MagicMock()
        mock_client.transcribe_audio = AsyncMock(return_value="你好世界")
        mock_client.close = AsyncMock()
        mock_glm_client_class.return_value = mock_client

        audio_data = b"fake wav header" + b"\x00" * 100
        response = client.post(
            "/api/speech",
            files={"audio": ("test.wav", audio_data, "audio/wav")}
        )
        assert response.status_code == 200
        assert response.json() == {"text": "你好世界"}
