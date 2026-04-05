"""Hotkey listener for SpeechMate Client.

Uses pynput to listen for global hotkey events.
"""

import threading
from typing import Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from pynput import keyboard


class HotkeyListener(QObject):
    """Global hotkey listener using pynput.

    Listens for F8 key press/release events globally and emits signals.
    Thread-safe - runs in a background thread.

    Signals:
        hotkey_pressed: Emitted when F8 is pressed down.
        hotkey_released: Emitted when F8 is released.
    """

    # Signals
    hotkey_pressed = pyqtSignal()
    hotkey_released = pyqtSignal()

    def __init__(self, hotkey: str = keyboard.Key.f8, parent: Optional[QObject] = None):
        """Initialize the hotkey listener.

        Args:
            hotkey: The key to listen for. Defaults to F8.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._hotkey = hotkey
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()
        self._is_running = False

    def _on_press(self, key) -> bool:
        """Handle key press events.

        Args:
            key: The key that was pressed.

        Returns:
            True to continue listening, False to stop.
        """
        if key == self._hotkey:
            self.hotkey_pressed.emit()
        return True  # Continue listening

    def _on_release(self, key) -> bool:
        """Handle key release events.

        Args:
            key: The key that was released.

        Returns:
            True to continue listening, False to stop.
        """
        if key == self._hotkey:
            self.hotkey_released.emit()
        return True  # Continue listening

    def start(self) -> bool:
        """Start listening for hotkey events.

        Returns:
            True if started successfully, False if already running.
        """
        with self._lock:
            if self._is_running:
                return False

            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            self._is_running = True
            return True

    def stop(self) -> bool:
        """Stop listening for hotkey events.

        Returns:
            True if stopped successfully, False if not running.
        """
        with self._lock:
            if not self._is_running or self._listener is None:
                return False

            self._listener.stop()
            self._listener = None
            self._is_running = False
            return True

    @property
    def is_running(self) -> bool:
        """Check if the listener is currently running.

        Returns:
            True if running, False otherwise.
        """
        return self._is_running
