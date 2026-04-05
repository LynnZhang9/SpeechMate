"""Tests for the HotkeyListener class."""

import unittest
from unittest.mock import patch, MagicMock
from PyQt5.QtCore import QObject
from client.hotkey import HotkeyListener
from pynput import keyboard


class TestHotkeyListener(unittest.TestCase):
    """Test cases for HotkeyListener."""

    def test_init_default_hotkey(self):
        """Test initialization with default hotkey (F8)."""
        listener = HotkeyListener()
        self.assertEqual(listener._hotkey, keyboard.Key.f8)
        self.assertFalse(listener.is_running)

    def test_init_custom_hotkey(self):
        """Test initialization with custom hotkey."""
        custom_key = keyboard.Key.f9
        listener = HotkeyListener(hotkey=custom_key)
        self.assertEqual(listener._hotkey, custom_key)
        self.assertFalse(listener.is_running)

    def test_start_creates_listener(self):
        """Test that start() creates a pynput listener."""
        listener = HotkeyListener()

        with patch('client.hotkey.keyboard.Listener') as MockListener:
            mock_listener_instance = MagicMock()
            MockListener.return_value = mock_listener_instance

            result = listener.start()

            self.assertTrue(result)
            self.assertTrue(listener.is_running)
            MockListener.assert_called_once()
            mock_listener_instance.start.assert_called_once()

    def test_start_returns_false_if_already_running(self):
        """Test that start() returns False if already running."""
        listener = HotkeyListener()

        with patch('client.hotkey.keyboard.Listener') as MockListener:
            mock_listener_instance = MagicMock()
            MockListener.return_value = mock_listener_instance

            listener.start()
            result = listener.start()

            self.assertFalse(result)
            self.assertTrue(listener.is_running)

    def test_stop_stops_listener(self):
        """Test that stop() stops the pynput listener."""
        listener = HotkeyListener()

        with patch('client.hotkey.keyboard.Listener') as MockListener:
            mock_listener_instance = MagicMock()
            MockListener.return_value = mock_listener_instance

            listener.start()
            result = listener.stop()

            self.assertTrue(result)
            self.assertFalse(listener.is_running)
            mock_listener_instance.stop.assert_called_once()

    def test_stop_returns_false_if_not_running(self):
        """Test that stop() returns False if not running."""
        listener = HotkeyListener()
        result = listener.stop()
        self.assertFalse(result)
        self.assertFalse(listener.is_running)

    def test_on_press_emits_signal_for_correct_key(self):
        """Test that _on_press emits hotkey_pressed for the correct key."""
        listener = HotkeyListener()

        with patch.object(listener, 'hotkey_pressed') as mock_signal:
            listener._on_press(keyboard.Key.f8)
            mock_signal.emit.assert_called_once()

    def test_on_press_does_not_emit_for_wrong_key(self):
        """Test that _on_press does not emit for wrong key."""
        listener = HotkeyListener()

        with patch.object(listener, 'hotkey_pressed') as mock_signal:
            listener._on_press(keyboard.Key.f9)
            mock_signal.emit.assert_not_called()

    def test_on_release_emits_signal_for_correct_key(self):
        """Test that _on_release emits hotkey_released for the correct key."""
        listener = HotkeyListener()

        with patch.object(listener, 'hotkey_released') as mock_signal:
            listener._on_release(keyboard.Key.f8)
            mock_signal.emit.assert_called_once()

    def test_on_release_does_not_emit_for_wrong_key(self):
        """Test that _on_release does not emit for wrong key."""
        listener = HotkeyListener()

        with patch.object(listener, 'hotkey_released') as mock_signal:
            listener._on_release(keyboard.Key.f9)
            mock_signal.emit.assert_not_called()

    def test_on_press_returns_true(self):
        """Test that _on_press always returns True to continue listening."""
        listener = HotkeyListener()
        self.assertTrue(listener._on_press(keyboard.Key.f8))
        self.assertTrue(listener._on_press(keyboard.Key.f9))

    def test_on_release_returns_true(self):
        """Test that _on_release always returns True to continue listening."""
        listener = HotkeyListener()
        self.assertTrue(listener._on_release(keyboard.Key.f8))
        self.assertTrue(listener._on_release(keyboard.Key.f9))


if __name__ == '__main__':
    unittest.main()
