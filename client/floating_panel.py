"""Floating panel for SpeechMate - A macOS-friendly alternative to system tray.

This provides a small floating window that shows the current status and can be
clicked to access the menu. Works reliably on macOS Sequoia where system tray
icons may not appear.
"""

import sys
import webbrowser
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QAction, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt5.QtGui import QFont, QColor, QCursor, QPalette

from client.modes import WorkMode


class FloatingPanel(QWidget):
    """A small floating panel that shows SpeechMate status.

    This is an alternative to system tray that works reliably on macOS Sequoia.

    Signals:
        exit_requested: Emitted when user requests to quit.
        config_requested: Emitted when user requests to open settings.
    """

    # Signals
    exit_requested = pyqtSignal()
    config_requested = pyqtSignal()

    # States
    STATE_READY = "ready"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"

    # Colors for different states
    COLORS = {
        "ready": "#3B82F6",      # Blue
        "recording": "#EF4444",  # Red
        "processing": "#F59E0B", # Orange/Amber
        "translate": "#4CAF50",  # Green
    }

    # Message icon constants (for compatibility with QSystemTrayIcon)
    Information = 1
    Warning = 2
    Critical = 3

    def __init__(self, parent=None, admin_url: str = "http://localhost:5000"):
        """Initialize the floating panel.

        Args:
            parent: Parent widget.
            admin_url: URL for the Web Admin interface.
        """
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self._admin_url = admin_url
        self._state = self.STATE_READY
        self._drag_pos = QPoint()
        self._mode = WorkMode.TRANSCRIBE

        # Setup UI
        self._setup_ui()

        # Set window properties
        self.setFixedSize(120, 40)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Position in top-right corner with some padding
        self._position_window()

        print(f"[DEBUG] FloatingPanel initialized")
        print(f"[DEBUG] Position: {self.pos()}")

    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Status indicator (colored circle)
        self._status_indicator = QLabel("●")
        self._status_indicator.setFont(QFont("Helvetica", 16))
        self._status_indicator.setStyleSheet(f"color: {self.COLORS['ready']};")
        layout.addWidget(self._status_indicator)

        # Status text
        self._status_label = QLabel("SM")
        self._status_label.setFont(QFont("Helvetica", 12, QFont.Bold))
        self._status_label.setStyleSheet("color: #333;")
        layout.addWidget(self._status_label)

        # Set background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 230);
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 30);
            }
        """)

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

    def _position_window(self):
        """Position the window in the top-right corner."""
        from PyQt5.QtWidgets import QApplication

        # Get the primary screen
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.width() - self.width() - 20
            y = 10  # Near the top
            self.move(x, y)

    def set_recording(self, is_recording: bool):
        """Set the recording state.

        Args:
            is_recording: True if recording, False otherwise.
        """
        if is_recording:
            self._state = self.STATE_RECORDING
            self._status_indicator.setStyleSheet(f"color: {self.COLORS['recording']};")
            self._status_label.setText("REC")
            print("[DEBUG] FloatingPanel: Recording state")
        else:
            self._state = self.STATE_READY
            # 根据当前模式设置颜色
            if self._mode == WorkMode.TRANSLATE:
                self._status_indicator.setStyleSheet(f"color: {self.COLORS['translate']};")
            else:
                self._status_indicator.setStyleSheet(f"color: {self.COLORS['ready']};")
            self._status_label.setText("SM")
            print("[DEBUG] FloatingPanel: Ready state")

    def set_processing(self, is_processing: bool):
        """Set the processing state.

        Args:
            is_processing: True if processing, False otherwise.
        """
        if is_processing:
            self._state = self.STATE_PROCESSING
            self._status_indicator.setStyleSheet(f"color: {self.COLORS['processing']};")
            self._status_label.setText("...")
            print("[DEBUG] FloatingPanel: Processing state")

    def set_mode(self, mode: WorkMode):
        """设置当前工作模式，更新面板颜色。

        Args:
            mode: 工作模式（TRANSCRIBE 或 TRANSLATE）
        """
        self._mode = mode
        # 仅在就绪状态时更新颜色
        if self._state == self.STATE_READY:
            if mode == WorkMode.TRANSLATE:
                self._status_indicator.setStyleSheet(f"color: {self.COLORS['translate']};")
            else:
                self._status_indicator.setStyleSheet(f"color: {self.COLORS['ready']};")
        print(f"[DEBUG] FloatingPanel: Mode set to {mode.value}")

    def show_message(self, title: str, message: str, icon=1, msecs: int = 3000):
        """Show a notification message.

        Args:
            title: Notification title.
            message: Notification message.
            icon: Icon type (ignored).
            msecs: Duration (ignored).
        """
        # Show as a temporary status change
        self._status_label.setText(message[:10])
        print(f"[DEBUG] FloatingPanel message: {title} - {message}")

        # Reset after a delay using QTimer
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._status_label.setText("SM"))

    def isVisible(self):
        """Check if the panel is visible."""
        return super().isVisible()

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and menu."""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self._show_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        """Handle mouse release for click action."""
        if event.button() == Qt.LeftButton:
            # Show menu on left click too
            self._show_menu(event.globalPos())

    def _show_menu(self, pos):
        """Show the context menu.

        Args:
            pos: Global position to show the menu.
        """
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3B82F6;
                color: white;
            }
        """)

        # Open settings action
        open_settings_action = QAction("打开设置", menu)
        open_settings_action.triggered.connect(self._on_open_settings)
        menu.addAction(open_settings_action)

        menu.addSeparator()

        # Status info
        status_text = "状态: 就绪" if self._state == self.STATE_READY else \
                      "状态: 录音中" if self._state == self.STATE_RECORDING else \
                      "状态: 处理中"
        status_action = QAction(status_text, menu)
        status_action.setEnabled(False)
        menu.addAction(status_action)

        menu.addSeparator()

        # Exit action
        exit_action = QAction("退出", menu)
        exit_action.triggered.connect(self._on_exit)
        menu.addAction(exit_action)

        menu.exec_(pos)

    def _on_open_settings(self):
        """Handle open settings action."""
        print("[DEBUG] FloatingPanel: Open settings")
        self.config_requested.emit()
        webbrowser.open(self._admin_url)

    def _on_exit(self):
        """Handle exit action."""
        print("[DEBUG] FloatingPanel: Exit requested")
        self.exit_requested.emit()


def create_tray_icon(parent=None, admin_url: str = "http://localhost:5000"):
    """Create a floating panel for macOS (alternative to system tray).

    Args:
        parent: Parent widget.
        admin_url: URL for the Web Admin interface.

    Returns:
        FloatingPanel instance.
    """
    print("[DEBUG] Creating FloatingPanel for macOS")
    return FloatingPanel(parent, admin_url)
