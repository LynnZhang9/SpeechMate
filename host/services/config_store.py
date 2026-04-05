import json
import os
from pathlib import Path
from typing import Optional

class ConfigStore:
    """Manages application configuration stored in ~/.speechmate/config.json"""

    def __init__(self):
        self.config_dir = Path.home() / ".speechmate"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_config(self) -> dict:
        """Get full configuration"""
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_config(self, config: dict) -> None:
        """Save configuration to file"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_api_key(self) -> Optional[str]:
        """Get the API key"""
        return self.get_config().get("api_key")

    def get_masked_api_key(self) -> str:
        """Get masked API key for display (e.g., sk-abc...xyz)"""
        api_key = self.get_api_key()
        if not api_key:
            return ""
        if len(api_key) <= 6:
            return "***"
        return f"{api_key[:6]}...{api_key[-6:]}"

    def has_api_key(self) -> bool:
        """Check if API key is configured"""
        api_key = self.get_api_key()
        return api_key is not None and len(api_key) > 0
