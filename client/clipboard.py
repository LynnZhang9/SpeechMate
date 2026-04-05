"""Clipboard operations for SpeechMate Client.

Handles clipboard save/restore and paste simulation.
"""

import platform
import threading
import time
from typing import Optional
import pyperclip
from pynput import keyboard


class ClipboardManager:
    """Manages clipboard operations with save/restore functionality.

    Saves the current clipboard content, pastes new text, and restores
    the original content after a delay.
    """

    # Time to wait before restoring clipboard (seconds)
    RESTORE_DELAY = 0.5

    def __init__(self):
        """Initialize the clipboard manager."""
        self._controller = keyboard.Controller()
        self._is_macos = platform.system() == "Darwin"

    def _get_paste_key(self) -> keyboard.Key:
        """Get the appropriate paste key combination for the platform.

        Returns:
            The modifier key for paste (Cmd on macOS, Ctrl on others).
        """
        if self._is_macos:
            return keyboard.Key.cmd
        else:
            return keyboard.Key.ctrl

    def paste_text(self, text: str, restore_delay: float = RESTORE_DELAY) -> bool:
        """Paste text at the current cursor position.

        Saves the current clipboard, copies the new text to clipboard,
        simulates Ctrl+V (Cmd+V on macOS), and restores the original
        clipboard after a delay.

        Args:
            text: The text to paste.
            restore_delay: Time in seconds to wait before restoring clipboard.

        Returns:
            True if paste was initiated successfully, False otherwise.
        """
        if not text:
            return False

        try:
            # Save current clipboard content
            original_clipboard = self._save_clipboard()

            # Copy new text to clipboard
            pyperclip.copy(text)

            # Small delay to ensure clipboard is updated
            time.sleep(0.05)

            # Simulate paste (Ctrl+V or Cmd+V)
            self._simulate_paste()

            # Schedule clipboard restore in background thread
            if restore_delay > 0:
                restore_thread = threading.Thread(
                    target=self._restore_clipboard_after_delay,
                    args=(original_clipboard, restore_delay),
                    daemon=True
                )
                restore_thread.start()

            return True

        except Exception as e:
            print(f"Error pasting text: {e}")
            return False

    def _save_clipboard(self) -> Optional[str]:
        """Save current clipboard content.

        Returns:
            Current clipboard content as string, or None if empty/error.
        """
        try:
            return pyperclip.paste()
        except Exception:
            return None

    def _simulate_paste(self):
        """Simulate Ctrl+V (Cmd+V on macOS) key press."""
        modifier = self._get_paste_key()

        # Press modifier + V
        self._controller.press(modifier)
        self._controller.press('v')

        # Release V then modifier
        self._controller.release('v')
        self._controller.release(modifier)

    def _restore_clipboard_after_delay(self, original_content: Optional[str], delay: float):
        """Restore clipboard content after a delay.

        Args:
            original_content: The content to restore to clipboard.
            delay: Time to wait before restoring.
        """
        time.sleep(delay)

        try:
            if original_content is not None:
                pyperclip.copy(original_content)
            else:
                # Try to clear clipboard if original was empty
                try:
                    pyperclip.copy("")
                except Exception:
                    pass
        except Exception:
            pass  # Silently fail on clipboard restore
