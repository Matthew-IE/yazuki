import sys
import json
import os
from PySide6.QtWidgets import QApplication, QMessageBox # type: ignore
from PySide6.QtGui import QSurfaceFormat # type: ignore
from app.window import OverlayWindow
from app.renderer import RendererWidget

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print("Config not found, using defaults.")
        return {
            "model_folder": "resources/model",
            "window": {"width": 800, "height": 1000, "x": 100, "y": 100, "always_on_top": True, "click_through": False},
            "render": {"scale": 1.0, "fps": 60}
        }
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    # Set up environment for high DPI
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # Set OpenGL Surface Format for transparency
    format = QSurfaceFormat()
    format.setAlphaBufferSize(8)
    format.setDepthBufferSize(24)
    format.setStencilBufferSize(8)
    format.setSamples(4) # Multisampling for smoother edges
    QSurfaceFormat.setDefaultFormat(format)

    app = QApplication(sys.argv)
    
    config = load_config()
    
    # Create Renderer
    renderer = RendererWidget(config)
    
    if not renderer.live2d_manager.has_live2d:
        QMessageBox.warning(None, "Live2D Library Missing", 
            "The 'live2d' Python library was not found.\n"
            "The application will run in Mock Mode (rotating green square).\n\n"
            "Please install 'live2d-py' or check the README for instructions.")

    # Create Window
    window = OverlayWindow(config, renderer)
    window.show()
    
    print("App started.")
    print("F8: Toggle Click-Through")
    print("F9: Reload Model")
    print("ESC: Quit")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
