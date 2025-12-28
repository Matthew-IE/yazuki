# Yazuki - Live2D Desktop Companion

<p float="left">
  <img src="resources/media/yazukiscreen.png" width="49%" />
  <img src="resources/media/yazukiscreen2.png" width="49%" /> 
</p>

<video src="resources/media/yazukivid.mp4" controls title="Yazuki Demo" width="100%"></video>

A Python-based desktop companion that renders a Live2D Cubism model in a transparent, always-on-top window. It allows you to have a virtual character on your screen that you can interact with or click through while working.

## Features

- **Transparent Window**: Borderless and transparent background (only the character is visible).
- **Always-on-Top**: Stays above other windows.
- **AI Companion**: Integrated with OpenAI (Whisper & GPT) for voice interaction. Hold the hotkey to speak, and the character responds with a text bubble.
- **Interactive Eye Tracking**: The model follows your mouse cursor with adjustable sensitivity.
- **Advanced Settings UI**: A modern, dark-themed settings window to control appearance, behavior, window properties, and AI configuration in real-time.
- **Customizable Chat**: Fully personalize the chat bubble's appearance (Font, Color, Background, Position) via the Settings menu.
- **Window Resizing**: "Edit Window Size" mode displays a wireframe border and resize grip to easily adjust the container size.
- **System Tray Control**: A system tray icon allows you to control the app even when the window is in click-through mode.
- **Click-Through Toggle**: Press `F8` or use the tray menu to toggle between interacting with the model (drag to move) and clicking through it.
- **Voice Input**: Configurable push-to-talk keybind (Default: 'V').
- **Live2D Rendering**: Supports Live2D Cubism models via `live2d-py`.
- **Mock Mode**: If the Live2D library is missing, it gracefully falls back to a "Mock Mode" (rotating green square) for testing window behavior.

## Roadmap

- **Local AI Integration**: Future updates aim to support running LLMs locally (e.g., Llama, Mistral) to remove the dependency on external APIs and ensure privacy/offline capability.
- **Lip Sync**: Syncing model mouth movements with AI text-to-speech output.
- **Expression Control**: AI-driven emotional expressions based on the conversation context.

## Requirements

- Windows 10/11
- Python 3.8+
- A Live2D Cubism Model (Exported for runtime, version 3.0+)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Matthew-IE/yazuki.git
    cd yazuki
    ```

2.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Live2D Bindings**:
    This project relies on `live2d-py` for rendering.
    ```bash
    pip install live2d-py
    ```
    *Note: If `pip install live2d-py` fails or isn't available for your platform, check [live2d-py on GitHub](https://github.com/EasyLive2D/live2d-py) for build instructions or pre-built wheels.*

4.  **Add Your Model**:
    - Place your exported Live2D model folder inside `resources/model/`.
    - Update `config.json` to point to your specific model folder.
    - Example `config.json`:
      ```json
      {
          "model_folder": "resources/model/my_character_folder",
          ...
      }
      ```

## How to Run

Run the application from the project root:

```bash
python -m app.main
```

## Controls

- **System Tray Icon**: Right-click the icon in your taskbar to access the menu (Settings, Toggle Click-Through, Reload, Quit).
- **Settings Window**: Accessible from the tray menu.
  - **Appearance Tab**: Adjust model scale and X/Y offset.
  - **Behavior Tab**: Toggle "Look at Mouse" and adjust tracking sensitivity.
  - **Window Tab**: Toggle Click-Through, Always-on-Top, and enable "Edit Window Size" (Wireframe mode) to resize the window.
  - **Input Tab**: Select microphone device and configure the Voice Input Keybind.
  - **AI Tab**: Configure OpenAI API Key.
  - **Chat Tab**: Customize chat bubble font, color, and position.
- **Left Click + Drag**: Move the character (only works when Click-Through is **OFF**).
- **Hold 'V' (Default)**: Record voice input. Release to send to AI. (Keybind is customizable in Settings).
- **F8**: Toggle Click-Through Mode.
  - **OFF**: You can click and drag the character.
  - **ON**: Clicks pass through the character to windows behind it.
- **F9**: Reload the model (useful for quick iteration).
- **ESC**: Quit the application.

## Configuration

You can customize the application by editing `config.json` or using the Settings UI:

```json
{
    "model_folder": "resources/model/yazuki",
    "window": {
        "width": 800,
        "height": 1000,
        "x": 100,
        "y": 100,
        "always_on_top": true,
        "click_through": false
    },
    "render": {
        "scale": 1.0,
        "fps": 60,
        "offset_x": 0.0,
        "offset_y": 0.0,
        "sensitivity": 0.35,
        "look_at_mouse": true
    },
    "chat": {
        "font_size": 16,
        "text_color": "#FFFFFF",
        "bg_color": "#000000",
        "bg_opacity": 180,
        "offset_x": 0,
        "offset_y": 0
    },
    "ai": {
        "api_key": "YOUR_OPENAI_API_KEY",
        "input_device": -1,
        "input_key_vk": 86,
        "input_key_name": "V"
    }
}
```

## Troubleshooting

- **"Live2D library not found"**: Ensure `live2d-py` is installed in your current Python environment. The app will run in "Mock Mode" (green square) if it's missing.
- **Black/White Background**: The app requests an OpenGL context with an alpha channel. If you see a solid background, ensure your graphics drivers are up to date.
- **Model not loading**: Check the terminal output. Ensure `model_folder` in `config.json` points to the folder containing the `.model3.json` file.
