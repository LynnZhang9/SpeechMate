# SpeechMate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local voice recognition and translation assistant with FastAPI Host and PyQt5 Client.

**Architecture:** Host Server provides REST API for speech recognition and translation via GLM API. Client runs as a system tray app, captures audio on hotkey, and auto-pastes results via clipboard.

**Tech Stack:** Python 3.10+, FastAPI, PyQt5, GLM API (智谱), PyAudio, pyperclip, pynput

---

## Phase 1: Host Server Foundation

### Task 1: Host Project Setup

**Files:**
- Create: `host/requirements.txt`
- Create: `host/main.py`
- Create: `host/__init__.py`

- [ ] **Step 1: Create host directory structure**

```bash
mkdir -p host/api host/services host/static
```

- [ ] **Step 2: Create requirements.txt**

```python
# host/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
```

- [ ] **Step 3: Create host/__init__.py**

```python
# host/__init__.py
"""SpeechMate Host Server"""
__version__ = "0.1.0"
```

- [ ] **Step 4: Create basic FastAPI application**

```python
# host/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure config directory exists
    config_dir = os.path.expanduser("~/.speechmate")
    os.makedirs(config_dir, exist_ok=True)
    yield
    # Shutdown: cleanup if needed

app = FastAPI(
    title="SpeechMate Host",
    description="Voice recognition and translation assistant server",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files for Web Admin
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"name": "SpeechMate Host", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Test the basic server**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && pip install -r requirements.txt && uvicorn main:app --host 127.0.0.1 --port 8000 &
sleep 2 && curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add host/
git commit -m "feat(host): initialize FastAPI server with basic structure"
```

---

### Task 2: Configuration Storage Service

**Files:**
- Create: `host/services/__init__.py`
- Create: `host/services/config_store.py`
- Create: `host/tests/__init__.py`
- Create: `host/tests/test_config_store.py`

- [ ] **Step 1: Create services __init__.py**

```python
# host/services/__init__.py
"""SpeechMate services"""
```

- [ ] **Step 2: Write failing test for config store**

```python
# host/tests/test_config_store.py
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
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_config_store.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'services'"

- [ ] **Step 4: Create tests __init__.py**

```python
# host/tests/__init__.py
"""SpeechMate Host tests"""
```

- [ ] **Step 5: Implement ConfigStore**

```python
# host/services/config_store.py
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
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_config_store.py -v
```

Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add host/services/ host/tests/
git commit -m "feat(host): add ConfigStore for API key management"
```

---

### Task 3: GLM API Client Service

**Files:**
- Create: `host/services/glm_client.py`
- Create: `host/tests/test_glm_client.py`

- [ ] **Step 1: Write failing test for GLM client**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_glm_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'services.glm_client'"

- [ ] **Step 3: Update requirements.txt for async tests**

```python
# Add to host/requirements.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-httpx==0.28.0
```

- [ ] **Step 4: Implement GLMClient**

```python
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
        self.client = httpx.AsyncClient(timeout=60.0)

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
        # GLM uses base64 encoded audio
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        url = f"{self.BASE_URL}/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Use multipart form data
        files = {
            "file": ("audio.wav", audio_data, "audio/wav")
        }
        data = {
            "model": "whisper-1"
        }

        response = await self.client.post(url, headers=headers, files=files, data=data)

        if response.status_code == 401:
            raise ValueError("API key is invalid or expired")
        elif response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
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
```

- [ ] **Step 5: Create pytest.ini**

```ini
# host/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_paths = .
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && pip install pytest pytest-asyncio pytest-httpx && python -m pytest tests/test_glm_client.py -v
```

Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add host/services/glm_client.py host/tests/test_glm_client.py host/pytest.ini
git commit -m "feat(host): add GLMClient for speech recognition and translation"
```

---

### Task 4: Configuration API Endpoint

**Files:**
- Create: `host/api/__init__.py`
- Create: `host/api/config.py`
- Create: `host/tests/test_api_config.py`

- [ ] **Step 1: Create api __init__.py**

```python
# host/api/__init__.py
"""SpeechMate API endpoints"""
```

- [ ] **Step 2: Write failing test for config API**

```python
# host/tests/test_api_config.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_api_config.py -v
```

Expected: FAIL with 404 (endpoint not found)

- [ ] **Step 4: Implement config API**

```python
# host/api/config.py
from fastapi import APIRouter, HTTPException
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
```

- [ ] **Step 5: Update main.py to include router**

```python
# host/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from api.config import router as config_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure config directory exists
    config_dir = os.path.expanduser("~/.speechmate")
    os.makedirs(config_dir, exist_ok=True)
    yield
    # Shutdown: cleanup if needed

