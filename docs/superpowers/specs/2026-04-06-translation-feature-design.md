# SpeechMate 中英翻译功能设计

日期：2026-04-06

## 概述

为 SpeechMate 添加中英翻译功能，用户可通过独立热键触发语音翻译。

## 需求摘要

| 项目 | 决定 |
|------|------|
| 触发方式 | 独立热键 `Cmd+Shift+T`，预留其他方式扩展点 |
| 翻译方向 | 自动检测（中文→英文，英文→中文） |
| 输出内容 | 原文 + 译文 |
| 分隔符 | 换行 |

## 架构设计

### 新增组件

```
client/
├── modes.py              # 新增：WorkMode 枚举 + 语言检测
├── main.py               # 修改：支持多热键 + 模式分发
├── hotkey.py             # 无需修改（已支持任意热键）
├── floating_panel.py     # 修改：显示当前模式状态
└── ...
```

### WorkMode 枚举

```python
class WorkMode(Enum):
    TRANSCRIBE = "transcribe"   # 语音识别（默认）
    TRANSLATE = "translate"     # 语音翻译
    # 预留扩展
    # AUTO = "auto"             # 未来：自动检测是否翻译
```

### 热键绑定

| 热键 | 模式 |
|------|------|
| `Cmd+Shift+R` | TRANSCRIBE（语音识别） |
| `Cmd+Shift+T` | TRANSLATE（语音翻译） |

## 组件详细设计

### 1. modes.py - 工作模式与语言检测

```python
from enum import Enum

class WorkMode(Enum):
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"


def detect_language(text: str) -> str:
    """检测文本语言，返回 'zh' 或 'en'"""
    if not text:
        return "zh"
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if chinese_chars / len(text) > 0.3:
        return "zh"
    return "en"


def get_target_lang(text: str) -> str:
    """根据源语言返回目标语言"""
    return "en" if detect_language(text) == "zh" else "zh"
```

### 2. main.py - 核心流程

**初始化改动**

```python
from client.modes import WorkMode, get_target_lang

class SpeechMateApp:
    def __init__(self, app: QApplication):
        # ... 现有代码不变 ...

        # 新增：当前工作模式
        self._mode = WorkMode.TRANSCRIBE

        # 新增：翻译热键监听器
        self._translate_hotkey = HotkeyListener("cmd+shift+t")
```

**连接设置改动**

```python
def _setup_connections(self):
    # ... 现有连接保持不变 ...

    # 新增：翻译热键连接
    self._translate_hotkey.hotkey_pressed.connect(self._on_translate_hotkey_pressed)
    self._translate_hotkey.hotkey_released.connect(self._on_translate_hotkey_released)
```

**启动改动**

```python
def start(self) -> int:
    # ... 现有代码 ...
    self._hotkey_listener.start()        # 原有
    self._translate_hotkey.start()       # 新增
    return self._app.exec_()
```

**录音停止处理改动**

```python
def _on_recording_stopped(self, audio_bytes: bytes):
    self._tray.set_recording(False)
    if not audio_bytes:
        # ... 原有逻辑不变 ...
        return

    # 根据 mode 分发
    if self._mode == WorkMode.TRANSLATE:
        self._process_audio_with_translation(audio_bytes)
    else:
        self._process_audio(audio_bytes)  # 原有方法，不改
```

**新增翻译处理方法**

```python
def _process_audio_with_translation(self, audio_bytes: bytes):
    """录音 → 识别 → 翻译 → 粘贴"""
    self._processing = True
    self._tray.show_message("SpeechMate", "识别中...")

    # 1. 语音识别
    success, text = self._client.transcribe(audio_bytes)
    if not success:
        self._tray.show_message("SpeechMate", f"识别失败: {text}", icon=self._tray.Warning, msecs=3000)
        self._processing = False
        return
    if not text:
        self._tray.show_message("SpeechMate", "未检测到语音", icon=self._tray.Warning, msecs=2000)
        self._processing = False
        return

    # 2. 检测语言并翻译
    target_lang = get_target_lang(text)
    success, translated = self._client.translate(text, target_lang)

    if success:
        result = f"{text}\n{translated}"
        self._tray.show_message("SpeechMate", "翻译完成", msecs=2000)
    else:
        # 降级：翻译失败仍输出原文
        result = text
        self._tray.show_message("SpeechMate", f"翻译失败，已输出原文", icon=self._tray.Warning, msecs=3000)

    self._clipboard.paste_text(result)
    self._processing = False
```

**新增翻译热键处理**

```python
def _on_translate_hotkey_pressed(self):
    """Handle Cmd+Shift+T press - start recording in translate mode."""
    if self._processing:
        return
    self._mode = WorkMode.TRANSLATE
    self._tray.set_mode(WorkMode.TRANSLATE)
    self._recorder.start_recording()

def _on_translate_hotkey_released(self):
    """Handle Cmd+Shift+T release - stop recording."""
    if self._processing:
        return
    self._recorder.stop_recording()
```

**清理改动**

```python
def _cleanup(self):
    self._hotkey_listener.stop()          # 原有
    self._translate_hotkey.stop()         # 新增
    # ... 其他原有代码 ...
```

### 3. floating_panel.py - 状态显示

**新增方法**

```python
from client.modes import WorkMode

def set_mode(self, mode: WorkMode):
    """设置当前模式，更新面板颜色"""
    self._mode = mode
    if mode == WorkMode.TRANSLATE:
        self._dot_color = QColor("#4CAF50")  # 绿色
    else:
        self._dot_color = QColor("#2196F3")  # 蓝色
    self.update()
```

**状态颜色对照**

| 状态 | 显示 |
|------|------|
| 就绪（识别模式） | 蓝色圆点 + "SM" |
| 就绪（翻译模式） | 绿色圆点 + "SM" |
| 录音中 | 红色圆点 |
| 处理中 | 橙色圆点 |

## 错误处理

| 场景 | 处理 |
|------|------|
| 语音识别失败 | 显示错误，不调用翻译 |
| 识别结果为空 | 提示"未检测到语音"，结束 |
| 翻译 API 失败 | 显示警告，已识别的原文仍粘贴（降级处理） |

## 测试计划

| 测试项 | 方法 |
|--------|------|
| 语言检测 | 单元测试：中文、英文、混合文本 |
| 翻译热键 | 手动测试：Cmd+Shift+T 触发录音 |
| 原有功能 | 回归测试：Cmd+Shift+R 仍正常工作 |
| 错误降级 | 模拟翻译 API 失败，验证原文仍输出 |
| 模式切换 | 验证浮动面板颜色正确切换 |

## 向后兼容

- 原有 `_process_audio()` 方法完全不变
- 原有 `Cmd+Shift+R` 热键行为不变
- 原有浮动面板默认状态（蓝色）不变
