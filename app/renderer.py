from PySide6.QtOpenGLWidgets import QOpenGLWidget # type: ignore
from PySide6.QtCore import QTimer # type: ignore
from PySide6.QtGui import QCursor # type: ignore
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
            # Pass global mouse position relative to this widget
            # We map global cursor pos to widget coordinates
            # Use QCursor.pos() to get the global mouse position reliably
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            
            # Pass pixel coordinates directly to Live2D manager
            # The Drag function likely expects screen coordinates (pixels), not normalized values.
            # If we pass normalized (-1 to 1), it interprets them as pixels near (0,0) (Top-Left).
            mx = float(cursor_pos.x())
            my = float(cursor_pos.y())
            
            self.live2d_manager.update(mx, my)
            
            self.live2d_manager.draw()

    def reload_model(self):
        if self.live2d_manager:
            print("Reloading model...")
            self.live2d_manager.load_model()