app = FastAPI(
    title="SpeechMate Host",
    description="Voice recognition and translation assistant server",
    version="0.1.0",
    lifespan=lifespan
)

# Include API routers
app.include_router(config_router)

# Mount static files for Web Admin
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"name": "SpeechMate Host", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_api_config.py -v
```

Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add host/api/config.py host/main.py host/tests/test_api_config.py
git commit -m "feat(host): add /api/config endpoint for API key management"
```

---

### Task 5: Speech Recognition API Endpoint

**Files:**
- Create: `host/api/speech.py`
- Create: `host/tests/test_api_speech.py`

- [ ] **Step 1: Write failing test for speech API**

```python
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
        assert response.json()["code"] == "API_KEY_NOT_SET"

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
        assert response.json()["code"] == "AUDIO_EMPTY"

    @patch("api.speech.GLMClient")
    def test_speech_success(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should transcribe audio successfully"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        # Mock GLMClient
        mock_client = MagicMock()
        mock_client.transcribe_audio = AsyncMock(return_value="你好世界")
        mock_glm_client_class.return_value = mock_client

        audio_data = b"fake wav header" + b"\x00" * 100
        response = client.post(
            "/api/speech",
            files={"audio": ("test.wav", audio_data, "audio/wav")}
        )
        assert response.status_code == 200
        assert response.json() == {"text": "你好世界"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_api_speech.py -v
```

Expected: FAIL with 404 (endpoint not found)

- [ ] **Step 3: Implement speech API**

```python
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

@router.post("/speech", response_model=SpeechResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
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
```

- [ ] **Step 4: Update main.py to include speech router**

```python
# Add to host/main.py imports
from api.speech import router as speech_router

# Add after app.include_router(config_router)
app.include_router(speech_router)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_api_speech.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add host/api/speech.py host/main.py host/tests/test_api_speech.py
git commit -m "feat(host): add /api/speech endpoint for audio transcription"
```

---

### Task 6: Translation API Endpoint

**Files:**
- Create: `host/api/translate.py`
- Create: `host/tests/test_api_translate.py`

- [ ] **Step 1: Write failing test for translate API**

```python
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
            json={"text": "你好世界", "target_lang": "en"}
        )
        assert response.status_code == 400
        assert response.json()["code"] == "API_KEY_NOT_SET"

    def test_translate_empty_text(self, tmp_path, monkeypatch):
        """Should handle empty text"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        response = client.post(
            "/api/translate",
            json={"text": "", "target_lang": "en"}
        )
        assert response.status_code == 200
        assert response.json() == {"translated_text": ""}

    @patch("api.translate.GLMClient")
    def test_translate_to_english(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should translate Chinese to English"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        mock_client = MagicMock()
        mock_client.translate = AsyncMock(return_value="Hello World")
        mock_glm_client_class.return_value = mock_client

        response = client.post(
            "/api/translate",
            json={"text": "你好世界", "target_lang": "en"}
        )
        assert response.status_code == 200
        assert response.json() == {"translated_text": "Hello World"}

    @patch("api.translate.GLMClient")
    def test_translate_to_chinese(self, mock_glm_client_class, tmp_path, monkeypatch):
        """Should translate English to Chinese"""
        monkeypatch.setenv("HOME", str(tmp_path))
        client.put("/api/config", json={"api_key": "sk-test123"})

        mock_client = MagicMock()
        mock_client.translate = AsyncMock(return_value="你好世界")
        mock_glm_client_class.return_value = mock_client

        response = client.post(
            "/api/translate",
            json={"text": "Hello World", "target_lang": "zh"}
        )
        assert response.status_code == 200
        assert response.json() == {"translated_text": "你好世界"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_api_translate.py -v
```

