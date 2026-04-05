#!/usr/bin/env python3
"""SpeechMate Client - Main entry point.

A PyQt5 desktop application that:
- Runs in system tray
- Records audio when F8 is held
- Sends audio to Host Server for transcription
- Auto-pastes result to cursor position
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from client.tray import TrayIcon
from client.hotkey import HotkeyListener
from client.recorder import AudioRecorder
from client.api_client import SpeechMateClient
from client.clipboard import ClipboardManager


class SpeechMateApp:
    """Main application controller.

    Coordinates all components:
    - TrayIcon: System tray UI
    - HotkeyListener: Global F8 hotkey detection
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
        self._tray = TrayIcon()
        self._hotkey_listener = HotkeyListener()

        # Track if we're waiting for a transcription
        self._processing = False

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

        # App cleanup
        self._app.aboutToQuit.connect(self._cleanup)

    def start(self) -> int:
        """Start the application.

        Returns:
            Exit code from the application.
        """
        # Check server health
        if not self._check_server_health():
            self._tray.show()
            self._tray.show_message(
                "SpeechMate",
                "Cannot connect to server. Please start the SpeechMate Host Server.",
                icon=self._tray.Warning,
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

        return self._app.exec_()

    def _check_server_health(self) -> bool:
        """Check if the server is healthy.

        Returns:
            True if server is healthy, False otherwise.
        """
        return self._client.health_check()

    def _on_hotkey_pressed(self):
        """Handle F8 press - start recording."""
        if self._processing:
            # Ignore if already processing a recording
            return

        self._recorder.start_recording()

    def _on_hotkey_released(self):
        """Handle F8 release - stop recording and process."""
        if self._processing:
            return

        self._recorder.stop_recording()

    def _on_recording_started(self):
        """Handle recording started event."""
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

        # Process the audio
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

    def _on_exit(self):
        """Handle exit request from tray."""
        self._app.quit()

    def _cleanup(self):
        """Clean up resources on exit."""
        # Stop hotkey listener
        self._hotkey_listener.stop()

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
