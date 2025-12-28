import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton, QGroupBox, QSpinBox, QTabWidget, QFrame) # type: ignore
from PySide6.QtCore import Qt, Signal # type: ignore
from PySide6.QtGui import QIcon # type: ignore

class SettingsWindow(QWidget):
    scale_changed = Signal(float)
    offset_x_changed = Signal(float)
    offset_y_changed = Signal(float)
    click_through_toggled = Signal(bool)
    always_on_top_toggled = Signal(bool)
    look_at_mouse_toggled = Signal(bool)
    sensitivity_changed = Signal(float)
    resize_mode_toggled = Signal(bool)
    window_size_changed = Signal(int, int)
    reload_requested = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Yazuki Settings")
        
        # Set Window Icon
        icon_path = os.path.join(self.config['model_folder'], 'yazuki.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.resize(400, 350)
        
        # Apply Dark Theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #aaaaaa;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #333333;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #2b2b2b;
                color: #aaaaaa;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #333333;
                color: #ffffff;
                border-bottom: 2px solid #007acc;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3d3d3d;
                height: 6px;
                background: #1e1e1e;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007acc;
                border: 1px solid #007acc;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QPushButton:pressed {
                background-color: #005c99;
            }
            QSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                padding: 4px;
                border-radius: 3px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- Tab 1: Appearance ---
        tab_appearance = QWidget()
        layout_appearance = QVBoxLayout(tab_appearance)
        
        # Scale
        group_scale = QGroupBox("Model Scale & Position")
        layout_scale = QVBoxLayout(group_scale)
        
        # Scale Slider
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(10)  # 0.1x
        self.scale_slider.setMaximum(300) # 3.0x
        initial_scale = int(config['render'].get('scale', 1.0) * 100)
        self.scale_slider.setValue(initial_scale)
        self.scale_slider.valueChanged.connect(self.on_scale_change)
        self.scale_label = QLabel(f"{initial_scale/100:.2f}x")
        self.scale_label.setFixedWidth(40)
        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_label)
        layout_scale.addLayout(scale_layout)
        
        # Offset X Slider
        offset_x_layout = QHBoxLayout()
        offset_x_layout.addWidget(QLabel("Offset X:"))
        self.offset_x_slider = QSlider(Qt.Horizontal)
        self.offset_x_slider.setMinimum(-200)
        self.offset_x_slider.setMaximum(200)
        initial_offset_x = int(config['render'].get('offset_x', 0.0) * 100)
        self.offset_x_slider.setValue(initial_offset_x)
        self.offset_x_slider.valueChanged.connect(self.on_offset_x_change)
        self.offset_x_label = QLabel(f"{initial_offset_x/100:.2f}")
        self.offset_x_label.setFixedWidth(40)
        offset_x_layout.addWidget(self.offset_x_slider)
        offset_x_layout.addWidget(self.offset_x_label)
        layout_scale.addLayout(offset_x_layout)

        # Offset Y Slider
        offset_y_layout = QHBoxLayout()
        offset_y_layout.addWidget(QLabel("Offset Y:"))
        self.offset_y_slider = QSlider(Qt.Horizontal)
        self.offset_y_slider.setMinimum(-200)
        self.offset_y_slider.setMaximum(200)
        initial_offset_y = int(config['render'].get('offset_y', 0.0) * 100)
        self.offset_y_slider.setValue(initial_offset_y)
        self.offset_y_slider.valueChanged.connect(self.on_offset_y_change)
        self.offset_y_label = QLabel(f"{initial_offset_y/100:.2f}")
        self.offset_y_label.setFixedWidth(40)
        offset_y_layout.addWidget(self.offset_y_slider)
        offset_y_layout.addWidget(self.offset_y_label)
        layout_scale.addLayout(offset_y_layout)
        
        layout_appearance.addWidget(group_scale)
        layout_appearance.addStretch()
        self.tabs.addTab(tab_appearance, "Appearance")
        
        # --- Tab 2: Behavior ---
        tab_behavior = QWidget()
        layout_behavior = QVBoxLayout(tab_behavior)
        
        group_tracking = QGroupBox("Eye Tracking")
        layout_tracking = QVBoxLayout(group_tracking)
        
        # Look at Mouse
        self.chk_look_at_mouse = QCheckBox("Look at Mouse Cursor")
        self.chk_look_at_mouse.setChecked(config['render'].get('look_at_mouse', True))
        self.chk_look_at_mouse.toggled.connect(self.look_at_mouse_toggled.emit)
        layout_tracking.addWidget(self.chk_look_at_mouse)
        
        # Sensitivity Slider
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(1)   # 0.01x
        self.sensitivity_slider.setMaximum(200) # 2.00x
        initial_sensitivity = int(config['render'].get('sensitivity', 0.35) * 100)
        self.sensitivity_slider.setValue(initial_sensitivity)
        self.sensitivity_slider.valueChanged.connect(self.on_sensitivity_change)
        self.sensitivity_label = QLabel(f"{initial_sensitivity/100:.2f}")
        self.sensitivity_label.setFixedWidth(40)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        sensitivity_layout.addWidget(self.sensitivity_label)
        layout_tracking.addLayout(sensitivity_layout)
        
        layout_behavior.addWidget(group_tracking)
        layout_behavior.addStretch()
        self.tabs.addTab(tab_behavior, "Behavior")
        
        # --- Tab 3: Window ---
        tab_window = QWidget()
        layout_window = QVBoxLayout(tab_window)
        
        group_window = QGroupBox("Window Properties")
        layout_group_window = QVBoxLayout(group_window)
        
        # Click Through
        self.chk_click_through = QCheckBox("Click-Through Mode (F8)")
        self.chk_click_through.setChecked(config['window'].get('click_through', False))
        self.chk_click_through.toggled.connect(self.click_through_toggled.emit)
        layout_group_window.addWidget(self.chk_click_through)
        
        # Always on Top
        self.chk_always_on_top = QCheckBox("Always on Top")
        self.chk_always_on_top.setChecked(config['window'].get('always_on_top', True))
        self.chk_always_on_top.toggled.connect(self.always_on_top_toggled.emit)
        layout_group_window.addWidget(self.chk_always_on_top)
        
        layout_window.addWidget(group_window)
        
        group_size = QGroupBox("Dimensions")
        layout_size = QVBoxLayout(group_size)
        
        # Resize Mode
        self.chk_resize_mode = QCheckBox("Edit Window Size (Wireframe)")
        self.chk_resize_mode.toggled.connect(self.resize_mode_toggled.emit)
        layout_size.addWidget(self.chk_resize_mode)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(100, 4000)
        self.spin_width.setValue(config['window']['width'])
        self.spin_width.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(self.spin_width)

        size_layout.addWidget(QLabel("Height:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(100, 4000)
        self.spin_height.setValue(config['window']['height'])
        self.spin_height.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(self.spin_height)
        
        layout_size.addLayout(size_layout)
        layout_window.addWidget(group_size)
        
        layout_window.addStretch()
        self.tabs.addTab(tab_window, "Window")

        # --- Bottom Actions ---
        action_layout = QHBoxLayout()
        
        btn_reload = QPushButton("Reload Model")
        btn_reload.clicked.connect(self.reload_requested.emit)
        action_layout.addWidget(btn_reload)
        
        main_layout.addLayout(action_layout)

    def on_scale_change(self, value):
        scale = value / 100.0
        self.scale_label.setText(f"{scale:.2f}x")
        self.scale_changed.emit(scale)

    def on_offset_x_change(self, value):
        offset = value / 100.0
        self.offset_x_label.setText(f"{offset:.2f}")
        self.offset_x_changed.emit(offset)

    def on_offset_y_change(self, value):
        offset = value / 100.0
        self.offset_y_label.setText(f"{offset:.2f}")
        self.offset_y_changed.emit(offset)

    def on_sensitivity_change(self, value):
        sensitivity = value / 100.0
        self.sensitivity_label.setText(f"{sensitivity:.2f}")
        self.sensitivity_changed.emit(sensitivity)

    def on_size_changed(self):
        self.window_size_changed.emit(self.spin_width.value(), self.spin_height.value())

    def update_size_display(self, w, h):
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)
        self.spin_width.setValue(w)
        self.spin_height.setValue(h)
        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)

    def update_state(self, click_through):
        # Update UI if state changes externally (e.g. F8)
        self.chk_click_through.blockSignals(True)
        self.chk_click_through.setChecked(click_through)
        self.chk_click_through.blockSignals(False)
