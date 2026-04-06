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
