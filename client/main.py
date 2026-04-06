#!/usr/bin/env python3
"""SpeechMate Client - Main entry point.

A PyQt5 desktop application that:
- Runs in system tray
- Records audio when F8 is held
- Sends audio to Host Server for transcription
- Auto-pastes result to cursor position
"""

import sys
import os

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from client.floating_panel import create_tray_icon
from client.hotkey import HotkeyListener
from client.recorder import AudioRecorder
from client.api_client import SpeechMateClient
from client.clipboard import ClipboardManager
from client.modes import WorkMode, get_target_lang


class SpeechMateApp:
    """Main application controller.

    Coordinates all components:
    - TrayIcon: System tray UI
    - HotkeyListener: Global Cmd+Shift+R hotkey detection
    - AudioRecorder: Microphone recording
    - SpeechMateClient: API communication
    - ClipboardManager: Text pasting
    """

    def __init__(self, app: QApplication):
        """Initialize the application.

        Args:
            app: The QApplication instance.
        """
        self._app = app

        # Initialize components
        self._client = SpeechMateClient()
        self._clipboard = ClipboardManager()
        self._recorder = AudioRecorder()
        self._tray = create_tray_icon()
        self._hotkey_listener = HotkeyListener("cmd+shift+r", hotkey_id="transcribe")

        # Track if we're waiting for a transcription
        self._processing = False

        # 新增：当前工作模式
        self._mode = WorkMode.TRANSCRIBE

        # 新增：翻译热键监听器
        self._translate_hotkey = HotkeyListener("cmd+shift+y", hotkey_id="translate")

        # Connect signals
        self._setup_connections()

    def _setup_connections(self):
        """Set up signal connections between components."""
        # Tray signals
        self._tray.exit_requested.connect(self._on_exit)

        # Hotkey signals
        self._hotkey_listener.hotkey_pressed.connect(self._on_hotkey_pressed)
        self._hotkey_listener.hotkey_released.connect(self._on_hotkey_released)

        # Recorder signals
        self._recorder.recording_started.connect(self._on_recording_started)
        self._recorder.recording_stopped.connect(self._on_recording_stopped)

        # 新增：翻译热键连接
        self._translate_hotkey.hotkey_pressed.connect(self._on_translate_hotkey_pressed)
        self._translate_hotkey.hotkey_released.connect(self._on_translate_hotkey_released)

        # App cleanup
        self._app.aboutToQuit.connect(self._cleanup)

    def start(self) -> int:
        """Start the application.

        Returns:
            Exit code from the application.
        """
        try:
            # Check server health
            if not self._check_server_health():
                self._tray.show()
                self._tray.show_message(
                    "SpeechMate",
                    "Cannot connect to server. Please start the SpeechMate Host Server.",
                    msecs=5000
                )
            else:
                self._tray.show()
                self._tray.show_message(
                    "SpeechMate",
                    "Ready! Hold F8 to record.",
                    msecs=2000
                )

            # Start hotkey listener
            self._hotkey_listener.start()
            self._translate_hotkey.start()       # 新增

            return self._app.exec_()
        except Exception as e:
            print(f"Error starting application: {e}")
            return 1

    def _check_server_health(self) -> bool:
        """Check if the server is healthy.

        Returns:
            True if server is healthy, False otherwise.
        """
        return self._client.health_check()

    def _on_hotkey_pressed(self):
        """Handle Cmd+Shift+R press - start recording."""
        print("[DEBUG] _on_hotkey_pressed called")
        if self._processing:
            # Ignore if already processing a recording
            print("[DEBUG] Ignoring hotkey - already processing")
            return

        self._mode = WorkMode.TRANSCRIBE
        self._tray.set_mode(WorkMode.TRANSCRIBE)
        print("[DEBUG] Starting recording...")
        self._recorder.start_recording()

    def _on_hotkey_released(self):
        """Handle F8 release - stop recording and process."""
        print("[DEBUG] _on_hotkey_released called")
        if self._processing:
            return

        print("[DEBUG] Stopping recording...")
        self._recorder.stop_recording()

    def _on_recording_started(self):
        """Handle recording started event."""
        print("[DEBUG] _on_recording_started called")
        self._tray.set_recording(True)

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

    def _process_audio(self, audio_bytes: bytes):
        """Process recorded audio - send to server and paste result.

        Args:
            audio_bytes: The recorded audio as WAV bytes.
        """
        self._processing = True

        # Show processing notification
        self._tray.show_message(
            "SpeechMate",
            "Processing...",
            msecs=1000
        )

        # Send to server for transcription
        success, result = self._client.transcribe(audio_bytes)

        if success:
            if result:
                # Paste the transcribed text
                self._clipboard.paste_text(result)
                self._tray.show_message(
                    "SpeechMate",
                    f"Pasted: {result[:50]}{'...' if len(result) > 50 else ''}",
                    msecs=2000
                )
            else:
                self._tray.show_message(
                    "SpeechMate",
                    "No speech detected",
                    icon=self._tray.Warning,
                    msecs=2000
                )
        else:
            # Show error
            self._tray.show_message(
                "SpeechMate",
                f"Error: {result}",
                icon=self._tray.Critical,
                msecs=3000
            )

        self._processing = False

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

    def _on_exit(self):
        """Handle exit request from tray."""
        self._app.quit()

    def _cleanup(self):
        """Clean up resources on exit."""
        # Stop hotkey listener
        self._hotkey_listener.stop()
        self._translate_hotkey.stop()         # 新增

        # Stop recording if in progress
        if self._recorder.is_recording:
            self._recorder.stop_recording()

        # Close API client
        self._client.close()


def main():
    """Main entry point for the SpeechMate client application."""
    # High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Create and start the application
    speechmate = SpeechMateApp(app)
    return speechmate.start()


if __name__ == "__main__":
    sys.exit(main())
