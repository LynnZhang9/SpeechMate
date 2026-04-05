import pytest
import os
import json
from pathlib import Path
from services.config_store import ConfigStore

class TestConfigStore:
    def test_get_config_when_not_exists(self, tmp_path, monkeypatch):
        """Should return empty dict when config file doesn't exist"""
        monkeypatch.setenv("HOME", str(tmp_path))
        store = ConfigStore()
        config = store.get_config()
        assert config == {}

    def test_save_and_get_config(self, tmp_path, monkeypatch):
        """Should save and retrieve config"""
        monkeypatch.setenv("HOME", str(tmp_path))
        store = ConfigStore()
        store.save_config({"api_key": "sk-test123"})
        config = store.get_config()
        assert config == {"api_key": "sk-test123"}

    def test_get_masked_api_key(self, tmp_path, monkeypatch):
        """Should return masked API key"""
        monkeypatch.setenv("HOME", str(tmp_path))
        store = ConfigStore()
        store.save_config({"api_key": "sk-abcdefghijklmnop123456"})
        masked = store.get_masked_api_key()
        assert masked == "sk-abc...123456"

    def test_get_masked_api_key_short(self, tmp_path, monkeypatch):
        """Should handle short API key"""
        monkeypatch.setenv("HOME", str(tmp_path))
        store = ConfigStore()
        store.save_config({"api_key": "short"})
        masked = store.get_masked_api_key()
        assert masked == "***"

    def test_has_api_key(self, tmp_path, monkeypatch):
        """Should check if API key is set"""
        monkeypatch.setenv("HOME", str(tmp_path))
        store = ConfigStore()
        assert store.has_api_key() == False
        store.save_config({"api_key": "sk-test"})
        assert store.has_api_key() == True
