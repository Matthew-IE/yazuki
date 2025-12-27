import sys
import ctypes
import os
import subprocess
from PySide6.QtCore import Qt, QPoint # type: ignore
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu # type: ignore
from PySide6.QtGui import QKeyEvent, QIcon, QAction # type: ignore
from app.settings import SettingsWindow

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

        # Settings Window
        self.settings_window = SettingsWindow(config)
        self.settings_window.scale_changed.connect(self.on_scale_changed)
        self.settings_window.offset_x_changed.connect(self.on_offset_x_changed)
        self.settings_window.offset_y_changed.connect(self.on_offset_y_changed)
        self.settings_window.click_through_toggled.connect(self.set_click_through)
        self.settings_window.always_on_top_toggled.connect(self.set_always_on_top)
        self.settings_window.reload_requested.connect(self.reload_model)

        # System Tray Icon
        self.init_tray_icon()

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to load an icon
        icon_path = os.path.join(self.config['model_folder'], 'yazuki.png')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback or standard icon
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

        # Context Menu
        tray_menu = QMenu()
        
        self.action_click_through = QAction("Click-Through", self)
        self.action_click_through.setCheckable(True)
        self.action_click_through.setChecked(self.click_through)
        self.action_click_through.triggered.connect(self.toggle_click_through)
        tray_menu.addAction(self.action_click_through)
        
        action_reload = QAction("Reload Model", self)
        action_reload.triggered.connect(self.reload_model)
        tray_menu.addAction(action_reload)

        action_settings = QAction("Settings", self)
        action_settings.triggered.connect(self.show_settings)
        tray_menu.addAction(action_settings)
        
        tray_menu.addSeparator()
        
        action_quit = QAction("Quit", self)
        action_quit.triggered.connect(QApplication.quit)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_click_through(self):
        # If called from menu, the state might already be toggled, but we manage it manually
        # to keep sync between F8 and Menu.
        # Actually, if called from menu triggered, the checked state updates automatically?
        # Let's rely on self.click_through as source of truth.
        
        # If sender is the action, update self.click_through from the action
        if self.sender() == self.action_click_through:
            self.click_through = self.action_click_through.isChecked()
        else:
            # If called from F8, toggle boolean and update action
            self.click_through = not self.click_through
            self.action_click_through.setChecked(self.click_through)
            
        self.update_click_through()
        self.settings_window.update_state(self.click_through)

    def reload_model(self):
        if hasattr(self.renderer, 'reload_model'):
            self.renderer.reload_model()

    def show_settings(self):
        self.settings_window.show()
        self.settings_window.activateWindow()

    def on_scale_changed(self, scale):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.scale = scale
            self.renderer.update()

    def on_offset_x_changed(self, offset):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.offset_x = offset
            self.renderer.update()

    def on_offset_y_changed(self, offset):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.offset_y = offset
            self.renderer.update()

    def set_click_through(self, enabled):
        self.click_through = enabled
        self.update_click_through()
        self.action_click_through.setChecked(enabled)

    def set_always_on_top(self, enabled):
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show() # Re-show needed after flag change
        # Re-apply click-through state because changing flags might reset window style
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
            self.toggle_click_through()
        elif event.key() == Qt.Key_F9:
            self.reload_model()
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

