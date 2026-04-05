"""System tray icon for SpeechMate Client."""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush
from PyQt5.QtCore import pyqtSignal, QObject
import webbrowser


class TrayIcon(QSystemTrayIcon):
    """System tray icon with normal and recording states.

    Signals:
        exit_requested: Emitted when user requests to quit the application.
        config_requested: Emitted when user requests to open configuration.
    """

    # Signals
    exit_requested = pyqtSignal()
    config_requested = pyqtSignal()

    # Icon sizes
    ICON_SIZE = 64

    def __init__(self, parent=None, admin_url: str = "http://localhost:5000"):
        """Initialize the tray icon.

        Args:
            parent: Parent QObject.
            admin_url: URL for the Web Admin interface.
        """
        super().__init__(parent)

        self._admin_url = admin_url
        self._is_recording = False

        # Create icons
        self._normal_icon = self._create_circle_icon(QColor(59, 130, 246))  # Blue
        self._recording_icon = self._create_circle_icon(QColor(239, 68, 68))  # Red

        # Set initial icon
        self.setIcon(self._normal_icon)
        self.setToolTip("SpeechMate")

        # Setup context menu
        self._setup_menu()

    def _create_circle_icon(self, color: QColor) -> QIcon:
        """Create a circular icon with the specified color.

        Args:
            color: The fill color for the circle.

        Returns:
            QIcon with a colored circle.
        """
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(color))
        painter.setPen(QColor(0, 0, 0, 0))  # No border

        # Draw circle with small margin
        margin = 4
        painter.drawEllipse(
            margin,
            margin,
            self.ICON_SIZE - 2 * margin,
            self.ICON_SIZE - 2 * margin
        )
        painter.end()

        return QIcon(pixmap)

    def _setup_menu(self):
        """Setup the context menu for the tray icon."""
        menu = QMenu()

        # Open settings action
        open_settings_action = QAction("打开设置", menu)
        open_settings_action.triggered.connect(self._on_open_settings)
        menu.addAction(open_settings_action)

        menu.addSeparator()

        # Exit action
        exit_action = QAction("退出", menu)
        exit_action.triggered.connect(self._on_exit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def _on_open_settings(self):
        """Handle open settings action."""
        self.config_requested.emit()
        webbrowser.open(self._admin_url)

    def _on_exit(self):
        """Handle exit action."""
        self.exit_requested.emit()

    def set_recording(self, is_recording: bool):
        """Set the recording state of the tray icon.

        Args:
            is_recording: True if recording, False if normal state.
        """
        self._is_recording = is_recording
        if is_recording:
            self.setIcon(self._recording_icon)
            self.setToolTip("SpeechMate - Recording...")
        else:
            self.setIcon(self._normal_icon)
            self.setToolTip("SpeechMate")

    def show_message(self, title: str, message: str,
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
                     msecs: int = 3000):
        """Show a notification balloon from the system tray.

        Args:
            title: Notification title.
            message: Notification message content.
            icon: Icon type for the notification.
            msecs: Duration in milliseconds to show the message.
        """
        self.showMessage(title, message, icon, msecs)
