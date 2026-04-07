"""System tray icon for SpeechMate Client."""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import pyqtSignal, QObject, Qt
import webbrowser

from client.modes import WorkMode


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

    # Colors for different states
    COLORS = {
        "ready": QColor(59, 130, 246),      # Blue - transcribe mode
        "recording": QColor(239, 68, 68),   # Red
        "processing": QColor(245, 158, 11), # Orange
        "translate": QColor(76, 175, 80),   # Green - translate mode
    }

    def __init__(self, parent=None, admin_url: str = "http://localhost:5000"):
        """Initialize the tray icon.

        Args:
            parent: Parent QObject.
            admin_url: URL for the Web Admin interface.
        """
        super().__init__(parent)

        self._admin_url = admin_url
        self._is_recording = False
        self._mode = WorkMode.TRANSCRIBE

        # Create icons
        self._normal_icon = self._create_wave_icon(self.COLORS["ready"])
        self._recording_icon = self._create_wave_icon(self.COLORS["recording"])
        self._processing_icon = self._create_wave_icon(self.COLORS["processing"])
        self._translate_icon = self._create_wave_icon(self.COLORS["translate"])

        # Set initial icon
        self.setIcon(self._normal_icon)
        self.setToolTip("SpeechMate")

        # Setup context menu
        self._setup_menu()

    def _create_wave_icon(self, color: QColor) -> QIcon:
        """Create a sound wave icon with the specified color.

        Args:
            color: The fill color for the wave.

        Returns:
            QIcon with a sound wave design.
        """
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QBrush(color))
        painter.setPen(QColor(0, 0, 0, 0))  # No border

        # Draw sound wave (3 curved lines)
        center_y = self.ICON_SIZE // 2
        margin = 8
        wave_width = self.ICON_SIZE - 2 * margin

        # Wave parameters - multiple curved lines to create wave effect
        painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))

        # Draw three curved wave lines
        for i in range(3):
            # Each wave line: curved path from left to right
            start_x = margin
            start_y = center_y - 8 + i * 6
            mid_y = center_y + 4 + i * 4
            end_x = self.ICON_SIZE - margin

            end_y = start_y  # End at same height

            # Draw smooth curve using cubic Bezier
            path = QPainterPath()
            path.moveTo(start_x, start_y)
            # Control points for the curve
            ctrl1_x = start_x + wave_width * 0.3
            ctrl1_y = start_y - 4
            ctrl2_x = start_x + wave_width * 0.7
            ctrl2_y = end_y + 4
            path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_x, end_y)
            painter.drawPath(path)

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
            # Restore to current mode's icon
            self.set_mode(self._mode)

    def set_processing(self, is_processing: bool):
        """Set the processing state of the tray icon.

        Args:
            is_processing: True if processing, False if normal state.
        """
        if is_processing:
            self.setIcon(self._processing_icon)
            self.setToolTip("SpeechMate - Processing...")
        else:
            # Restore to current mode's icon
            self.set_mode(self._mode)

    def set_mode(self, mode: WorkMode):
        """Set the work mode of the tray icon.

        Args:
            mode: WorkMode.TRANSCRIBE or WorkMode.TRANSLATE
        """
        self._mode = mode
        if not self._is_recording:
            if mode == WorkMode.TRANSLATE:
                self.setIcon(self._translate_icon)
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
