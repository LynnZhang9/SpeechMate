# host/tests/test_api_config.py
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, ".")
from main import app

client = TestClient(app)

class TestConfigAPI:
    def test_get_config_empty(self, tmp_path, monkeypatch):
        """Should return empty API key when not configured"""
        monkeypatch.setenv("HOME", str(tmp_path))
        response = client.get("/api/config")
        assert response.status_code == 200
        assert response.json() == {"api_key": ""}

    def test_get_config_with_key(self, tmp_path, monkeypatch):
        """Should return masked API key"""
        monkeypatch.setenv("HOME", str(tmp_path))
        # First save a config
        client.put("/api/config", json={"api_key": "sk-test123456789"})
        response = client.get("/api/config")
        assert response.status_code == 200
        assert "api_key" in response.json()
        assert response.json()["api_key"] == "sk-tes...456789"

    def test_save_config(self, tmp_path, monkeypatch):
        """Should save API key"""
        monkeypatch.setenv("HOME", str(tmp_path))
        response = client.put("/api/config", json={"api_key": "sk-newkey123"})
        assert response.status_code == 200
        assert response.json() == {"success": True}

    def test_save_config_empty_key(self, tmp_path, monkeypatch):
        """Should allow saving empty key to clear"""
        monkeypatch.setenv("HOME", str(tmp_path))
        response = client.put("/api/config", json={"api_key": ""})
        assert response.status_code == 200
        assert response.json() == {"success": True}
