import sys
import json
import os
import socket
from PySide6.QtWidgets import QApplication, QMessageBox # type: ignore
from PySide6.QtGui import QSurfaceFormat # type: ignore
from app.window import OverlayWindow
from app.renderer import RendererWidget

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print("Config not found, using defaults.")
        return {
            "model_folder": "resources/model/live2d/yazuki",
            "window": {"width": 800, "height": 1000, "x": 100, "y": 100, "always_on_top": True, "click_through": False},
            "render": {"scale": 1.0, "fps": 60}
        }
    with open(config_path, 'r') as f:
        return json.load(f)

# Global socket to hold the lock
_lock_socket = None

def is_already_running():
    global _lock_socket
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Bind to a specific port to ensure single instance
        # Port 44242 is chosen arbitrarily for Yazuki
        _lock_socket.bind(('127.0.0.1', 44242))
        return False
    except socket.error:
        return True

def main():
    if is_already_running():
        # Show a message box if possible, or just print
        # Since we haven't created QApplication yet, we can create a temporary one or just print
        print("Yazuki is already running.")
        # We can try to show a native message box or just exit
        # Creating a QApplication just for a message box is fine
        app = QApplication(sys.argv)
        QMessageBox.warning(None, "Already Running", "Yazuki is already running!")
        return

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
    
    # Prevent app from quitting when Settings window is closed
    # (Because OverlayWindow is a Tool window and doesn't count towards the window count)
    app.setQuitOnLastWindowClosed(False)
    
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
