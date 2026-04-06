"""Hotkey listener for SpeechMate Client.

Uses pynput to listen for global hotkey events.
Supports both single keys and key combinations.
"""

import threading
from typing import Optional, Set
from PyQt5.QtCore import QObject, pyqtSignal
from pynput import keyboard


class HotkeyListener(QObject):
    """Global hotkey listener using pynput.

    Listens for hotkey press/release events globally and emits signals.
    Supports key combinations like Cmd+Shift+R.

    Signals:
        hotkey_pressed: Emitted when hotkey is pressed down.
        hotkey_released: Emitted when hotkey is released.
    """

    # Signals
    hotkey_pressed = pyqtSignal()
    hotkey_released = pyqtSignal()

    # Modifier keys mapping
    MODIFIER_KEYS = {
        keyboard.Key.cmd: 'cmd',
        keyboard.Key.cmd_l: 'cmd',
        keyboard.Key.cmd_r: 'cmd',
        keyboard.Key.shift: 'shift',
        keyboard.Key.shift_l: 'shift',
        keyboard.Key.shift_r: 'shift',
        keyboard.Key.ctrl: 'ctrl',
        keyboard.Key.ctrl_l: 'ctrl',
        keyboard.Key.ctrl_r: 'ctrl',
        keyboard.Key.alt: 'alt',
        keyboard.Key.alt_l: 'alt',
        keyboard.Key.alt_r: 'alt',
    }

    def __init__(self, hotkey: str = "cmd+shift+r", parent: Optional[QObject] = None):
        """Initialize the hotkey listener.

        Args:
            hotkey: The hotkey combination (e.g., "cmd+shift+r", "f8").
                   Use "+" to separate keys. Modifiers: cmd, shift, ctrl, alt.
                   Single keys: "f8", "space", etc.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._hotkey_str = hotkey.lower()
        self._parse_hotkey(hotkey)
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()
        self._is_running = False
        self._pressed_modifiers: Set[str] = set()
        self._pressed_keys: Set[keyboard.Key] = set()

    def _parse_hotkey(self, hotkey: str):
        """Parse the hotkey string into modifiers and main key.

        Args:
            hotkey: The hotkey string (e.g., "cmd+shift+r").
        """
        parts = [p.strip().lower() for p in hotkey.split('+')]
        self._modifiers = set()
        self._main_key = None

        for part in parts:
            if part in ('cmd', 'command', '⌘'):
                self._modifiers.add('cmd')
            elif part in ('shift', '⇧'):
                self._modifiers.add('shift')
            elif part in ('ctrl', 'control', '⌃'):
                self._modifiers.add('ctrl')
            elif part in ('alt', 'option', '⌥'):
                self._modifiers.add('alt')
            else:
                # This is the main key
                self._main_key = part

        print(f"[DEBUG] Parsed hotkey: modifiers={self._modifiers}, main_key={self._main_key}")

    def _get_key_name(self, key) -> Optional[str]:
        """Get the name of a key.

        Args:
            key: The key from pynput.

        Returns:
            The key name as a string.
        """
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else None
        elif isinstance(key, keyboard.Key):
            # Handle special keys like f8, space, etc.
            key_name = str(key).replace('Key.', '').lower()
            return key_name
        return None

    def _check_hotkey_match(self) -> bool:
        """Check if the current pressed keys match the hotkey.

        Returns:
            True if the hotkey combination is pressed.
        """
        # Check if all required modifiers are pressed
        if not self._modifiers.issubset(self._pressed_modifiers):
            return False

        # Check if the main key is pressed
        if self._main_key is None:
            return False

        # Check main key in pressed keys
        for key in self._pressed_keys:
            key_name = self._get_key_name(key)
            if key_name == self._main_key:
                return True

        return False

    def _on_press(self, key) -> bool:
        """Handle key press events.

        Args:
            key: The key that was pressed.

        Returns:
            True to continue listening.
        """
        # Track modifier keys
        if key in self.MODIFIER_KEYS:
            modifier = self.MODIFIER_KEYS[key]
            self._pressed_modifiers.add(modifier)
            print(f"[DEBUG] Modifier pressed: {modifier}, current: {self._pressed_modifiers}")
        else:
            # Track regular keys
            self._pressed_keys.add(key)
            key_name = self._get_key_name(key)
            print(f"[DEBUG] Key pressed: {key} (name: {key_name})")

        # Check for hotkey match
        if self._check_hotkey_match():
            print(f"[DEBUG] Hotkey '{self._hotkey_str}' matched! Emitting signal")
            self.hotkey_pressed.emit()

        return True

    def _on_release(self, key) -> bool:
        """Handle key release events.

        Args:
            key: The key that was released.

        Returns:
            True to continue listening.
        """
        was_matched = self._check_hotkey_match()

        # Remove from tracked keys
        if key in self.MODIFIER_KEYS:
            modifier = self.MODIFIER_KEYS[key]
            self._pressed_modifiers.discard(modifier)
        else:
            self._pressed_keys.discard(key)

        # If hotkey was matched and now released, emit released signal
        if was_matched and not self._check_hotkey_match():
            print(f"[DEBUG] Hotkey '{self._hotkey_str}' released! Emitting signal")
            self.hotkey_released.emit()

        return True

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
            print(f"[DEBUG] HotkeyListener started, listening for: {self._hotkey_str}")
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
            self._pressed_modifiers.clear()
            self._pressed_keys.clear()
            print("[DEBUG] HotkeyListener stopped")
            return True

    @property
    def is_running(self) -> bool:
        """Check if the listener is currently running.

        Returns:
            True if running, False otherwise.
        """
        return self._is_running