Expected: FAIL with 404 (endpoint not found)

- [ ] **Step 3: Implement translate API**

```python
# host/api/translate.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from services.config_store import ConfigStore
from services.glm_client import GLMClient

router = APIRouter(prefix="/api", tags=["translate"])

class TranslateRequest(BaseModel):
    text: str
    target_lang: Literal["en", "zh"] = "en"

class TranslateResponse(BaseModel):
    translated_text: str

class ErrorResponse(BaseModel):
    error: str
    code: str

@router.post("/translate", response_model=TranslateResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
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
    if not request.text.strip():
        return TranslateResponse(translated_text="")

    # Call GLM API
    try:
        glm_client = GLMClient(api_key=store.get_api_key())
        translated = await glm_client.translate(request.text, request.target_lang)
        await glm_client.close()
        return TranslateResponse(translated_text=translated)
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
```

- [ ] **Step 4: Update main.py to include translate router**

```python
# Add to host/main.py imports
from api.translate import router as translate_router

# Add after app.include_router(speech_router)
app.include_router(translate_router)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/test_api_translate.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add host/api/translate.py host/main.py host/tests/test_api_translate.py
git commit -m "feat(host): add /api/translate endpoint for text translation"
```

---

### Task 7: Web Admin Static Files

**Files:**
- Create: `host/static/index.html`
- Create: `host/static/style.css`
- Create: `host/static/app.js`

- [ ] **Step 1: Create Web Admin HTML**

```html
<!-- host/static/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpeechMate Admin</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>SpeechMate Admin</h1>
        </header>

        <main>
            <section class="config-section">
                <h2>API 配置</h2>

                <div class="form-group">
                    <label for="apiKey">GLM API Key</label>
                    <input type="password" id="apiKey" placeholder="sk-xxxxxxxxxxxxxxxx">
                    <small>从 <a href="https://open.bigmodel.cn" target="_blank">智谱开放平台</a> 获取 API Key</small>
                </div>

                <button id="saveBtn" class="btn-primary">保存配置</button>

                <div id="message" class="message hidden"></div>
            </section>

            <!-- Reserved for future features -->
            <section class="stats-section hidden">
                <h2>使用统计</h2>
                <p>暂无数据</p>
            </section>
        </main>

        <footer>
            <p>SpeechMate v0.1.0</p>
        </footer>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create Web Admin CSS**

```css
/* host/static/style.css */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

header h1 {
    color: #2563eb;
    font-size: 28px;
}

