import os
import time
import math
from OpenGL.GL import ( # type: ignore
    glPushMatrix, glLoadIdentity, glRotatef, glBegin, glColor4f, 
    glVertex2f, glEnd, glPopMatrix, GL_QUADS, glScalef
)

# Try to import live2d. 
# This assumes the user has installed a package named 'live2d' or 'live2d-py' that exposes a 'live2d' module.
# Common bindings: https://github.com/gwj916/live2d-py
HAS_LIVE2D = False
try:
    # Try v3 first (common in newer live2d-py)
    import live2d.v3 as live2d # type: ignore
    HAS_LIVE2D = True
    print("Live2D v3 library found.")
except ImportError:
    try:
        import live2d # type: ignore
        # Check for expected functions to ensure it's the right library
        if hasattr(live2d, 'init') and hasattr(live2d, 'LAppModel'):
            HAS_LIVE2D = True
            print("Live2D library found.")
        else:
            print("Live2D module found but does not match expected API. Falling back to mock.")
    except ImportError:
        print("Live2D library not found. Falling back to mock renderer.")

class Live2DManager:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.mock_angle = 0.0
        self.model_path = config.get('model_folder', 'resources/model')
        self.has_live2d = HAS_LIVE2D
        self.width = config['window']['width']
        self.height = config['window']['height']
        self.ref_width = self.width
        self.ref_height = self.height
        self.scale = config['render'].get('scale', 1.0)
        self.offset_x = config['render'].get('offset_x', 0.0)
        self.offset_y = config['render'].get('offset_y', 0.0)
        self.look_at_mouse = config['render'].get('look_at_mouse', True)
        self.sensitivity = config['render'].get('sensitivity', 0.35)
        
    def init_gl(self):
        if self.has_live2d:
            try:
                live2d.init()
                if hasattr(live2d, 'glInit'):
                    live2d.glInit()
                
                if hasattr(live2d, 'enableLog'):
                    live2d.enableLog(True)
                elif hasattr(live2d, 'setLogEnable'):
                    live2d.setLogEnable(True)

                self.load_model()
            except Exception as e:
                print(f"Failed to initialize Live2D: {e}")
                global HAS_LIVE2D
                HAS_LIVE2D = False
                self.has_live2d = False
        
        if not self.has_live2d:
            print("Initializing Mock Renderer (Green rotating square)")

    def load_model(self):
        if not self.has_live2d:
            return

        # Find the .model3.json file
        json_file = None
        if os.path.isdir(self.model_path):
            for f in os.listdir(self.model_path):
                if f.endswith('.model3.json'):
                    json_file = os.path.join(self.model_path, f)
                    break
        elif os.path.isfile(self.model_path):
            json_file = self.model_path

        if json_file:
            print(f"Loading model: {json_file}")
            try:
                if self.model:
                    # Cleanup old model if needed (depends on library API)
                    pass
                self.model = live2d.LAppModel()
                self.model.LoadModelJson(json_file)
                
                # Set initial scale/position if API allows
                self.model.Resize(self.width, self.height)
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print(f"No .model3.json found in {self.model_path}")

    def resize(self, w, h):
        self.width = w
        self.height = h
        if self.has_live2d and self.model:
            self.model.Resize(w, h)
            # Re-apply scale logic in draw()

    def update(self, mouse_x=0.0, mouse_y=0.0):
        if self.has_live2d and self.model:
            # Update model state (time, physics, etc)
            
            if self.look_at_mouse:
                # Calculate center
                cx = self.width / 2
                cy = self.height / 2
                
                # Calculate delta from center
                dx = mouse_x - cx
                dy = mouse_y - cy
                
                # Apply sensitivity
                target_x = cx + (dx * self.sensitivity)
                target_y = cy + (dy * self.sensitivity)
                
                # Use Drag to simulate looking
                self.model.Drag(target_x, target_y)
            else:
                # Look at center (straight ahead)
                self.model.Drag(self.width / 2, self.height / 2)

            self.model.Update()
        else:
            self.mock_angle += 2.0
            if self.mock_angle > 360:
                self.mock_angle -= 360

    def draw(self):
        # Calculate compensation to keep model size constant in pixels regardless of window size
        current_min = min(self.width, self.height) if self.width > 0 and self.height > 0 else 1
        ref_min = min(self.ref_width, self.ref_height)
        
        # Compensation factor: if window grows, scale down to match reference size
        compensation = ref_min / current_min
        final_scale = self.scale * compensation

        if self.has_live2d and self.model:
            # Use LAppModel's SetScale instead of glScalef
            # Note: SetScale usually sets the scale relative to the model's base scale.
            # We might need to be careful if it accumulates, but usually it's a setter.
            # However, LAppModel might reset this in Update() or Resize()?
            # Let's try setting it every frame or just rely on it.
            # But wait, if we use SetScale, we might not need glScalef.
            
            # Actually, let's try to use glScalef again but ensure we are in the right matrix mode?
            # If model.Draw() resets matrix, glScalef is useless.
            # But LAppModel has SetScale! Let's use that.
            
            # We need to know what the "base" scale is. 
            # Assuming SetScale(1.0) is "fit to window".
            self.model.SetScale(final_scale)
            self.model.SetOffset(self.offset_x, self.offset_y)
            self.model.Draw()
        else:
            glPushMatrix()
            glScalef(final_scale, final_scale, 1.0)
            self.draw_mock()
            glPopMatrix()

    def draw_mock(self):
        # Simple rotating quad using legacy OpenGL for simplicity in prototype
        # Note: Outer glPushMatrix handled in draw()
        glPushMatrix()
        glLoadIdentity()
        
        # Convert to screen coordinates -1 to 1
        # Just draw in center
        glRotatef(self.mock_angle, 0, 0, 1)
        
        glBegin(GL_QUADS)
        glColor4f(0.0, 1.0, 0.0, 0.5) # Semi-transparent green
        glVertex2f(-0.5, -0.5)
        glVertex2f(0.5, -0.5)
        glVertex2f(0.5, 0.5)
        glVertex2f(-0.5, 0.5)
        glEnd()
        
        glPopMatrix()
