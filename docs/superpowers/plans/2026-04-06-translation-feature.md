# SpeechMate 中英翻译功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 SpeechMate 添加中英翻译功能，用户通过 `Cmd+Shift+T` 热键触发语音翻译。

**Architecture:** 采用模式架构，新增 `WorkMode` 枚举区分识别/翻译模式，通过独立热键触发不同处理流程，保留原有功能不变。

**Tech Stack:** Python 3.10+, PyQt5, GLM API

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `client/modes.py` | 创建 | WorkMode 枚举 + 语言检测函数 |
| `client/tests/test_modes.py` | 创建 | 语言检测单元测试 |
| `client/main.py` | 修改 | 支持多热键 + 模式分发 |
| `client/floating_panel.py` | 修改 | 显示当前模式状态（颜色区分） |

---

### Task 1: 创建 modes.py 和语言检测测试

**Files:**
- Create: `client/modes.py`
- Create: `client/tests/test_modes.py`

- [ ] **Step 1: 创建 modes.py**

```python
# client/modes.py
"""Work modes and language detection for SpeechMate."""

from enum import Enum


class WorkMode(Enum):
    """Work mode for audio processing."""
    TRANSCRIBE = "transcribe"   # 语音识别（默认）
    TRANSLATE = "translate"     # 语音翻译


def detect_language(text: str) -> str:
    """检测文本语言，返回 'zh' 或 'en'。

    Args:
        text: 待检测的文本。

    Returns:
        'zh' 如果中文占比超过 30%，否则 'en'。
    """
    if not text:
        return "zh"
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if chinese_chars / len(text) > 0.3:
        return "zh"
    return "en"


def get_target_lang(text: str) -> str:
    """根据源语言返回目标语言。

    Args:
        text: 待翻译的文本。

    Returns:
        'en' 如果源语言是中文，否则 'zh'。
    """
    return "en" if detect_language(text) == "zh" else "zh"
```

- [ ] **Step 2: 创建语言检测单元测试**

```python
# client/tests/test_modes.py
"""Tests for language detection."""

import pytest
from client.modes import detect_language, get_target_lang, WorkMode


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_detect_chinese_text(self):
        """纯中文文本应返回 'zh'"""
        assert detect_language("你好世界") == "zh"
        assert detect_language("这是一个测试") == "zh"

    def test_detect_english_text(self):
        """纯英文文本应返回 'en'"""
        assert detect_language("Hello World") == "en"
        assert detect_language("This is a test") == "en"

    def test_detect_mixed_text_chinese_dominant(self):
        """中文占比超过30%应返回 'zh'"""
        # 4个中文字符 / 10总字符 = 40%
        assert detect_language("你好HelloWorld") == "zh"

    def test_detect_mixed_text_english_dominant(self):
        """中文占比不超过30%应返回 'en'"""
        # 2个中文字符 / 10总字符 = 20%
        assert detect_language("Hi你好World") == "en"

    def test_detect_empty_text(self):
        """空文本应返回 'zh'（默认）"""
        assert detect_language("") == "zh"

    def test_detect_numbers_only(self):
        """纯数字应返回 'en'"""
        assert detect_language("123456") == "en"


class TestGetTargetLang:
    """Tests for get_target_lang function."""

    def test_chinese_to_english(self):
        """中文文本目标语言应为 'en'"""
        assert get_target_lang("你好世界") == "en"

    def test_english_to_chinese(self):
        """英文文本目标语言应为 'zh'"""
        assert get_target_lang("Hello World") == "zh"


class TestWorkMode:
    """Tests for WorkMode enum."""

    def test_work_mode_values(self):
        """验证枚举值"""
        assert WorkMode.TRANSCRIBE.value == "transcribe"
        assert WorkMode.TRANSLATE.value == "translate"
```

- [ ] **Step 3: 运行测试验证通过**

Run: `cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate && python -m pytest client/tests/test_modes.py -v`

Expected: 所有测试 PASS

- [ ] **Step 4: Commit**

```bash
git add client/modes.py client/tests/test_modes.py
git commit -m "$(cat <<'EOF'
feat(client): add WorkMode enum and language detection

- Add WorkMode enum for transcribe/translate modes
- Add detect_language() for Chinese/English detection
- Add get_target_lang() for translation direction
- Add unit tests for all functions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: 修改 floating_panel.py 支持模式状态显示

**Files:**
- Modify: `client/floating_panel.py`

- [ ] **Step 1: 添加导入和颜色常量**

在文件顶部导入区域添加：

```python
# 在第 15 行后添加
from client.modes import WorkMode
```

在 `COLORS` 字典中添加翻译模式颜色：

```python
# 替换 COLORS 定义（第 38-42 行）
COLORS = {
    "ready": "#3B82F6",      # Blue
    "recording": "#EF4444",  # Red
    "processing": "#F59E0B", # Orange/Amber
    "translate": "#4CAF50",  # Green
}
```

- [ ] **Step 2: 添加 _mode 属性和 set_mode 方法**

在 `__init__` 方法中初始化模式（第 60 行后）：

```python
# 在 self._drag_pos = QPoint() 后添加
self._mode = WorkMode.TRANSCRIBE
```

添加 `set_mode` 方法（在 `set_processing` 方法后，第 146 行后）：

```python
def set_mode(self, mode: WorkMode):
    """设置当前工作模式，更新面板颜色。

    Args:
        mode: 工作模式（TRANSCRIBE 或 TRANSLATE）
    """
    self._mode = mode
    # 仅在就绪状态时更新颜色
    if self._state == self.STATE_READY:
        if mode == WorkMode.TRANSLATE:
            self._status_indicator.setStyleSheet(f"color: {self.COLORS['translate']};")
        else:
            self._status_indicator.setStyleSheet(f"color: {self.COLORS['ready']};")
    print(f"[DEBUG] FloatingPanel: Mode set to {mode.value}")
