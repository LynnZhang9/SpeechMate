"""System tray icon for SpeechMate Client."""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import pyqtSignal, QObject, Qt
import webbrowser

from client.modes import WorkMode


class TrayIcon(QSystemTrayIcon):
    """System tray icon with normal, recording states.

    Signals:
        exit_requested: Emitted when user requests to quit the application.
        config_requested: Emitted when user requests to open configuration.
    """

    # Signals
    exit_requested = pyqtSignal()
    config_requested = pyqtSignal()

    # Icon sizes
    ICON_SIZE = 64

    # Colors for different states
    COLORS = {
        "ready": QColor(59, 130, 246),      # Blue - transcribe mode
        "recording": QColor(239, 68, 66),   # Red
        "processing": QColor(245, 158, 11), # Orange
        "translate": QColor(76, 175, 80),   # Green - translate mode
    }

