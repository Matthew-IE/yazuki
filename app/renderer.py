from PySide6.QtOpenGLWidgets import QOpenGLWidget # type: ignore
from PySide6.QtCore import QTimer, Qt, QRect # type: ignore
from PySide6.QtGui import QCursor, QPainter, QPen, QColor, QFont, QFontDatabase # type: ignore
from OpenGL.GL import * # type: ignore
from app.live2d_manager import Live2DManager
import os

class RendererWidget(QOpenGLWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.show_border = False
        self.chat_text = ""
        self.status_text = ""
        self.chat_timer = QTimer()
        self.chat_timer.setSingleShot(True)
        self.chat_timer.timeout.connect(self.clear_chat)
        
        self.live2d_manager = Live2DManager(self.config)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update) # Trigger paintGL
        
        fps = config['render'].get('fps', 60)
        self.timer.start(1000 // fps)
        
        # Chat Settings
        chat_config = config.get('chat', {})
        self.chat_font_size = chat_config.get('font_size', 16)
        self.chat_text_color = QColor(chat_config.get('text_color', '#FFFFFF'))
        self.chat_bg_color = QColor(chat_config.get('bg_color', '#000000'))
        self.chat_bg_color.setAlpha(chat_config.get('bg_opacity', 180))
        self.chat_offset_x = chat_config.get('offset_x', 0)
        self.chat_offset_y = chat_config.get('offset_y', 0)

        # Load Font
        self.font_family = "Arial" # Fallback
        font_path = os.path.join('resources', 'font', 'CHERI.TTF')
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.font_family = families[0]
                    print(f"Loaded font: {self.font_family}")

    def update_chat_settings(self, settings):
        self.chat_font_size = settings.get('font_size', 16)
        self.chat_text_color = QColor(settings.get('text_color', '#FFFFFF'))
        bg_color = QColor(settings.get('bg_color', '#000000'))
        bg_color.setAlpha(settings.get('bg_opacity', 180))
        self.chat_bg_color = bg_color
        self.chat_offset_x = settings.get('offset_x', 0)
        self.chat_offset_y = settings.get('offset_y', 0)
        self.update()

    def set_chat_text(self, text):
        self.chat_text = text
        self.chat_timer.start(10000) # Show for 10 seconds
        self.update()

    def set_status_text(self, text):
        self.status_text = text
        self.update()

    def clear_chat(self):
        self.chat_text = ""
        self.update()

    def set_lip_sync(self, value):
        if self.live2d_manager:
            self.live2d_manager.set_lip_sync(value)

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

    def paintEvent(self, event):
        # Call the default paintEvent which calls paintGL
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Chat Text
        if self.chat_text:
            painter.setFont(QFont(self.font_family, self.chat_font_size))
            
            # Calculate text rect
            rect = self.rect().adjusted(20 + self.chat_offset_x, 20 + self.chat_offset_y, -20 + self.chat_offset_x, -20 + self.chat_offset_y)
            flags = Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap
            
            # Draw background bubble
            # Measure text
            bounding_rect = painter.boundingRect(rect, flags, self.chat_text)
            bounding_rect.adjust(-10, -10, 10, 10) # Padding
            
            painter.setBrush(self.chat_bg_color) # Semi-transparent black
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bounding_rect, 10, 10)
            
            # Draw text
            painter.setPen(self.chat_text_color)
            painter.drawText(rect, flags, self.chat_text)

        # Draw Status Text (Listening/Thinking)
        if self.status_text:
            painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
            painter.setPen(QColor(255, 255, 0)) # Yellow
            painter.drawText(self.rect().adjusted(0, 0, -10, -10), Qt.AlignBottom | Qt.AlignRight, self.status_text)

        # Draw border overlay if enabled
        if self.show_border:
            # Draw green border
            pen = QPen(QColor(0, 255, 0))
            pen.setWidth(4)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            
            # Adjust rect to be inside the widget
            rect = self.rect().adjusted(2, 2, -2, -2)
            painter.drawRect(rect)
            
            # Draw crosshair or grid for better sizing reference?
            # Optional: Draw a faint grid
            pen.setColor(QColor(0, 255, 0, 50))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawLine(rect.center().x(), rect.top(), rect.center().x(), rect.bottom())
            painter.drawLine(rect.left(), rect.center().y(), rect.right(), rect.center().y())
            
        painter.end()

    def reload_model(self):
        if self.live2d_manager:
            print("Reloading model...")
            self.live2d_manager.load_model()
