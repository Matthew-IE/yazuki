from PySide6.QtOpenGLWidgets import QOpenGLWidget # type: ignore
from PySide6.QtCore import QTimer # type: ignore
from OpenGL.GL import * # type: ignore
from app.live2d_manager import Live2DManager

class RendererWidget(QOpenGLWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.live2d_manager = Live2DManager(self.config)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update) # Trigger paintGL
        
        fps = config['render'].get('fps', 60)
        self.timer.start(1000 // fps)

    def initializeGL(self):
        # Initialize OpenGL state
        glClearColor(0.0, 0.0, 0.0, 0.0) # Transparent background # type: ignore
        glEnable(GL_BLEND) # type: ignore
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # type: ignore
        
        # Initialize Live2D GL context
        self.live2d_manager.init_gl()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h) # type: ignore
        if self.live2d_manager:
            self.live2d_manager.resize(w, h)

    def paintGL(self):
        # Ensure we clear to transparent
        glClearColor(0.0, 0.0, 0.0, 0.0) # type: ignore
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # type: ignore
        
        if self.live2d_manager:
            self.live2d_manager.update()
            self.live2d_manager.draw()

    def reload_model(self):
        if self.live2d_manager:
            print("Reloading model...")
            self.live2d_manager.load_model()