```

- [ ] **Step 3: 修改 set_recording 方法恢复正确颜色**

修改 `set_recording` 方法（第 118-133 行），在恢复就绪状态时考虑当前模式：

```python
def set_recording(self, is_recording: bool):
    """Set the recording state.

    Args:
        is_recording: True if recording, False otherwise.
    """
    if is_recording:
        self._state = self.STATE_RECORDING
        self._status_indicator.setStyleSheet(f"color: {self.COLORS['recording']};")
        self._status_label.setText("REC")
        print("[DEBUG] FloatingPanel: Recording state")
    else:
        self._state = self.STATE_READY
        # 根据当前模式设置颜色
        if self._mode == WorkMode.TRANSLATE:
            self._status_indicator.setStyleSheet(f"color: {self.COLORS['translate']};")
        else:
            self._status_indicator.setStyleSheet(f"color: {self.COLORS['ready']};")
        self._status_label.setText("SM")
        print("[DEBUG] FloatingPanel: Ready state")
```

- [ ] **Step 4: 验证语法正确**

Run: `cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate && python -c "from client.floating_panel import FloatingPanel; print('OK')"`

Expected: 输出 `OK`

- [ ] **Step 5: Commit**

```bash
git add client/floating_panel.py
git commit -m "$(cat <<'EOF'
feat(client): add mode status display to floating panel

- Add set_mode() method to update panel color based on mode
- Green color for translate mode, blue for transcribe mode
- Preserve mode color when returning to ready state

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 修改 main.py 支持翻译热键和模式分发

**Files:**
- Modify: `client/main.py`

- [ ] **Step 1: 添加导入**

在文件顶部导入区域（第 23 行后）添加：

```python
from client.modes import WorkMode, get_target_lang
```

- [ ] **Step 2: 修改 __init__ 方法**

在 `__init__` 方法中（第 53 行 `self._processing = False` 后）添加：

```python
# 新增：当前工作模式
self._mode = WorkMode.TRANSCRIBE

# 新增：翻译热键监听器
self._translate_hotkey = HotkeyListener("cmd+shift+t")
```

- [ ] **Step 3: 修改 _setup_connections 方法**

在 `_setup_connections` 方法末尾（第 72 行后）添加：

```python
# 新增：翻译热键连接
self._translate_hotkey.hotkey_pressed.connect(self._on_translate_hotkey_pressed)
self._translate_hotkey.hotkey_released.connect(self._on_translate_hotkey_released)
```

- [ ] **Step 4: 修改 start 方法**

在 `start` 方法中（第 98 行 `self._hotkey_listener.start()` 后）添加：

```python
self._translate_hotkey.start()       # 新增
```

- [ ] **Step 5: 修改 _on_recording_stopped 方法**

修改 `_on_recording_stopped` 方法（第 138-157 行），在检查 audio_bytes 后添加模式分发：

```python
def _on_recording_stopped(self, audio_bytes: bytes):
    """Handle recording stopped event.

    Args:
        audio_bytes: The recorded audio as WAV bytes.
    """
    self._tray.set_recording(False)

    # Check if we got audio
    if not audio_bytes:
        self._tray.show_message(
            "SpeechMate",
            "No audio recorded",
            icon=self._tray.Warning,
            msecs=2000
        )
        return

    # 根据 mode 分发
    if self._mode == WorkMode.TRANSLATE:
        self._process_audio_with_translation(audio_bytes)
    else:
        self._process_audio(audio_bytes)
```

- [ ] **Step 6: 添加翻译热键处理方法**

在 `_process_audio` 方法后（第 202 行后）添加：

```python
def _on_translate_hotkey_pressed(self):
    """Handle Cmd+Shift+T press - start recording in translate mode."""
    print("[DEBUG] _on_translate_hotkey_pressed called")
    if self._processing:
        print("[DEBUG] Ignoring hotkey - already processing")
        return

    self._mode = WorkMode.TRANSLATE
    self._tray.set_mode(WorkMode.TRANSLATE)
    print("[DEBUG] Starting recording in TRANSLATE mode...")
    self._recorder.start_recording()


def _on_translate_hotkey_released(self):
    """Handle Cmd+Shift+T release - stop recording."""
    print("[DEBUG] _on_translate_hotkey_released called")
    if self._processing:
        return

    print("[DEBUG] Stopping recording...")
    self._recorder.stop_recording()
```

