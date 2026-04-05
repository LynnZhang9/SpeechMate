#!/usr/bin/env python3
"""SpeechMate Client - Main entry point."""

import sys
from PyQt5.QtWidgets import QApplication


def main():
    """Main entry point for the SpeechMate client application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SpeechMate")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # TODO: Initialize system tray icon
    # TODO: Initialize hotkey listener
    # TODO: Initialize audio recorder

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