main {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

section {
    margin-bottom: 24px;
}

section:last-child {
    margin-bottom: 0;
}

h2 {
    font-size: 18px;
    margin-bottom: 16px;
    color: #1f2937;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #4b5563;
}

.form-group input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group small {
    display: block;
    margin-top: 6px;
    color: #6b7280;
    font-size: 12px;
}

.form-group small a {
    color: #2563eb;
    text-decoration: none;
}

.form-group small a:hover {
    text-decoration: underline;
}

.btn-primary {
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

.btn-primary:hover {
    background-color: #1d4ed8;
}

.btn-primary:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
}

.message {
    margin-top: 16px;
    padding: 12px;
    border-radius: 6px;
    font-size: 14px;
}

.message.success {
    background-color: #d1fae5;
    color: #065f46;
}

.message.error {
    background-color: #fee2e2;
    color: #991b1b;
}

.message.hidden {
    display: none;
}

.hidden {
    display: none;
}

footer {
    text-align: center;
    margin-top: 24px;
    color: #9ca3af;
    font-size: 12px;
}
```

- [ ] **Step 3: Create Web Admin JavaScript**

```javascript
// host/static/app.js
const API_BASE = '';

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const data = await response.json();
        if (data.api_key) {
            document.getElementById('apiKey').placeholder = data.api_key;
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

function showMessage(text, isError = false) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message ${isError ? 'error' : 'success'}`;

    // Auto hide after 3 seconds
    setTimeout(() => {
        messageEl.className = 'message hidden';
    }, 3000);
}

async function saveConfig() {
    const apiKey = document.getElementById('apiKey').value.trim();

    if (!apiKey) {
        showMessage('请输入 API Key', true);
        return;
    }

    const saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = true;
    saveBtn.textContent = '保存中...';

    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showMessage('保存成功');
            document.getElementById('apiKey').value = '';
            await loadConfig();
        } else {
            showMessage('保存失败: ' + (data.error || '未知错误'), true);
        }
    } catch (error) {
        showMessage('保存失败: ' + error.message, true);
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '保存配置';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    document.getElementById('saveBtn').addEventListener('click', saveConfig);

    // Allow Enter key to save
    document.getElementById('apiKey').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            saveConfig();
        }
    });
});
```

- [ ] **Step 4: Update main.py to serve admin page**

```python
# Add to host/main.py

@app.get("/admin")
async def admin_page():
    """Serve Web Admin page"""
    from fastapi.responses import FileResponse
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return FileResponse(os.path.join(static_dir, "index.html"))
```

- [ ] **Step 5: Test Web Admin manually**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && uvicorn main:app --host 127.0.0.1 --port 8000 &
sleep 2 && curl http://127.0.0.1:8000/admin
```

Expected: HTML content returned

- [ ] **Step 6: Commit**

```bash
git add host/static/ host/main.py
git commit -m "feat(host): add Web Admin page for API key configuration"
```

---

## Phase 2: Client Application

### Task 8: Client Project Setup

**Files:**
- Create: `client/requirements.txt`
- Create: `client/main.py`
- Create: `client/__init__.py`

- [ ] **Step 1: Create client directory structure**

```bash
mkdir -p client/resources/icons
```

- [ ] **Step 2: Create requirements.txt**

```python
# client/requirements.txt
PyQt5==5.15.10
pynput==1.7.6
pyaudio==0.2.14
pyperclip==1.8.2
httpx==0.26.0
sounddevice==0.4.6
soundfile==0.12.1
```

- [ ] **Step 3: Create client/__init__.py**

```python
# client/__init__.py
"""SpeechMate Client"""
__version__ = "0.1.0"
```

- [ ] **Step 4: Create basic PyQt5 application**

```python
# client/main.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    # Placeholder - will be replaced with actual tray implementation
    print("SpeechMate Client starting...")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Test basic client startup**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/client && pip install PyQt5 && python main.py &
sleep 2 && pkill -f "python main.py"
```

Expected: "SpeechMate Client starting..." printed

- [ ] **Step 6: Commit**

```bash
git add client/
git commit -m "feat(client): initialize PyQt5 application structure"
```

---

### Task 9: System Tray Implementation

**Files:**
- Create: `client/tray.py`
- Create: `client/resources/icons/normal.png`
- Create: `client/resources/icons/recording.png`

- [ ] **Step 1: Create placeholder icon files (using simple colored squares)**

```bash
# Create simple colored PNG icons (1x1 pixel, will be replaced with proper icons)
# For now, we'll create them programmatically in the code
```

- [ ] **Step 2: Implement tray module**

```python
# client/tray.py
import os
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import pyqtSignal, QObject

class TrayIcon(QObject):
    """System tray icon manager"""

    # Signals
    exit_requested = pyqtSignal()
    config_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon()
        self._is_recording = False

        # Create icons programmatically
        self.normal_icon = self._create_icon(QColor(59, 130, 246))  # Blue
        self.recording_icon = self._create_icon(QColor(239, 68, 68))  # Red

        self._setup_tray()

    def _create_icon(self, color: QColor) -> QIcon:
        """Create a simple colored circle icon"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()

        return QIcon(pixmap)

    def _setup_tray(self):
        """Setup tray icon and menu"""
        self.tray_icon.setIcon(self.normal_icon)
        self.tray_icon.setToolTip("SpeechMate - 按 F8 开始录音")

        # Create context menu
        menu = QMenu()

        # Open admin action
        admin_action = QAction("打开设置", self)
        admin_action.triggered.connect(self.config_requested.emit)
        menu.addAction(admin_action)

        menu.addSeparator()

        # Exit action
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)

    def show(self):
        """Show the tray icon"""
        self.tray_icon.show()

    def hide(self):
        """Hide the tray icon"""
        self.tray_icon.hide()

    def set_recording(self, is_recording: bool):
        """Set recording state (changes icon)"""
        self._is_recording = is_recording
        if is_recording:
            self.tray_icon.setIcon(self.recording_icon)
            self.tray_icon.setToolTip("SpeechMate - 录音中...")
        else:
            self.tray_icon.setIcon(self.normal_icon)
            self.tray_icon.setToolTip("SpeechMate - 按 F8 开始录音")

    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        """Show a tray notification"""
        self.tray_icon.showMessage(title, message, icon, 3000)
```

- [ ] **Step 3: Update main.py to use tray**

```python
# client/main.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from tray import TrayIcon

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Create tray icon
    tray = TrayIcon()
    tray.show()
    tray.exit_requested.connect(app.quit)

    print("SpeechMate Client started. Press F8 to record.")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Test tray icon**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/client && python main.py &
sleep 2 && pkill -f "python main.py"
```

Expected: Tray icon appears in system tray

- [ ] **Step 5: Commit**

```bash
git add client/tray.py client/main.py
git commit -m "feat(client): add system tray icon with recording state"
```

---

### Task 10: Hotkey Listener

**Files:**
- Create: `client/hotkey.py`

- [ ] **Step 1: Implement hotkey module**

```python
# client/hotkey.py
from pynput import keyboard
from PyQt5.QtCore import QObject, pyqtSignal

class HotkeyListener(QObject):
    """Global hotkey listener for F8 key"""

    # Signals
    hotkey_pressed = pyqtSignal()
    hotkey_released = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None
        self._is_listening = False

    def start(self):
        """Start listening for hotkey"""
        if self._is_listening:
            return

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.start()
        self._is_listening = True

    def stop(self):
        """Stop listening for hotkey"""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._is_listening = False

    def _on_press(self, key):
        """Handle key press"""
        try:
            # F8 key code
            if key == keyboard.Key.f8:
                self.hotkey_pressed.emit()
        except AttributeError:
            pass

    def _on_release(self, key):
        """Handle key release"""
        try:
            # F8 key code
            if key == keyboard.Key.f8:
                self.hotkey_released.emit()
        except AttributeError:
            pass
```

- [ ] **Step 2: Update main.py to use hotkey**

```python
# client/main.py
import sys
import webbrowser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from tray import TrayIcon
from hotkey import HotkeyListener

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Create tray icon
    tray = TrayIcon()
    tray.show()
    tray.exit_requested.connect(app.quit)
    tray.config_requested.connect(lambda: webbrowser.open("http://127.0.0.1:8000/admin"))

    # Create hotkey listener
    hotkey = HotkeyListener()
    hotkey.hotkey_pressed.connect(lambda: tray.set_recording(True))
    hotkey.hotkey_released.connect(lambda: tray.set_recording(False))
    hotkey.start()

    print("SpeechMate Client started. Press F8 to record.")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test hotkey listener**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/client && pip install pynput && python main.py &
sleep 2
# Press F8 to test (icon should turn red), release (icon should turn blue)
pkill -f "python main.py"
```

Expected: Icon changes color when F8 pressed/released

- [ ] **Step 4: Commit**

```bash
git add client/hotkey.py client/main.py
git commit -m "feat(client): add F8 hotkey listener for recording trigger"
```

---

### Task 11: Audio Recorder

**Files:**
- Create: `client/recorder.py`

- [ ] **Step 1: Implement recorder module**

```python
# client/recorder.py
import io
import wave
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

class AudioRecorder(QObject):
    """Audio recorder using sounddevice"""

    # Audio settings
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = np.int16

    # Signals
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(bytes)  # Emits WAV audio data

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_recording = False
        self._frames = []

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start_recording(self):
        """Start recording audio"""
        if self._is_recording:
            return

        self._frames = []
        self._is_recording = True
        self.recording_started.emit()

        # Start recording stream
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            callback=self._audio_callback
        )
        self._stream.start()

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if self._is_recording:
            self._frames.append(indata.copy())

    def stop_recording(self) -> bytes:
        """Stop recording and return WAV audio data"""
        if not self._is_recording:
            return b""

        self._is_recording = False

        # Stop stream
        if hasattr(self, '_stream'):
            self._stream.stop()
            self._stream.close()

        # Convert to WAV format
        wav_data = self._create_wav()

        self.recording_stopped.emit(wav_data)
        return wav_data

    def _create_wav(self) -> bytes:
        """Create WAV file in memory from recorded frames"""
        if not self._frames:
            return b""

        # Concatenate all frames
        audio_data = np.concatenate(self._frames, axis=0)

        # Create WAV in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(audio_data.tobytes())

        return buffer.getvalue()
```

- [ ] **Step 2: Update main.py to use recorder**

```python
# client/main.py
import sys
import webbrowser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from tray import TrayIcon
from hotkey import HotkeyListener
from recorder import AudioRecorder

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Create tray icon
    tray = TrayIcon()
    tray.show()
    tray.exit_requested.connect(app.quit)
    tray.config_requested.connect(lambda: webbrowser.open("http://127.0.0.1:8000/admin"))

    # Create audio recorder
    recorder = AudioRecorder()

    # Create hotkey listener
    hotkey = HotkeyListener()

    def on_hotkey_pressed():
        tray.set_recording(True)
        recorder.start_recording()

    def on_hotkey_released():
        tray.set_recording(False)
        audio_data = recorder.stop_recording()
        print(f"Recorded {len(audio_data)} bytes of audio")
        # TODO: Send to API

    hotkey.hotkey_pressed.connect(on_hotkey_pressed)
    hotkey.hotkey_released.connect(on_hotkey_released)
    hotkey.start()

    print("SpeechMate Client started. Press F8 to record.")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test audio recorder**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/client && pip install sounddevice soundfile numpy && python main.py &
sleep 2
# Press F8, speak, release F8
# Should see "Recorded X bytes of audio"
pkill -f "python main.py"
```

Expected: Audio bytes logged after recording

- [ ] **Step 4: Commit**

```bash
git add client/recorder.py client/main.py
git commit -m "feat(client): add audio recorder with WAV output"
```

---

### Task 12: API Client

**Files:**
- Create: `client/api_client.py`

- [ ] **Step 1: Implement API client module**

```python
# client/api_client.py
import httpx
from typing import Optional, Tuple

class SpeechMateClient:
    """Client for SpeechMate Host API"""

    def __init__(self, host: str = "http://127.0.0.1:8000"):
        self.host = host
        self.client = httpx.Client(timeout=60.0)

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            response = self.client.get(f"{self.host}/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def transcribe(self, audio_data: bytes) -> Tuple[bool, str]:
        """
        Transcribe audio to text

        Returns:
            Tuple of (success, text_or_error)
        """
        try:
            response = self.client.post(
                f"{self.host}/api/speech",
                files={"audio": ("audio.wav", audio_data, "audio/wav")}
            )

            if response.status_code == 200:
                return True, response.json()["text"]
            else:
                error = response.json().get("error", "Unknown error")
                return False, error

        except httpx.RequestError as e:
            return False, f"连接服务器失败: {str(e)}"

    def translate(self, text: str, target_lang: str = "en") -> Tuple[bool, str]:
        """
        Translate text

        Returns:
            Tuple of (success, translated_text_or_error)
        """
        try:
            response = self.client.post(
                f"{self.host}/api/translate",
                json={"text": text, "target_lang": target_lang}
            )

            if response.status_code == 200:
                return True, response.json()["translated_text"]
            else:
                error = response.json().get("error", "Unknown error")
                return False, error

        except httpx.RequestError as e:
            return False, f"连接服务器失败: {str(e)}"

    def get_config(self) -> Tuple[bool, dict]:
        """Get current configuration"""
        try:
            response = self.client.get(f"{self.host}/api/config")
            if response.status_code == 200:
                return True, response.json()
            return False, {}
        except httpx.RequestError:
            return False, {}
```

- [ ] **Step 2: Commit**

```bash
git add client/api_client.py
git commit -m "feat(client): add API client for Host server communication"
```

---

### Task 13: Clipboard Operations

**Files:**
- Create: `client/clipboard.py`

- [ ] **Step 1: Implement clipboard module**

```python
# client/clipboard.py
import pyperclip
import time
import platform
from pynput import keyboard

class ClipboardManager:
    """Manages clipboard operations and auto-paste"""

    def __init__(self):
        self.system = platform.system()

    def paste_text(self, text: str):
        """
        Paste text to cursor position via clipboard

        1. Save current clipboard
        2. Set text to clipboard
        3. Simulate Ctrl+V / Cmd+V
        4. Restore original clipboard after delay
        """
        # Save current clipboard
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = ""

        # Set new text
        pyperclip.copy(text)

        # Simulate paste
        self._simulate_paste()

        # Restore clipboard after delay
        def restore_clipboard():
            time.sleep(0.5)  # Wait for paste to complete
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass

        # Run restore in background
        import threading
        thread = threading.Thread(target=restore_clipboard, daemon=True)
        thread.start()

    def _simulate_paste(self):
        """Simulate paste keyboard shortcut"""
        controller = keyboard.Controller()

        if self.system == "Darwin":  # macOS
            controller.press(keyboard.Key.cmd)
            controller.press('v')
            controller.release('v')
            controller.release(keyboard.Key.cmd)
        else:  # Windows and Linux
            controller.press(keyboard.Key.ctrl)
            controller.press('v')
            controller.release('v')
            controller.release(keyboard.Key.ctrl)
```

- [ ] **Step 2: Commit**

```bash
git add client/clipboard.py
git commit -m "feat(client): add clipboard manager with auto-paste functionality"
```

---

### Task 14: Main Application Integration

**Files:**
- Modify: `client/main.py`

- [ ] **Step 1: Integrate all components**

```python
# client/main.py
import sys
import webbrowser
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from tray import TrayIcon
from hotkey import HotkeyListener
from recorder import AudioRecorder
from api_client import SpeechMateClient
from clipboard import ClipboardManager

class ProcessingWorker(QThread):
    """Background worker for processing audio"""
    finished = pyqtSignal(bool, str)  # success, text

    def __init__(self, api_client: SpeechMateClient, audio_data: bytes, translate: bool = False):
        super().__init__()
        self.api_client = api_client
        self.audio_data = audio_data
        self.translate = translate

    def run(self):
        # Transcribe audio
        success, result = self.api_client.transcribe(self.audio_data)

        if not success:
            self.finished.emit(False, result)
            return

        text = result

        # Optionally translate
        if self.translate:
            success, result = self.api_client.translate(text, target_lang="en")
            if success:
                text = result

        self.finished.emit(True, text)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Initialize components
    tray = TrayIcon()
    recorder = AudioRecorder()
    hotkey = HotkeyListener()
    api_client = SpeechMateClient()
    clipboard = ClipboardManager()

    # Check server connection
    if not api_client.health_check():
        tray.show_message(
            "SpeechMate",
            "无法连接到服务器，请确保 Host 已启动",
            tray.tray_icon.Warning
        )

    # Current worker (to prevent multiple)
    current_worker = [None]

    def on_hotkey_pressed():
        tray.set_recording(True)
        recorder.start_recording()

    def on_hotkey_released():
        tray.set_recording(False)
        audio_data = recorder.stop_recording()

        if len(audio_data) < 1000:  # Too short
            tray.show_message("SpeechMate", "录音时间太短")
            return

        # Process in background
        worker = ProcessingWorker(api_client, audio_data, translate=False)
        worker.finished.connect(on_processing_finished)
        worker.start()
        current_worker[0] = worker

    def on_processing_finished(success: bool, text: str):
        if success:
            clipboard.paste_text(text)
            tray.show_message("SpeechMate", f"已输入: {text[:20]}...")
        else:
            tray.show_message("SpeechMate", f"处理失败: {text}", tray.tray_icon.Warning)

    def open_config():
        webbrowser.open("http://127.0.0.1:8000/admin")

    def quit_app():
        hotkey.stop()
        api_client.close()
        app.quit()

    # Connect signals
    tray.show()
    tray.exit_requested.connect(quit_app)
    tray.config_requested.connect(open_config)
    hotkey.hotkey_pressed.connect(on_hotkey_pressed)
    hotkey.hotkey_released.connect(on_hotkey_released)
    hotkey.start()

    print("SpeechMate Client started. Press F8 to record.")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test full integration**

```bash
# Start host server first
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && uvicorn main:app --host 127.0.0.1 --port 8000 &

# Wait for server
sleep 2

# Start client
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/client && python main.py &

# Press F8 to record, speak, release
# Text should be pasted to active application
```

Expected: Full workflow working

- [ ] **Step 3: Commit**

```bash
git add client/main.py
git commit -m "feat(client): integrate all components for full speech-to-text workflow"
```

---

## Phase 3: Documentation & Finalization

### Task 15: Project Documentation

**Files:**
- Create: `README.md`
- Create: `docs/README.md`

- [ ] **Step 1: Create main README**

```markdown
# SpeechMate

语音识别与翻译助手 - 按住 F8 说话，松开后自动转文字并粘贴到光标位置。

## 功能

- 🎤 **语音识别**: 按住 F8 说话，松开后自动转文字
- 🌐 **语音翻译**: 支持中英互译（通过 GLM API）
- ⌨️ **自动输入**: 识别的文字自动粘贴到光标位置
- 🔧 **Web 管理**: 提供界面配置 API Key

## 系统要求

- Python 3.10+
- macOS / Windows / Linux

## 快速开始

### 1. 安装依赖

```bash
# Host 依赖
cd host
pip install -r requirements.txt

# Client 依赖
cd ../client
pip install -r requirements.txt
```

### 2. 配置 API Key

1. 启动 Host 服务器：
   ```bash
   cd host
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```

2. 打开浏览器访问 http://127.0.0.1:8000/admin

3. 输入你的 GLM API Key（从 [智谱开放平台](https://open.bigmodel.cn) 获取）

### 3. 启动客户端

```bash
cd client
python main.py
```

### 4. 使用

1. 将光标放在任意输入框中
2. 按住 F8 开始录音
3. 说话
4. 松开 F8，文字将自动粘贴到光标位置

## 项目结构

```
SpeechMate/
├── host/           # FastAPI 服务器
│   ├── api/        # API 端点
│   ├── services/   # 业务逻辑
│   └── static/     # Web Admin
├── client/         # PyQt5 客户端
│   ├── main.py     # 主程序
│   ├── tray.py     # 系统托盘
│   ├── hotkey.py   # 快捷键
│   ├── recorder.py # 录音
│   └── clipboard.py# 剪贴板
└── docs/           # 文档
```

## 开发

### 运行测试

```bash
cd host
python -m pytest tests/ -v
```

## License

MIT
```

- [ ] **Step 2: Create docs README**

```markdown
# SpeechMate 使用文档

## 快捷键

- `F8`: 按住录音，松开识别

## 系统托盘

- 蓝色图标: 待机状态
- 红色图标: 录音中

右键托盘图标可：
- 打开设置（Web Admin）
- 退出程序

## Web Admin

访问 http://127.0.0.1:8000/admin 配置：

- GLM API Key: 从智谱开放平台获取

## 故障排除

### 无法录音

确保麦克风权限已授予 Python。

### 无法连接服务器

确保 Host 服务器已启动：
```bash
cd host
uvicorn main:app --host 127.0.0.1 --port 8000
```

### API Key 无效

检查 API Key 是否正确，是否有余额。
```

- [ ] **Step 3: Commit**

```bash
git add README.md docs/README.md
git commit -m "docs: add project documentation"
```

---

### Task 16: Final Verification

- [ ] **Step 1: Run all host tests**

```bash
cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 2: Manual end-to-end test**

1. Start host server
2. Configure API key via Web Admin
3. Start client
4. Press F8, speak, release
5. Verify text is pasted

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```

---

## Summary

This plan creates a complete SpeechMate application with:

**Host Server (FastAPI)**
- Configuration storage service
- GLM API client for speech recognition and translation
- REST API endpoints (`/api/config`, `/api/speech`, `/api/translate`)
- Web Admin interface for API key configuration

**Client Application (PyQt5)**
- System tray icon with recording state indicator
- F8 hotkey listener
- Audio recorder (WAV output)
- API client for server communication
- Clipboard manager with auto-paste

**Total: 16 tasks with TDD approach**
