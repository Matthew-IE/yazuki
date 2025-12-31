import sys
import ctypes
from ctypes import wintypes
import os
import json
import subprocess
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, Signal # type: ignore
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QSizeGrip # type: ignore
from PySide6.QtGui import QKeyEvent, QIcon, QAction, QPainter, QPen, QColor # type: ignore
from app.settings import SettingsWindow
from app.ai_manager import AIManager

# Windows API constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WM_HOTKEY = 0x0312
MOD_NONE = 0x0000
VK_F8 = 0x77
VK_F9 = 0x78
VK_V = 0x56
HOTKEY_ID_F8 = 1
HOTKEY_ID_F9 = 2

class OverlayWindow(QMainWindow):
    ai_response_received = Signal(str, str, float)
    lip_sync_updated = Signal(float)

    def __init__(self, config, renderer_widget):
        super().__init__()
        self.config = config
        self.renderer = renderer_widget
        self.ai_manager = AIManager(config)

        # Connect AI signal
        self.ai_response_received.connect(self.on_ai_response)
        self.lip_sync_updated.connect(self.renderer.set_lip_sync)
        
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
        self.resize_mode = False

        # Size Grip (for resizing)
        self.size_grip = QSizeGrip(self)
        self.size_grip.setVisible(False)
        self.size_grip.resize(20, 20)

        # Apply initial click-through state
        self.update_click_through()

        # Settings Window
        self.settings_window = SettingsWindow(config)
        self.settings_window.scale_changed.connect(self.on_scale_changed)
        self.settings_window.offset_x_changed.connect(self.on_offset_x_changed)
        self.settings_window.offset_y_changed.connect(self.on_offset_y_changed)
        self.settings_window.click_through_toggled.connect(self.set_click_through)
        self.settings_window.always_on_top_toggled.connect(self.set_always_on_top)
        self.settings_window.look_at_mouse_toggled.connect(self.set_look_at_mouse)
        self.settings_window.random_look_toggled.connect(self.set_random_look)
        self.settings_window.random_interval_changed.connect(self.set_random_interval)
        self.settings_window.random_radius_changed.connect(self.set_random_radius)
        self.settings_window.sensitivity_changed.connect(self.set_sensitivity)
        self.settings_window.resize_mode_toggled.connect(self.set_resize_mode)
        self.settings_window.window_size_changed.connect(self.set_window_size)
        self.settings_window.reload_requested.connect(self.reload_model)
        self.settings_window.save_requested.connect(self.save_settings)
        self.settings_window.quit_requested.connect(QApplication.quit)
        self.settings_window.ai_settings_changed.connect(self.update_ai_settings)
        self.settings_window.chat_settings_changed.connect(self.update_chat_settings)
        self.settings_window.input_key_changed.connect(self.set_input_key)
        self.settings_window.clear_memory_requested.connect(self.clear_ai_memory)
        self.settings_window.memory_enabled_toggled.connect(self.set_memory_enabled)
        self.settings_window.ai_enabled_toggled.connect(self.set_ai_enabled)
        self.settings_window.tts_settings_changed.connect(self.update_ai_settings)
        self.settings_window.mouth_sensitivity_changed.connect(self.set_mouth_sensitivity)
        self.settings_window.system_prompt_changed.connect(self.set_system_prompt)
        self.settings_window.emotions_enabled_toggled.connect(self.set_emotions_enabled)
        self.settings_window.chat_edit_mode_toggled.connect(self.renderer.set_edit_mode)
        self.settings_window.chat_tab_active_changed.connect(self.renderer.set_preview_mode)
        self.renderer.chat_position_changed.connect(self.settings_window.update_chat_position)

        # System Tray Icon
        self.init_tray_icon()
        
        # Register Global Hotkeys
        self.register_hotkeys()
        
        # Input Polling Timer (for V key)
        self.input_key_vk = config.get('ai', {}).get('input_key_vk', VK_V)
        self.input_timer = QTimer()
        self.input_timer.timeout.connect(self.check_input_key)
        self.input_timer.start(50) # Check every 50ms
        self.v_key_pressed = False

    def check_input_key(self):
        # Check if AI is enabled
        if not self.config.get('ai', {}).get('enabled', False):
            return

        if sys.platform == "win32":
            # Check if configured key is down (high bit set)
            is_down = ctypes.windll.user32.GetAsyncKeyState(self.input_key_vk) & 0x8000
            
            if is_down and not self.v_key_pressed:
                # Key Pressed
                self.v_key_pressed = True
                self.renderer.set_status_text("Listening...")
                self.ai_manager.start_recording()
                
            elif not is_down and self.v_key_pressed:
                # Key Released
                self.v_key_pressed = False
                self.renderer.set_status_text("Thinking...")
                self.ai_manager.stop_recording_and_process(
                    self.ai_response_received.emit,
                    self.lip_sync_updated.emit
                )

    def set_ai_enabled(self, enabled):
        self.config.setdefault('ai', {})['enabled'] = enabled
        if not enabled:
            self.renderer.set_status_text("") # Clear any status

    def set_input_key(self, vk_code):
        self.input_key_vk = vk_code

    def on_ai_response(self, text, emotion, duration):
        # This might be called from a thread, so we should be careful with UI updates
        # But setText is usually thread-safe enough for simple strings, or we use signals.
        # For safety, let's assume it's okay or use QMetaObject.invokeMethod if needed.
        # Actually, let's just set it.
        self.renderer.set_chat_text(text, duration)
        self.renderer.set_status_text("")
        
        if hasattr(self.renderer, 'set_expression'):
            self.renderer.set_expression(emotion)

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to load an icon
        # Check media folder first, then model folder
        icon_path = os.path.join('resources', 'media', 'yazuki.png')
        if not os.path.exists(icon_path):
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
            
        self.config['window']['click_through'] = self.click_through
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
        self.config['render']['scale'] = scale

    def on_offset_x_changed(self, offset):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.offset_x = offset
            self.renderer.update()
        self.config['render']['offset_x'] = offset

    def on_offset_y_changed(self, offset):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.offset_y = offset
            self.renderer.update()
        self.config['render']['offset_y'] = offset

    def set_resize_mode(self, enabled):
        self.resize_mode = enabled
        self.size_grip.setVisible(enabled)
        
        # Pass state to renderer for drawing border
        if hasattr(self.renderer, 'show_border'):
            self.renderer.show_border = enabled
            self.renderer.update() # Trigger repaint
        
        if enabled:
            # Disable click-through when resizing
            if self.click_through:
                self.toggle_click_through(force_state=False)
        else:
            # Restore click-through if it was enabled in config? 
            # Or just leave it as is. User can re-enable it.
            pass

    def set_window_size(self, w, h):
        self.resize(w, h)
        self.config['window']['width'] = w
        self.config['window']['height'] = h

    def resizeEvent(self, event):
        # Update size grip position
        rect = self.rect()
        self.size_grip.move(rect.right() - self.size_grip.width(), rect.bottom() - self.size_grip.height())
        
        # Update settings UI
        self.settings_window.update_size_display(self.width(), self.height())
        
        # Update config
        self.config['window']['width'] = self.width()
        self.config['window']['height'] = self.height()
        
        # Update renderer
        if self.renderer:
            self.renderer.resize(self.width(), self.height())
            
        super().resizeEvent(event)

    def set_click_through(self, enabled):
        self.click_through = enabled
        self.update_click_through()
        self.action_click_through.setChecked(enabled)
        self.config['window']['click_through'] = enabled

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
        self.config['window']['always_on_top'] = enabled

    def set_look_at_mouse(self, enabled):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.look_at_mouse = enabled
            # Force update to reset look direction if disabled
            self.renderer.update()
        self.config['render']['look_at_mouse'] = enabled

    def set_random_look(self, enabled):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.random_look = enabled
        self.config['render']['random_look'] = enabled

    def set_random_interval(self, value):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.random_interval_base = value
        self.config['render']['random_interval'] = value

    def set_random_radius(self, value):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.random_radius = value
        self.config['render']['random_radius'] = value

    def set_sensitivity(self, value):
        if self.renderer.live2d_manager:
            self.renderer.live2d_manager.sensitivity = value
        self.config['render']['sensitivity'] = value

    def set_mouth_sensitivity(self, value):
        if self.ai_manager:
            self.ai_manager.set_mouth_sensitivity(value)
        self.config['render']['mouth_sensitivity'] = value

    def set_system_prompt(self, prompt):
        if self.ai_manager:
            self.ai_manager.set_system_prompt(prompt)

    def set_emotions_enabled(self, enabled):
        if self.ai_manager:
            self.ai_manager.set_emotions_enabled(enabled)

    def save_settings(self):
        try:
            # Update position in config before saving
            self.config['window']['x'] = self.x()
            self.config['window']['y'] = self.y()
            
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            print("Settings saved to config.json")
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def update_ai_settings(self):
        # Re-initialize client if key changed
        self.ai_manager.setup_client()

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

    def register_hotkeys(self):
        if sys.platform == "win32":
            hwnd = self.winId()
            # Register F8
            if not ctypes.windll.user32.RegisterHotKey(int(hwnd), HOTKEY_ID_F8, MOD_NONE, VK_F8):
                print("Failed to register F8 hotkey")
            # Register F9
            if not ctypes.windll.user32.RegisterHotKey(int(hwnd), HOTKEY_ID_F9, MOD_NONE, VK_F9):
                print("Failed to register F9 hotkey")

    def update_ai_settings(self):
        # Re-setup AI manager clients with new config
        # We don't want to create a new instance because we'd lose history
        self.ai_manager.setup_client()

    def update_chat_settings(self, settings):
        self.config['chat'] = settings
        self.renderer.update_chat_settings(settings)

    def clear_ai_memory(self):
        self.ai_manager.clear_memory()
        self.renderer.set_status_text("Memory Cleared")
        # Clear status after 2 seconds
        QTimer.singleShot(2000, lambda: self.renderer.set_status_text(""))

    def set_memory_enabled(self, enabled):
        self.ai_manager.set_memory_enabled(enabled)

    def unregister_hotkeys(self):
        if sys.platform == "win32":
            hwnd = self.winId()
            ctypes.windll.user32.UnregisterHotKey(int(hwnd), HOTKEY_ID_F8)
            ctypes.windll.user32.UnregisterHotKey(int(hwnd), HOTKEY_ID_F9)

    def nativeEvent(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                if msg.wParam == HOTKEY_ID_F8:
                    self.toggle_click_through()
                    return True, 0
                elif msg.wParam == HOTKEY_ID_F9:
                    self.reload_model()
                    return True, 0
        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        self.unregister_hotkeys()
        super().closeEvent(event)

