from PySide6.QtOpenGLWidgets import QOpenGLWidget # type: ignore
from PySide6.QtCore import QTimer, Qt, QRect, Signal, QPoint # type: ignore
from PySide6.QtGui import QCursor, QPainter, QPen, QColor, QFont, QFontDatabase, QFontMetrics # type: ignore
from OpenGL.GL import * # type: ignore
from app.live2d_manager import Live2DManager
import os

class RendererWidget(QOpenGLWidget):
    chat_position_changed = Signal(int, int)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.show_border = False
        self.chat_text = ""
        self.full_chat_text = ""
        self.displayed_chat_text = ""
        self.status_text = ""
        self.chat_timer = QTimer()
        self.chat_timer.setSingleShot(True)
        self.chat_timer.timeout.connect(self.clear_chat)
        
        self.typewriter_timer = QTimer()
        self.typewriter_timer.timeout.connect(self.update_typewriter)
        self.current_char_index = 0
        
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
        self.typewriter_effect = chat_config.get('typewriter_effect', True)
        self.typewriter_speed = chat_config.get('typewriter_speed', 50)

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
        
        self.chat_font = QFont(self.font_family, self.chat_font_size)
        self.status_font = QFont("Segoe UI", 12, QFont.Bold)
        
        # Dragging state
        self.is_dragging_chat = False
        self.drag_start_pos = QPoint()
        self.drag_start_offset = QPoint()
        self.edit_mode = False
        self.preview_mode = False

    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        if enabled:
            self.set_chat_text("Drag me to position!", duration=9999)
        else:
            if not self.preview_mode:
                self.clear_chat()
            else:
                self.set_chat_text("Sample Text", duration=9999)
        self.update()

    def set_preview_mode(self, enabled):
        self.preview_mode = enabled
        if enabled:
            # Only show sample text if not already editing position
            if not self.edit_mode:
                self.set_chat_text("Sample Text", duration=9999)
        else:
            if not self.edit_mode:
                self.clear_chat()
        self.update()

    def update_chat_settings(self, settings):
        self.chat_font_size = settings.get('font_size', 16)
        self.chat_text_color = QColor(settings.get('text_color', '#FFFFFF'))
        bg_color = QColor(settings.get('bg_color', '#000000'))
        bg_color.setAlpha(settings.get('bg_opacity', 180))
        self.chat_bg_color = bg_color
        self.chat_offset_x = settings.get('offset_x', 0)
        self.chat_offset_y = settings.get('offset_y', 0)
        self.chat_font = QFont(self.font_family, self.chat_font_size)
        self.typewriter_effect = settings.get('typewriter_effect', True)
        self.typewriter_speed = settings.get('typewriter_speed', 50)
        self.update()

    def set_chat_text(self, text, duration=10.0):
        self.full_chat_text = text
        self.chat_text = text # Keep for compatibility if needed, but we use displayed_chat_text
        
        # Ensure a minimum duration of 2 seconds, and add a small buffer
        # If typewriter is on, add time for typing
        typing_duration = 0
        if self.typewriter_effect:
            typing_duration = (len(text) * self.typewriter_speed) / 1000.0
            
        display_time = max(2.0, duration + typing_duration + 1.0)
        self.chat_timer.start(int(display_time * 1000)) 
        
        if self.typewriter_effect:
            self.displayed_chat_text = ""
            self.current_char_index = 0
            self.typewriter_timer.start(self.typewriter_speed)
        else:
            self.displayed_chat_text = text
            self.typewriter_timer.stop()
            
        self.update()

    def update_typewriter(self):
        if self.current_char_index < len(self.full_chat_text):
            self.current_char_index += 1
            self.displayed_chat_text = self.full_chat_text[:self.current_char_index]
            self.update()
        else:
            self.typewriter_timer.stop()

    def set_status_text(self, text):
        self.status_text = text
        self.update()

    def clear_chat(self):
        self.chat_text = ""
        self.full_chat_text = ""
        self.displayed_chat_text = ""
        self.typewriter_timer.stop()
        self.update()

    def set_lip_sync(self, value):
        if self.live2d_manager:
            self.live2d_manager.set_lip_sync(value)

    def set_expression(self, emotion):
        if self.live2d_manager:
            self.live2d_manager.set_expression(emotion)

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
        if self.displayed_chat_text or (self.typewriter_effect and self.full_chat_text):
            painter.setFont(self.chat_font)
            
            # Calculate text rect
            rect = self.rect().adjusted(20 + self.chat_offset_x, 20 + self.chat_offset_y, -20 + self.chat_offset_x, -20 + self.chat_offset_y)
            flags = Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap
            
            # Draw background bubble
            # Measure text - Use full text for stable bubble size
            text_to_measure = self.full_chat_text if self.full_chat_text else self.displayed_chat_text
            bounding_rect = painter.boundingRect(rect, flags, text_to_measure)
            bounding_rect.adjust(-10, -10, 10, 10) # Padding
            
            painter.setBrush(self.chat_bg_color) # Semi-transparent black
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bounding_rect, 10, 10)
            
            # Draw text - Use displayed text
            painter.setPen(self.chat_text_color)
            painter.drawText(rect, flags, self.displayed_chat_text)

        # Draw Status Text (Listening/Thinking)
        if self.status_text:
            painter.setFont(self.status_font)
            painter.setPen(QColor(255, 255, 0)) # Yellow
            painter.drawText(self.rect().adjusted(0, 0, -10, -10), Qt.AlignBottom | Qt.AlignRight, self.status_text)

        # Draw Edit Mode Overlay
        if self.edit_mode:
            # Draw a dashed border around the chat area to indicate it's draggable
            rect = self.rect().adjusted(20 + self.chat_offset_x, 20 + self.chat_offset_y, -20 + self.chat_offset_x, -20 + self.chat_offset_y)
            flags = Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap
            text_to_measure = self.full_chat_text if self.full_chat_text else "Drag me to position!"
            bounding_rect = painter.boundingRect(rect, flags, text_to_measure)
            bounding_rect.adjust(-10, -10, 10, 10)
            
            pen = QPen(QColor(255, 255, 0))
            pen.setStyle(Qt.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(bounding_rect)

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

    def mousePressEvent(self, event):
        if self.edit_mode and event.button() == Qt.LeftButton:
            # Check if click is inside chat bubble
            rect = self.rect().adjusted(20 + self.chat_offset_x, 20 + self.chat_offset_y, -20 + self.chat_offset_x, -20 + self.chat_offset_y)
            flags = Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap
            text_to_measure = self.full_chat_text if self.full_chat_text else "Drag me to position!"
            
            # We need a painter to measure accurately, or just approximate
            # Since we don't have a painter here, let's use QFontMetrics
            fm = QFontMetrics(self.chat_font)
            bounding_rect = fm.boundingRect(rect, flags, text_to_measure)
            bounding_rect.adjust(-10, -10, 10, 10)
            
            if bounding_rect.contains(event.pos()):
                self.is_dragging_chat = True
                self.drag_start_pos = event.pos()
                self.drag_start_offset = QPoint(self.chat_offset_x, self.chat_offset_y)
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging_chat:
            delta = event.pos() - self.drag_start_pos
            self.chat_offset_x = self.drag_start_offset.x() + delta.x()
            self.chat_offset_y = self.drag_start_offset.y() + delta.y()
            self.update()
            self.chat_position_changed.emit(self.chat_offset_x, self.chat_offset_y)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_dragging_chat:
            self.is_dragging_chat = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
