#!/usr/bin/env python3
"""SpeechMate Client - Main entry point."""

import sys
from PyQt5.QtWidgets import QApplication
from client.tray import TrayIcon
from client.hotkey import HotkeyListener


def main():
    """Main entry point for the SpeechMate client application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Initialize system tray icon
    tray = TrayIcon()
    tray.show()
    tray.exit_requested.connect(app.quit)

    # Initialize hotkey listener
    hotkey_listener = HotkeyListener()
    hotkey_listener.start()

    # Connect hotkey signals to tray icon recording state
    hotkey_listener.hotkey_pressed.connect(lambda: tray.set_recording(True))
    hotkey_listener.hotkey_released.connect(lambda: tray.set_recording(False))

    # Ensure hotkey listener stops on app exit
    app.aboutToQuit.connect(hotkey_listener.stop)

    # TODO: Initialize audio recorder

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
