"""System tray icon for SpeechMate Client."""
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QPainterPath
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
        self._normal_icon = self._create_seashell_icon(self.COLORS["ready"])
        self._recording_icon = self._create_seashell_icon(self.COLORS["recording"])
        self._processing_icon = self._create_seashell_icon(self.COLORS["processing"])
        self._translate_icon = self._create_seashell_icon(self.COLORS["translate"])
        # Set initial icon
        self.setIcon(self._normal_icon)
        self.setToolTip("SpeechMate")
        # Setup context menu
        self._setup_menu()
    def _create_seashell_icon(self, color: QColor) -> QIcon:
        """Create a seashell (conch) icon with the specified color.
        Args:
            color: The fill color for the shell.
        Returns:
            QIcon with a detailed seashell design.
        """
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Center and sizing
        center_x = self.ICON_SIZE // 2
        center_y = self.ICON_SIZE // 2
        base_radius = self.ICON_SIZE * 0.35

        # Draw the main shell body - spiral shape
        shell_color = QColor(color)
        painter.setBrush(QBrush(shell_color))
        painter.setPen(QColor(0, 0, 0, 0))

        # Create the spiral shell body using multiple overlapping ellipses
        # This creates the layered, segmented look of a real seashell
        for i in range(8):
            # Each segment gets slightly lighter toward the outer edge
            segment_color = QColor(
                min(255, color.red() + i * 15),
                min(255, color.green() + i * 15),
                min(255, color.blue() + i * 15)
            )
            painter.setBrush(QBrush(segment_color))

            # Calculate position and size for each spiral segment
            angle = i * 0.4  # Spiral angle increment
            radius = base_radius * (0.3 + i * 0.09)  # Growing radius
            offset_x = center_x + (i * 3) * 0.8
            offset_y = center_y - (i * 2) * 0.5

            # Draw elliptical segment
            seg_width = radius * 1.8
            seg_height = radius * 1.2

            ellipse_path = QPainterPath()
            ellipse_path.addEllipse(
                offset_x - seg_width / 2,
                offset_y - seg_height / 2,
                seg_width,
                seg_height
            )
            painter.drawPath(ellipse_path)

        # Add shell texture lines - curved ridges following the spiral
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        texture_pen = QPen(QColor(255, 255, 255, 80), 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(texture_pen)

        for i in range(6):
            ridge_angle = i * 0.5
            ridge_radius = base_radius * (0.4 + i * 0.08)
            ridge_x = center_x + (i * 4) * 0.6
            ridge_y = center_y - (i * 2.5) * 0.4

            # Create curved ridge line
            ridge_path = QPainterPath()
            start_angle = -0.8 + ridge_angle * 0.3
            end_angle = 0.8 + ridge_angle * 0.3

            for angle in range(int((end_angle - start_angle) * 20)):
                t = start_angle + angle * 0.05
                x = ridge_x + ridge_radius * 1.5 * t
                y = ridge_y + ridge_radius * 0.8 * (1 - abs(t) * 0.5)
                if angle == 0:
                    ridge_path.moveTo(x, y)
                else:
                    ridge_path.lineTo(x, y)

            painter.drawPath(ridge_path)

        # Draw the shell opening (aperture) - darker inner area
        aperture_path = QPainterPath()
        aperture_x = center_x + self.ICON_SIZE * 0.15
        aperture_y = center_y + self.ICON_SIZE * 0.1
        aperture_radius = base_radius * 0.6

        aperture_path.addEllipse(
            aperture_x - aperture_radius,
            aperture_y - aperture_radius * 0.7,
            aperture_radius * 2,
            aperture_radius * 1.4
        )

        aperture_color = QColor(color.darker(120))
        aperture_color.setAlpha(180)
        painter.setBrush(QBrush(aperture_color))
        painter.setPen(QColor(0, 0, 0, 0))
        painter.drawPath(aperture_path)

        # Add highlight for 3D effect
        highlight_path = QPainterPath()
        highlight_x = center_x - self.ICON_SIZE * 0.1
        highlight_y = center_y - self.ICON_SIZE * 0.15

        highlight_path.addEllipse(
            highlight_x - base_radius * 0.3,
            highlight_y - base_radius * 0.2,
            base_radius * 0.6,
            base_radius * 0.4
        )

        highlight_color = QColor(255, 255, 255, 100)
        painter.setBrush(QBrush(highlight_color))
        painter.drawPath(highlight_path)

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
            msecs: Duration in milliseconds to show this message.
        """
        self.showMessage(title, message, icon, msecs)
