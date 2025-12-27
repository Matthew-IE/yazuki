import sys
import ctypes
from PySide6.QtCore import Qt, QPoint # type: ignore
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget # type: ignore
from PySide6.QtGui import QKeyEvent # type: ignore

# Windows API constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

class OverlayWindow(QMainWindow):
    def __init__(self, config, renderer_widget):
        super().__init__()
        self.config = config
        self.renderer = renderer_widget
        
        # Window setup
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowSystemMenuHint |
            Qt.Tool # Tool window doesn't show in taskbar usually, but maybe we want it to.
        )
        if config['window'].get('always_on_top', True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.renderer)

        # Geometry
        self.resize(config['window']['width'], config['window']['height'])
        self.move(config['window']['x'], config['window']['y'])

        # State
        self.click_through = config['window'].get('click_through', False)
        self.dragging = False
        self.drag_pos = QPoint()

        # Apply initial click-through state
        self.update_click_through()

    def update_click_through(self):
        if sys.platform == "win32":
            hwnd = self.winId()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if self.click_through:
                # Add transparent flag (click-through)
                style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
            else:
                # Remove transparent flag
                style &= ~WS_EX_TRANSPARENT
                # Keep layered if needed for transparency, but usually Qt handles it. 
                # However, for click-through to work with alpha, WS_EX_LAYERED is often needed.
                # If we remove WS_EX_TRANSPARENT, it catches clicks.
            
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            print(f"Click-through set to: {self.click_through}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_F8:
            self.click_through = not self.click_through
            self.update_click_through()
        elif event.key() == Qt.Key_F9:
            if hasattr(self.renderer, 'reload_model'):
                self.renderer.reload_model()
        elif event.key() == Qt.Key_Escape:
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if not self.click_through and event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

