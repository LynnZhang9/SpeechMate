"""Hotkey listener for SpeechMate Client.

Uses pynput to listen for global hotkey events.
Supports both single keys and key combinations.
"""

import threading
from typing import Optional, Set, Dict
from PyQt5.QtCore import QObject, pyqtSignal
from pynput import keyboard


class HotkeyListener(QObject):
    """Global hotkey listener using pynput.

    Uses a SINGLE pynput listener to handle multiple hotkey combinations.
    Supports key combinations like Cmd+Shift+R.

    Signals:
        hotkey_pressed: Emitted when a registered hotkey is pressed (arg: hotkey_id)
        hotkey_released: Emitted when a registered hotkey is released (arg: hotkey_id)
    """

    # Signals - now with hotkey_id argument
    hotkey_pressed = pyqtSignal(str)   # hotkey_id
    hotkey_released = pyqtSignal(str)  # hotkey_id

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

    # Class-level shared listener
    _shared_listener: Optional[keyboard.Listener] = None
    _shared_lock = threading.Lock()
    _instances: Dict[str, 'HotkeyListener'] = {}
    _pressed_modifiers: Set[str] = set()
    _pressed_keys: Set = set()
    _active_hotkeys: Set[str] = set()  # Track which hotkeys are currently active

    def __init__(self, hotkey: str = "cmd+shift+r", hotkey_id: Optional[str] = None, parent: Optional[QObject] = None):
        """Initialize the hotkey listener.

        Args:
            hotkey: The hotkey combination (e.g., "cmd+shift+r", "f8").
            hotkey_id: Unique identifier for this hotkey (defaults to hotkey string).
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._hotkey_str = hotkey.lower()
        self._hotkey_id = hotkey_id or self._hotkey_str
        self._parse_hotkey(hotkey)
        self._is_running = False

        # Register this instance
        with self._shared_lock:
            HotkeyListener._instances[self._hotkey_id] = self

    def _parse_hotkey(self, hotkey: str):
        """Parse the hotkey string into modifiers and main key."""
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
                self._main_key = part

    @classmethod
    def _get_key_name(cls, key) -> Optional[str]:
        """Get the name of a key."""
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else None
        elif isinstance(key, keyboard.Key):
            return str(key).replace('Key.', '').lower()
        return None

    def _check_hotkey_match(self, pressed_modifiers: Set[str], pressed_keys: Set) -> bool:
        """Check if the current pressed keys match this hotkey."""
        if not self._modifiers.issubset(pressed_modifiers):
            return False
        if self._main_key is None:
            return False
        for key in pressed_keys:
            key_name = self._get_key_name(key)
            if key_name == self._main_key:
                return True
        return False

    @classmethod
    def _shared_on_press(cls, key) -> bool:
        """Handle key press events for ALL registered hotkeys."""
        with cls._shared_lock:
            # Track modifiers globally
            if key in cls.MODIFIER_KEYS:
                modifier = cls.MODIFIER_KEYS[key]
                cls._pressed_modifiers.add(modifier)
            else:
                cls._pressed_keys.add(key)

            # Check each registered hotkey
            for hotkey_id, instance in cls._instances.items():
                if instance._check_hotkey_match(cls._pressed_modifiers, cls._pressed_keys):
                    # Only emit press signal if this hotkey is not already active
                    if hotkey_id not in cls._active_hotkeys:
                        cls._active_hotkeys.add(hotkey_id)
                        instance.hotkey_pressed.emit(hotkey_id)

        return True

    @classmethod
    def _shared_on_release(cls, key) -> bool:
        """Handle key release events for ALL registered hotkeys."""
        with cls._shared_lock:
            # First, check which hotkeys are currently matched (before releasing)
            was_matched = {}
            for hotkey_id, instance in cls._instances.items():
                was_matched[hotkey_id] = instance._check_hotkey_match(cls._pressed_modifiers, cls._pressed_keys)

            # Update global state
            if key in cls.MODIFIER_KEYS:
                modifier = cls.MODIFIER_KEYS[key]
                cls._pressed_modifiers.discard(modifier)
            else:
                cls._pressed_keys.discard(key)

            # Check for release after state update
            for hotkey_id, instance in cls._instances.items():
                now_matched = instance._check_hotkey_match(cls._pressed_modifiers, cls._pressed_keys)
                # Only emit release signal if:
                # 1. Was matched before release
                # 2. Is not matched after release
                # 3. Is in active hotkeys (was actually triggered)
                if was_matched.get(hotkey_id, False) and not now_matched and hotkey_id in cls._active_hotkeys:
                    cls._active_hotkeys.discard(hotkey_id)
                    instance.hotkey_released.emit(hotkey_id)

        return True

    def start(self) -> bool:
        """Start listening for hotkey events."""
        with self._shared_lock:
            if self._is_running:
                return False

            # Start shared listener if not running
            if HotkeyListener._shared_listener is None:
                HotkeyListener._shared_listener = keyboard.Listener(
                    on_press=HotkeyListener._shared_on_press,
                    on_release=HotkeyListener._shared_on_release
                )
                HotkeyListener._shared_listener.start()

            self._is_running = True
            return True

    def stop(self) -> bool:
        """Stop listening for this hotkey (unregister)."""
        with self._shared_lock:
            if not self._is_running:
                return False

            # Unregister this instance
            if self._hotkey_id in HotkeyListener._instances:
                del HotkeyListener._instances[self._hotkey_id]

            self._is_running = False

            # Stop shared listener if no more instances
            if not HotkeyListener._instances and HotkeyListener._shared_listener:
                HotkeyListener._shared_listener.stop()
                HotkeyListener._shared_listener = None
                print(f"[DEBUG] Shared HotkeyListener stopped")

            return True

    @property
    def is_running(self) -> bool:
        """Check if this hotkey is registered."""
        return self._is_running
