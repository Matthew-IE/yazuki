import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton, QGroupBox, QSpinBox, QTabWidget, QFrame, QLineEdit, QComboBox, QColorDialog, QFileDialog, QPlainTextEdit) # type: ignore
from PySide6.QtCore import Qt, Signal # type: ignore
from PySide6.QtGui import QIcon, QColor, QKeySequence, QKeyEvent # type: ignore
from app.ai_manager import AIManager

class SettingsWindow(QWidget):
    scale_changed = Signal(float)
    offset_x_changed = Signal(float)
    offset_y_changed = Signal(float)
    click_through_toggled = Signal(bool)
    always_on_top_toggled = Signal(bool)
    look_at_mouse_toggled = Signal(bool)
    random_look_toggled = Signal(bool)
    random_interval_changed = Signal(float)
    random_radius_changed = Signal(float)
    sensitivity_changed = Signal(float)
    resize_mode_toggled = Signal(bool)
    window_size_changed = Signal(int, int)
    reload_requested = Signal()
    save_requested = Signal()
    quit_requested = Signal()
    ai_settings_changed = Signal()
    chat_settings_changed = Signal(dict)
    input_key_changed = Signal(int)
    clear_memory_requested = Signal()
    memory_enabled_toggled = Signal(bool)
    ai_enabled_toggled = Signal(bool)
    tts_settings_changed = Signal()
    mouth_sensitivity_changed = Signal(float)
    system_prompt_changed = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.waiting_for_key = False
        self.setWindowTitle("Yazuki Settings")
        
        # Set Window Icon
        # Check media folder first, then model folder
        icon_path = os.path.join('resources', 'media', 'yazuki.png')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.config['model_folder'], 'yazuki.png')

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.resize(500, 600)
        
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
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                padding: 4px;
                border-radius: 3px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: #ffffff;
                selection-background-color: #007acc;
                font-size: 14px;
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
        
        # Model Selection
        group_model = QGroupBox("Live2D Model")
        layout_model = QVBoxLayout(group_model)
        
        self.txt_model_path = QLineEdit()
        self.txt_model_path.setReadOnly(True)
        self.txt_model_path.setText(config.get('model_folder', 'resources/model/yazuki'))
        layout_model.addWidget(self.txt_model_path)
        
        model_btn_layout = QHBoxLayout()
        btn_browse_model = QPushButton("Browse Folder...")
        btn_browse_model.clicked.connect(self.browse_model_folder)
        model_btn_layout.addWidget(btn_browse_model)
        
        btn_reset_model = QPushButton("Use Yazuki Model")
        btn_reset_model.clicked.connect(self.reset_model_to_default)
        model_btn_layout.addWidget(btn_reset_model)
        
        layout_model.addLayout(model_btn_layout)
        layout_appearance.addWidget(group_model)

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
        self.chk_look_at_mouse.toggled.connect(self.on_look_at_mouse_toggled)
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

        # Random Look (Only enabled if Look at Mouse is OFF)
        self.chk_random_look = QCheckBox("Randomly Look Around")
        self.chk_random_look.setChecked(config['render'].get('random_look', False))
        # self.chk_random_look.setEnabled(not self.chk_look_at_mouse.isChecked()) # Removed to allow mutual toggle
        self.chk_random_look.toggled.connect(self.on_random_look_toggled)
        layout_tracking.addWidget(self.chk_random_look)

        # Random Interval Slider
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Look Interval (s):"))
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setMinimum(5)   # 0.5s
        self.interval_slider.setMaximum(100) # 10.0s
        initial_interval = int(config['render'].get('random_interval', 2.0) * 10)
        self.interval_slider.setValue(initial_interval)
        self.interval_slider.setEnabled(self.chk_random_look.isChecked())
        self.interval_slider.valueChanged.connect(self.on_interval_change)
        self.interval_label = QLabel(f"{initial_interval/10.0:.1f}s")
        self.interval_label.setFixedWidth(40)
        interval_layout.addWidget(self.interval_slider)
        interval_layout.addWidget(self.interval_label)
        layout_tracking.addLayout(interval_layout)

        # Random Radius Slider
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("Look Radius:"))
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setMinimum(5)   # 0.05 (5%)
        self.radius_slider.setMaximum(100) # 1.00 (100%)
        initial_radius = int(config['render'].get('random_radius', 0.2) * 100)
        self.radius_slider.setValue(initial_radius)
        self.radius_slider.setEnabled(self.chk_random_look.isChecked())
        self.radius_slider.valueChanged.connect(self.on_radius_change)
        self.radius_label = QLabel(f"{initial_radius}%")
        self.radius_label.setFixedWidth(40)
        radius_layout.addWidget(self.radius_slider)
        radius_layout.addWidget(self.radius_label)
        layout_tracking.addLayout(radius_layout)
        
        layout_behavior.addWidget(group_tracking)

        # Lip Sync Group
        group_lipsync = QGroupBox("Lip Sync")
        layout_lipsync = QVBoxLayout(group_lipsync)

        # Mouth Sensitivity Slider
        mouth_sens_layout = QHBoxLayout()
        mouth_sens_layout.addWidget(QLabel("Mouth Sensitivity:"))
        self.mouth_sens_slider = QSlider(Qt.Horizontal)
        self.mouth_sens_slider.setMinimum(10)   # 1.0x
        self.mouth_sens_slider.setMaximum(200)  # 20.0x
        initial_mouth_sens = int(config['render'].get('mouth_sensitivity', 5.0) * 10)
        self.mouth_sens_slider.setValue(initial_mouth_sens)
        self.mouth_sens_slider.valueChanged.connect(self.on_mouth_sens_change)
        self.mouth_sens_label = QLabel(f"{initial_mouth_sens/10.0:.1f}")
        self.mouth_sens_label.setFixedWidth(40)
        mouth_sens_layout.addWidget(self.mouth_sens_slider)
        mouth_sens_layout.addWidget(self.mouth_sens_label)
        layout_lipsync.addLayout(mouth_sens_layout)

        layout_behavior.addWidget(group_lipsync)
        
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

        # --- Tab 4: Input ---
        tab_input = QWidget()
        layout_input = QVBoxLayout(tab_input)
        
        group_input = QGroupBox("Audio Input")
        layout_group_input = QVBoxLayout(group_input)
        
        layout_group_input.addWidget(QLabel("Microphone Device:"))
        self.combo_input_device = QComboBox()
        self.combo_input_device.addItem("Default", -1)
        
        # Populate devices
        self.ai_manager = AIManager(config) # Temp instance to list devices
        devices = self.ai_manager.get_input_devices()
        for idx, name in devices:
            self.combo_input_device.addItem(name, idx)
            
        # Set current selection
        current_device = config.get('ai', {}).get('input_device', -1)
        index = self.combo_input_device.findData(current_device)
        if index >= 0:
            self.combo_input_device.setCurrentIndex(index)
            
        self.combo_input_device.currentIndexChanged.connect(self.on_input_device_changed)
        layout_group_input.addWidget(self.combo_input_device)
        
        layout_input.addWidget(group_input)

        group_keybind = QGroupBox("Voice Input Keybind")
        layout_keybind = QVBoxLayout(group_keybind)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Current Key:"))
        
        self.btn_keybind = QPushButton()
        current_key_name = config.get('ai', {}).get('input_key_name', 'V')
        self.btn_keybind.setText(current_key_name)
        self.btn_keybind.clicked.connect(self.start_key_recording)
        key_layout.addWidget(self.btn_keybind)
        
        layout_keybind.addLayout(key_layout)
        layout_keybind.addWidget(QLabel("Click the button and press a key to change."))
        
        layout_input.addWidget(group_keybind)
        
        layout_input.addStretch()
        self.tabs.addTab(tab_input, "Input")

        # --- Tab 5: AI ---
        tab_ai = QWidget()
        layout_ai = QVBoxLayout(tab_ai)
        
        # Global AI Toggle
        self.chk_ai_enabled = QCheckBox("Enable AI Features")
        self.chk_ai_enabled.setChecked(config.get('ai', {}).get('enabled', False))
        self.chk_ai_enabled.toggled.connect(self.on_ai_enabled_toggled)
        layout_ai.addWidget(self.chk_ai_enabled)

        # Provider Selection
        group_provider = QGroupBox("AI Provider")
        layout_provider = QVBoxLayout(group_provider)
        
        layout_provider.addWidget(QLabel("Select Provider:"))
        self.combo_provider = QComboBox()
        self.combo_provider.addItem("OpenAI", "openai")
        self.combo_provider.addItem("Ollama", "ollama")
        
        current_provider = config.get('ai', {}).get('provider', 'openai')
        index = self.combo_provider.findData(current_provider)
        if index >= 0:
            self.combo_provider.setCurrentIndex(index)
        self.combo_provider.currentIndexChanged.connect(self.on_provider_changed)
        layout_provider.addWidget(self.combo_provider)
        
        layout_ai.addWidget(group_provider)

        # OpenAI Config
        self.group_ai_config = QGroupBox("OpenAI Configuration")
        layout_group_ai = QVBoxLayout(self.group_ai_config)
        
        layout_group_ai.addWidget(QLabel("API Key:"))
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        self.txt_api_key.setText(config.get('ai', {}).get('api_key', ''))
        self.txt_api_key.textChanged.connect(self.on_api_key_changed)
        layout_group_ai.addWidget(self.txt_api_key)

        layout_group_ai.addWidget(QLabel("Model:"))
        self.txt_openai_model = QLineEdit()
        self.txt_openai_model.setText(config.get('ai', {}).get('openai_model', 'gpt-5-nano'))
        self.txt_openai_model.textChanged.connect(self.on_openai_model_changed)
        layout_group_ai.addWidget(self.txt_openai_model)
        
        layout_ai.addWidget(self.group_ai_config)

        # Ollama Config
        self.group_ollama_config = QGroupBox("Ollama Configuration")
        layout_group_ollama = QVBoxLayout(self.group_ollama_config)
        
        layout_group_ollama.addWidget(QLabel("Endpoint:"))
        self.txt_ollama_endpoint = QLineEdit()
        self.txt_ollama_endpoint.setText(config.get('ai', {}).get('ollama_endpoint', 'http://localhost:11434/api/chat'))
        self.txt_ollama_endpoint.textChanged.connect(self.on_ollama_endpoint_changed)
        layout_group_ollama.addWidget(self.txt_ollama_endpoint)
        
        layout_group_ollama.addWidget(QLabel("Model:"))
        self.txt_ollama_model = QLineEdit()
        self.txt_ollama_model.setText(config.get('ai', {}).get('ollama_model', 'llama3'))
        self.txt_ollama_model.textChanged.connect(self.on_ollama_model_changed)
        layout_group_ollama.addWidget(self.txt_ollama_model)
        
        layout_ai.addWidget(self.group_ollama_config)

        # Memory Control
        self.group_memory = QGroupBox("Memory")
        layout_memory = QVBoxLayout(self.group_memory)
        
        self.chk_memory_enabled = QCheckBox("Enable Conversation Memory")
        self.chk_memory_enabled.setChecked(config.get('ai', {}).get('memory_enabled', True))
        self.chk_memory_enabled.toggled.connect(self.on_memory_toggled)
        layout_memory.addWidget(self.chk_memory_enabled)
        
        btn_clear_memory = QPushButton("Clear Conversation Memory")
        btn_clear_memory.clicked.connect(self.clear_memory_requested.emit)
        layout_memory.addWidget(btn_clear_memory)
        
        layout_ai.addWidget(self.group_memory)

        # Personality (System Prompt)
        self.group_personality = QGroupBox("Personality (System Prompt)")
        layout_personality = QVBoxLayout(self.group_personality)
        
        self.txt_system_prompt = QPlainTextEdit()
        self.txt_system_prompt.setPlaceholderText("Enter the system prompt here...")
        default_prompt = "You are a helpful desktop companion named Yazuki. Keep your responses concise (under 20 words if possible) and friendly. Do not use markdown formatting."
        self.txt_system_prompt.setPlainText(config.get('ai', {}).get('system_prompt', default_prompt))
        self.txt_system_prompt.setMaximumHeight(100)
        self.txt_system_prompt.textChanged.connect(self.on_system_prompt_changed)
        
        layout_personality.addWidget(self.txt_system_prompt)
        
        btn_load_personality = QPushButton("Load from File (.txt, .json)")
        btn_load_personality.clicked.connect(self.load_personality_from_file)
        layout_personality.addWidget(btn_load_personality)
        
        layout_ai.addWidget(self.group_personality)
        
        # Apply initial state
        self.update_ai_ui_state(self.chk_ai_enabled.isChecked())
        
        layout_ai.addStretch()
        self.tabs.addTab(tab_ai, "AI")

        # --- Tab 6: Chat ---
        tab_chat = QWidget()
        self.init_chat_tab(tab_chat)
        self.tabs.addTab(tab_chat, "Chat")

        # --- Tab 7: TTS ---
        tab_tts = QWidget()
        layout_tts = QVBoxLayout(tab_tts)
        
        # Enable TTS
        self.chk_tts_enabled = QCheckBox("Enable TTS")
        self.chk_tts_enabled.setChecked(config.get('typecast', {}).get('enabled', False))
        self.chk_tts_enabled.toggled.connect(self.on_tts_enabled_toggled)
        layout_tts.addWidget(self.chk_tts_enabled)

        # TTS Provider Selection
        group_tts_provider = QGroupBox("TTS Provider")
        layout_tts_provider = QVBoxLayout(group_tts_provider)
        
        layout_tts_provider.addWidget(QLabel("Select Provider:"))
        self.combo_tts_provider = QComboBox()
        self.combo_tts_provider.addItem("Typecast.ai", "typecast")
        self.combo_tts_provider.addItem("GPT-SoVITS (Local)", "gpt_sovits")
        
        current_tts_provider = config.get('tts', {}).get('provider', 'typecast')
        index = self.combo_tts_provider.findData(current_tts_provider)
        if index >= 0:
            self.combo_tts_provider.setCurrentIndex(index)
        self.combo_tts_provider.currentIndexChanged.connect(self.on_tts_provider_changed)
        layout_tts_provider.addWidget(self.combo_tts_provider)
        
        layout_tts.addWidget(group_tts_provider)
        self.group_tts_provider = group_tts_provider
        
        # Typecast Config
        self.group_typecast_config = QGroupBox("Typecast Configuration")
        layout_group_typecast = QVBoxLayout(self.group_typecast_config)
        
        layout_group_typecast.addWidget(QLabel("API Key:"))
        self.txt_tts_api_key = QLineEdit()
        self.txt_tts_api_key.setEchoMode(QLineEdit.Password)
        self.txt_tts_api_key.setText(config.get('typecast', {}).get('api_key', ''))
        self.txt_tts_api_key.textChanged.connect(self.on_tts_api_key_changed)
        layout_group_typecast.addWidget(self.txt_tts_api_key)
        
        layout_group_typecast.addWidget(QLabel("Voice ID:"))
        self.txt_tts_voice_id = QLineEdit()
        self.txt_tts_voice_id.setText(config.get('typecast', {}).get('voice_id', ''))
        self.txt_tts_voice_id.textChanged.connect(self.on_tts_voice_id_changed)
        layout_group_typecast.addWidget(self.txt_tts_voice_id)
        
        layout_tts.addWidget(self.group_typecast_config)

        # GPT-SoVITS Config
        self.group_sovits_config = QGroupBox("GPT-SoVITS Configuration")
        layout_group_sovits = QVBoxLayout(self.group_sovits_config)
        
        # Inference Version Toggle
        self.chk_sovits_inference = QCheckBox("Use Inference Version (API v2)")
        self.chk_sovits_inference.setChecked(config.get('gpt_sovits', {}).get('is_inference_version', False))
        self.chk_sovits_inference.toggled.connect(self.on_sovits_inference_toggled)
        layout_group_sovits.addWidget(self.chk_sovits_inference)

        layout_group_sovits.addWidget(QLabel("API Endpoint:"))
        self.txt_sovits_endpoint = QLineEdit()
        self.txt_sovits_endpoint.setText(config.get('gpt_sovits', {}).get('endpoint', 'http://127.0.0.1:9880'))
        self.txt_sovits_endpoint.textChanged.connect(self.on_sovits_endpoint_changed)
        layout_group_sovits.addWidget(self.txt_sovits_endpoint)
        
        layout_group_sovits.addWidget(QLabel("Reference Audio Path:"))
        ref_audio_layout = QHBoxLayout()
        self.txt_sovits_ref_audio = QLineEdit()
        self.txt_sovits_ref_audio.setText(config.get('gpt_sovits', {}).get('ref_audio_path', ''))
        self.txt_sovits_ref_audio.textChanged.connect(self.on_sovits_ref_audio_changed)
        ref_audio_layout.addWidget(self.txt_sovits_ref_audio)
        
        btn_browse_ref = QPushButton("Browse...")
        btn_browse_ref.clicked.connect(self.browse_ref_audio)
        ref_audio_layout.addWidget(btn_browse_ref)
        
        layout_group_sovits.addLayout(ref_audio_layout)

        layout_group_sovits.addWidget(QLabel("Prompt Text:"))
        self.txt_sovits_prompt_text = QLineEdit()
        self.txt_sovits_prompt_text.setText(config.get('gpt_sovits', {}).get('prompt_text', ''))
        self.txt_sovits_prompt_text.textChanged.connect(self.on_sovits_prompt_text_changed)
        layout_group_sovits.addWidget(self.txt_sovits_prompt_text)

        layout_group_sovits.addWidget(QLabel("Prompt Language:"))
        self.txt_sovits_prompt_lang = QLineEdit()
        self.txt_sovits_prompt_lang.setText(config.get('gpt_sovits', {}).get('prompt_lang', 'en'))
        self.txt_sovits_prompt_lang.textChanged.connect(self.on_sovits_prompt_lang_changed)
        layout_group_sovits.addWidget(self.txt_sovits_prompt_lang)

        layout_group_sovits.addWidget(QLabel("Target Language:"))
        self.txt_sovits_text_lang = QLineEdit()
        self.txt_sovits_text_lang.setText(config.get('gpt_sovits', {}).get('text_lang', 'en'))
        self.txt_sovits_text_lang.textChanged.connect(self.on_sovits_text_lang_changed)
        layout_group_sovits.addWidget(self.txt_sovits_text_lang)
        
        layout_tts.addWidget(self.group_sovits_config)
        
        self.update_tts_ui_state(self.chk_tts_enabled.isChecked())
        
        layout_tts.addStretch()
        self.tabs.addTab(tab_tts, "TTS")

        # --- Bottom Actions ---
        action_layout = QHBoxLayout()
        
        btn_reload = QPushButton("Reload Model")
        btn_reload.clicked.connect(self.reload_requested.emit)
        action_layout.addWidget(btn_reload)
        
        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(self.save_requested.emit)
        action_layout.addWidget(btn_save)
        
        btn_quit = QPushButton("Quit Application")
        btn_quit.setStyleSheet("background-color: #d32f2f; color: white;") # Red color for quit
        btn_quit.clicked.connect(self.quit_requested.emit)
        action_layout.addWidget(btn_quit)
        
        main_layout.addLayout(action_layout)

    def on_look_at_mouse_toggled(self, checked):
        self.look_at_mouse_toggled.emit(checked)
        if checked:
            self.chk_random_look.setChecked(False)

    def on_random_look_toggled(self, checked):
        self.random_look_toggled.emit(checked)
        self.interval_slider.setEnabled(checked)
        self.radius_slider.setEnabled(checked)
        if checked:
            self.chk_look_at_mouse.setChecked(False)

    def on_interval_change(self, value):
        float_val = value / 10.0
        self.interval_label.setText(f"{float_val:.1f}s")
        self.config['render']['random_interval'] = float_val
        self.random_interval_changed.emit(float_val)

    def on_radius_change(self, value):
        float_val = value / 100.0
        self.radius_label.setText(f"{value}%")
        self.config['render']['random_radius'] = float_val
        self.random_radius_changed.emit(float_val)

    def on_tts_enabled_toggled(self, checked):
        self.config.setdefault('typecast', {})['enabled'] = checked
        self.update_tts_ui_state(checked)
        self.tts_settings_changed.emit()

    def on_tts_provider_changed(self, index):
        provider = self.combo_tts_provider.currentData()
        self.config.setdefault('tts', {})['provider'] = provider
        self.update_tts_ui_state(self.chk_tts_enabled.isChecked())
        self.tts_settings_changed.emit()

    def on_tts_api_key_changed(self, text):
        self.config.setdefault('typecast', {})['api_key'] = text
        self.tts_settings_changed.emit()

    def on_tts_voice_id_changed(self, text):
        self.config.setdefault('typecast', {})['voice_id'] = text
        self.tts_settings_changed.emit()

    def on_sovits_endpoint_changed(self, text):
        self.config.setdefault('gpt_sovits', {})['endpoint'] = text
        self.tts_settings_changed.emit()

    def on_sovits_ref_audio_changed(self, text):
        self.config.setdefault('gpt_sovits', {})['ref_audio_path'] = text
        self.tts_settings_changed.emit()

    def browse_ref_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Reference Audio", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.txt_sovits_ref_audio.setText(file_path)

    def on_sovits_prompt_text_changed(self, text):
        self.config.setdefault('gpt_sovits', {})['prompt_text'] = text
        self.tts_settings_changed.emit()

    def on_sovits_inference_toggled(self, checked):
        self.config.setdefault('gpt_sovits', {})['is_inference_version'] = checked
        self.tts_settings_changed.emit()

    def on_sovits_prompt_lang_changed(self, text):
        self.config.setdefault('gpt_sovits', {})['prompt_lang'] = text
        self.tts_settings_changed.emit()

    def on_sovits_text_lang_changed(self, text):
        self.config.setdefault('gpt_sovits', {})['text_lang'] = text
        self.tts_settings_changed.emit()

    def update_tts_ui_state(self, enabled):
        self.group_tts_provider.setEnabled(enabled)
        
        provider = self.combo_tts_provider.currentData()
        is_typecast = (provider == 'typecast')
        is_sovits = (provider == 'gpt_sovits')
        
        self.group_typecast_config.setVisible(enabled and is_typecast)
        self.group_sovits_config.setVisible(enabled and is_sovits)

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

    def on_input_device_changed(self, index):
        device_id = self.combo_input_device.currentData()
        self.config.setdefault('ai', {})['input_device'] = device_id
        self.ai_settings_changed.emit()

    def on_api_key_changed(self, text):
        self.config.setdefault('ai', {})['api_key'] = text
        self.ai_settings_changed.emit()

    def on_mouth_sens_change(self, value):
        sens = value / 10.0
        self.mouth_sens_label.setText(f"{sens:.1f}")
        self.config['render']['mouth_sensitivity'] = sens
        self.mouth_sensitivity_changed.emit(sens)

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

    def init_chat_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        chat_config = self.config.get('chat', {})
        
        # Font Size
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(chat_config.get('font_size', 16))
        self.font_size_spin.valueChanged.connect(self.emit_chat_settings)
        size_layout.addWidget(self.font_size_spin)
        font_layout.addLayout(size_layout)
        
        # Text Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.text_color_btn = QPushButton()
        self.text_color = chat_config.get('text_color', '#FFFFFF')
        self.text_color_btn.setStyleSheet(f"background-color: {self.text_color}; border: 1px solid #555;")
        self.text_color_btn.clicked.connect(self.pick_text_color)
        color_layout.addWidget(self.text_color_btn)
        font_layout.addLayout(color_layout)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Background
        bg_group = QGroupBox("Background")
        bg_layout = QVBoxLayout()
        
        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel("Color:"))
        self.bg_color_btn = QPushButton()
        self.bg_color = chat_config.get('bg_color', '#000000')
        self.bg_color_btn.setStyleSheet(f"background-color: {self.bg_color}; border: 1px solid #555;")
        self.bg_color_btn.clicked.connect(self.pick_bg_color)
        bg_color_layout.addWidget(self.bg_color_btn)
        bg_layout.addLayout(bg_color_layout)
        
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.bg_opacity_slider = QSlider(Qt.Horizontal)
        self.bg_opacity_slider.setRange(0, 255)
        self.bg_opacity_slider.setValue(chat_config.get('bg_opacity', 180))
        self.bg_opacity_slider.valueChanged.connect(self.emit_chat_settings)
        opacity_layout.addWidget(self.bg_opacity_slider)
        bg_layout.addLayout(opacity_layout)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        
        # Position
        pos_group = QGroupBox("Position Offset")
        pos_layout = QVBoxLayout()
        
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self.offset_x_spin = QSpinBox()
        self.offset_x_spin.setRange(-500, 500)
        self.offset_x_spin.setValue(chat_config.get('offset_x', 0))
        self.offset_x_spin.valueChanged.connect(self.emit_chat_settings)
        x_layout.addWidget(self.offset_x_spin)
        pos_layout.addLayout(x_layout)
        
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.offset_y_spin = QSpinBox()
        self.offset_y_spin.setRange(-500, 500)
        self.offset_y_spin.setValue(chat_config.get('offset_y', 0))
        self.offset_y_spin.valueChanged.connect(self.emit_chat_settings)
        y_layout.addWidget(self.offset_y_spin)
        pos_layout.addLayout(y_layout)
        
        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group)
        
        layout.addStretch()

    def pick_text_color(self):
        color = QColorDialog.getColor(QColor(self.text_color), self, "Select Text Color")
        if color.isValid():
            self.text_color = color.name()
            self.text_color_btn.setStyleSheet(f"background-color: {self.text_color}; border: 1px solid #555;")
            self.emit_chat_settings()

    def start_key_recording(self):
        self.waiting_for_key = True
        self.btn_keybind.setText("Press any key...")
        self.btn_keybind.setStyleSheet("background-color: #ff9800; color: black;")
        self.grabKeyboard() # Grab keyboard input

    def keyPressEvent(self, event: QKeyEvent):
        if self.waiting_for_key:
            key = event.key()
            native_key = event.nativeVirtualKey()
            
            # Ignore modifier keys alone
            if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
                return
                
            key_name = QKeySequence(key).toString()
            
            # Update Config
            ai_config = self.config.setdefault('ai', {})
            ai_config['input_key_vk'] = native_key
            ai_config['input_key_name'] = key_name
            
            # Update UI
            self.btn_keybind.setText(key_name)
            self.btn_keybind.setStyleSheet("") # Reset style
            
            self.waiting_for_key = False
            self.releaseKeyboard()
            
            self.input_key_changed.emit(native_key)
        else:
            super().keyPressEvent(event)

    def on_memory_toggled(self, checked):
        self.config.setdefault('ai', {})['memory_enabled'] = checked
        self.memory_enabled_toggled.emit(checked)

    def on_ai_enabled_toggled(self, checked):
        self.config.setdefault('ai', {})['enabled'] = checked
        self.update_ai_ui_state(checked)
        self.ai_enabled_toggled.emit(checked)

    def on_provider_changed(self, index):
        provider = self.combo_provider.currentData()
        self.config.setdefault('ai', {})['provider'] = provider
        self.update_ai_ui_state(self.chk_ai_enabled.isChecked())
        self.ai_settings_changed.emit()

    def on_openai_model_changed(self, text):
        self.config.setdefault('ai', {})['openai_model'] = text
        self.ai_settings_changed.emit()

    def on_ollama_endpoint_changed(self, text):
        self.config.setdefault('ai', {})['ollama_endpoint'] = text
        self.ai_settings_changed.emit()

    def on_ollama_model_changed(self, text):
        self.config.setdefault('ai', {})['ollama_model'] = text
        self.ai_settings_changed.emit()

    def load_personality_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Personality", "", "Text/JSON Files (*.txt *.json);;All Files (*.*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.lower().endswith('.json'):
                        data = json.load(f)
                        # Try to find common keys
                        if isinstance(data, dict):
                            # Check for TavernAI/SillyTavern style cards
                            if 'data' in data and 'description' in data['data']:
                                # V2 card
                                prompt = data['data']['description']
                                if 'scenario' in data['data']:
                                    prompt += "\n\nScenario: " + data['data']['scenario']
                                if 'first_mes' in data['data']:
                                    prompt += "\n\nFirst Message: " + data['data']['first_mes']
                                self.txt_system_prompt.setPlainText(prompt)
                                return
                            
                            # Check for simple keys
                            for key in ['system_prompt', 'personality', 'description', 'char_persona', 'prompt']:
                                if key in data:
                                    self.txt_system_prompt.setPlainText(str(data[key]))
                                    return
                            
                            # If no known keys, dump the whole thing
                            self.txt_system_prompt.setPlainText(json.dumps(data, indent=2))
                        else:
                            self.txt_system_prompt.setPlainText(str(data))
                    else:
                        # Text file
                        self.txt_system_prompt.setPlainText(f.read())
            except Exception as e:
                print(f"Error loading personality file: {e}")

    def on_system_prompt_changed(self):
        text = self.txt_system_prompt.toPlainText()
        self.config.setdefault('ai', {})['system_prompt'] = text
        self.system_prompt_changed.emit(text)

    def update_ai_ui_state(self, enabled):
        # Always enable configuration groups so they can be edited
        self.combo_provider.setEnabled(True)
        
        provider = self.combo_provider.currentData()
        is_openai = (provider == 'openai')
        is_ollama = (provider == 'ollama')
        
        self.group_ai_config.setVisible(is_openai)
        self.group_ollama_config.setVisible(is_ollama)
        self.group_memory.setEnabled(True)
        self.group_personality.setEnabled(True)

    def update_tts_ui_state(self, enabled):
        # Always enable configuration groups so they can be edited
        self.combo_tts_provider.setEnabled(True)
        
        provider = self.combo_tts_provider.currentData()
        is_typecast = (provider == 'typecast')
        is_sovits = (provider == 'gpt_sovits')
        
        self.group_typecast_config.setVisible(is_typecast)
        self.group_sovits_config.setVisible(is_sovits)

    def browse_model_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Live2D Model Folder")
        if folder_path:
            # Try to make relative path if inside current directory
            try:
                rel_path = os.path.relpath(folder_path, os.getcwd())
                if not rel_path.startswith(".."):
                    folder_path = rel_path
            except ValueError:
                pass # Different drive or error
            
            # Normalize separators to forward slash
            folder_path = folder_path.replace("\\", "/")

            # Update config
            self.config['model_folder'] = folder_path
            self.txt_model_path.setText(folder_path)
            # Trigger reload
            self.reload_requested.emit()

    def reset_model_to_default(self):
        default_path = "resources/model/yazuki"
        self.config['model_folder'] = default_path
        self.txt_model_path.setText(default_path)
        self.reload_requested.emit()

    def pick_bg_color(self):
        color = QColorDialog.getColor(QColor(self.bg_color), self, "Select Background Color")
        if color.isValid():
            self.bg_color = color.name()
            self.bg_color_btn.setStyleSheet(f"background-color: {self.bg_color}; border: 1px solid #555;")
            self.emit_chat_settings()

    def emit_chat_settings(self):
        settings = {
            'font_size': self.font_size_spin.value(),
            'text_color': self.text_color,
            'bg_color': self.bg_color,
            'bg_opacity': self.bg_opacity_slider.value(),
            'offset_x': self.offset_x_spin.value(),
            'offset_y': self.offset_y_spin.value()
        }
        self.chat_settings_changed.emit(settings)
