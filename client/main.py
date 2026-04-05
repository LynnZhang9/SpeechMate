#!/usr/bin/env python3
"""SpeechMate Client - Main entry point."""

import sys
from PyQt5.QtWidgets import QApplication
from client.tray import TrayIcon


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

    # TODO: Initialize hotkey listener
    # TODO: Initialize audio recorder

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