- [ ] **Step 7: 添加翻译处理方法**

在 `_on_translate_hotkey_released` 方法后添加：

```python
def _process_audio_with_translation(self, audio_bytes: bytes):
    """Process recorded audio with translation - transcribe, translate, paste.

    Args:
        audio_bytes: The recorded audio as WAV bytes.
    """
    self._processing = True

    # Show processing notification
    self._tray.show_message(
        "SpeechMate",
        "识别中...",
        msecs=1000
    )

    # Step 1: Transcribe
    success, result = self._client.transcribe(audio_bytes)

    if not success:
        self._tray.show_message(
            "SpeechMate",
            f"识别失败: {result}",
            icon=self._tray.Warning,
            msecs=3000
        )
        self._processing = False
        return

    if not result:
        self._tray.show_message(
            "SpeechMate",
            "未检测到语音",
            icon=self._tray.Warning,
            msecs=2000
        )
        self._processing = False
        return

    # Step 2: Translate
    target_lang = get_target_lang(result)
    self._tray.show_message(
        "SpeechMate",
        "翻译中...",
        msecs=1000
    )

    trans_success, translated = self._client.translate(result, target_lang)

    if trans_success:
        # 输出：原文 + 换行 + 译文
        final_result = f"{result}\n{translated}"
        self._tray.show_message(
            "SpeechMate",
            "翻译完成",
            msecs=2000
        )
    else:
        # 降级：翻译失败仍输出原文
        final_result = result
        self._tray.show_message(
            "SpeechMate",
            f"翻译失败，已输出原文: {translated}",
            icon=self._tray.Warning,
            msecs=3000
        )

    # Paste result
    self._clipboard.paste_text(final_result)
    self._processing = False
```

- [ ] **Step 8: 修改 _cleanup 方法**

在 `_cleanup` 方法中（第 210 行 `self._hotkey_listener.stop()` 后）添加：

```python
self._translate_hotkey.stop()         # 新增
```

- [ ] **Step 9: 验证语法正确**

Run: `cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate && python -c "from client.main import SpeechMateApp; print('OK')"`

Expected: 输出 `OK`

- [ ] **Step 10: Commit**

```bash
git add client/main.py
git commit -m "$(cat <<'EOF'
feat(client): add translation hotkey and mode dispatch

- Add Cmd+Shift+T hotkey for translation mode
- Add _process_audio_with_translation() for transcribe-translate flow
- Add mode dispatch in _on_recording_stopped()
- Output format: original text + newline + translation
- Graceful degradation: output original text if translation fails

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 手动集成测试

**Files:**
- None (手动测试)

- [ ] **Step 1: 启动 Host Server**

Run: `cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate/host && uvicorn main:app --host 127.0.0.1 --port 8001`

Expected: Server 启动成功，监听 8001 端口

- [ ] **Step 2: 启动 Client**

Run: `cd /Users/zhanglin/Documents/claude_code_projects/SpeechMate && python -m client.main`

Expected:
- 浮动面板显示在右上角
- 蓝色圆点 + "SM"
- 控制台输出 `[DEBUG] FloatingPanel initialized`

- [ ] **Step 3: 测试原有功能（回归测试）**

操作：
1. 按住 `Cmd+Shift+R` 开始录音（圆点变红）
2. 说话（如 "你好世界"）
3. 松开 `Cmd+Shift+R` 停止录音
4. 等待识别完成

Expected:
- 识别的文本自动粘贴到光标位置
- 浮动面板恢复蓝色

- [ ] **Step 4: 测试翻译功能**

操作：
1. 按住 `Cmd+Shift+T` 开始录音（圆点变红）
2. 说话（如 "你好世界"）
3. 松开 `Cmd+Shift+T` 停止录音
4. 等待翻译完成

Expected:
- 浮动面板变绿（翻译模式）
- 输出格式：原文 + 换行 + 译文
- 例如：`你好世界\nHello World`

- [ ] **Step 5: 测试模式颜色切换**

操作：
1. 使用 `Cmd+Shift+T` 录音后，观察面板颜色恢复为绿色
2. 再使用 `Cmd+Shift+R` 录音后，观察面板颜色恢复为蓝色

Expected:
- 翻译模式结束后面板为绿色
- 识别模式结束后面板为蓝色

- [ ] **Step 6: 最终 Commit（如有遗漏）**

如果测试中发现问题并修复：

```bash
git add -A
git commit -m "$(cat <<'EOF'
fix(client): fix issues found in integration testing

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## 完成检查

- [ ] 所有单元测试通过
- [ ] 原有 `Cmd+Shift+R` 功能正常
- [ ] 新增 `Cmd+Shift+T` 翻译功能正常
- [ ] 翻译输出格式正确（原文 + 换行 + 译文）
- [ ] 翻译失败时降级输出原文
- [ ] 浮动面板颜色正确切换（蓝/绿）
