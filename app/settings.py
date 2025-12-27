from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton, QGroupBox) # type: ignore
from PySide6.QtCore import Qt, Signal # type: ignore

class SettingsWindow(QWidget):
    scale_changed = Signal(float)
    offset_x_changed = Signal(float)
    offset_y_changed = Signal(float)
    click_through_toggled = Signal(bool)
    always_on_top_toggled = Signal(bool)
    reload_requested = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Yazuki Settings")
        self.resize(300, 250)
        
        layout = QVBoxLayout(self)
        
        # --- Render Settings ---
        render_group = QGroupBox("Appearance")
        render_layout = QVBoxLayout(render_group)
        
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
        
        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_label)
        render_layout.addLayout(scale_layout)
        
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
        offset_x_layout.addWidget(self.offset_x_slider)
        offset_x_layout.addWidget(self.offset_x_label)
        render_layout.addLayout(offset_x_layout)

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
        offset_y_layout.addWidget(self.offset_y_slider)
        offset_y_layout.addWidget(self.offset_y_label)
        render_layout.addLayout(offset_y_layout)

        layout.addWidget(render_group)
        
        # --- Window Settings ---
        window_group = QGroupBox("Window Behavior")
        window_layout = QVBoxLayout(window_group)
        
        # Click Through
        self.chk_click_through = QCheckBox("Click-Through (F8)")
        self.chk_click_through.setChecked(config['window'].get('click_through', False))
        self.chk_click_through.toggled.connect(self.click_through_toggled.emit)
        window_layout.addWidget(self.chk_click_through)
        
        # Always on Top
        self.chk_always_on_top = QCheckBox("Always on Top")
        self.chk_always_on_top.setChecked(config['window'].get('always_on_top', True))
        self.chk_always_on_top.toggled.connect(self.always_on_top_toggled.emit)
        window_layout.addWidget(self.chk_always_on_top)
        
        layout.addWidget(window_group)
        
        # --- Actions ---
        action_layout = QHBoxLayout()
        
        btn_reload = QPushButton("Reload Model")
        btn_reload.clicked.connect(self.reload_requested.emit)
        action_layout.addWidget(btn_reload)
        
        layout.addLayout(action_layout)
        
        layout.addStretch()

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

    def update_state(self, click_through):
        # Update UI if state changes externally (e.g. F8)
        self.chk_click_through.blockSignals(True)
        self.chk_click_through.setChecked(click_through)
        self.chk_click_through.blockSignals(False)
