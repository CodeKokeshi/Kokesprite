import pygame
from abc import ABC, abstractmethod

class Tool(ABC):
    """Base class for all tools"""
    def __init__(self, name, size=1, shape="square"):
        self.name = name
        self.size = max(1, int(size))
        self.shape = shape  # "square" or "circle"

    def set_size(self, size):
        self.size = max(1, min(256, int(size)))

    def increase(self, delta=1):
        self.size = min(256, max(1, self.size + delta))

    def toggle_shape(self):
        self.shape = "circle" if self.shape == "square" else "square"

    def get_affected_pixels(self, cx, cy):
        """Get list of pixel coordinates that this tool affects"""
        pixels = []
        
        if self.shape == "square":
            half = self.size // 2
            for py in range(cy - half, cy - half + self.size):
                for px in range(cx - half, cx - half + self.size):
                    pixels.append((px, py))
        else:  # circle
            if self.size == 1:
                pixels.append((cx, cy))
            else:
                radius = self.size / 2.0
                r2 = radius * radius
                half = int(radius) + 1
                for py in range(cy - half, cy + half + 1):
                    for px in range(cx - half, cx + half + 1):
                        dx = px - cx
                        dy = py - cy
                        if dx * dx + dy * dy <= r2:
                            pixels.append((px, py))
        return pixels

    @abstractmethod
    def apply(self, canvas, mouse_x, mouse_y):
        """Apply the tool effect to the canvas"""
        pass

    @abstractmethod
    def get_preview_color(self):
        """Get the color for the tool preview"""
        pass

    def render_preview(self, screen, mouse_x, mouse_y, canvas):
        """Render tool preview at mouse position"""
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        cx, cy = coords
        
        preview_color = self.get_preview_color()
        
        pixels = self.get_affected_pixels(cx, cy)
        for px, py in pixels:
            if canvas.in_bounds(px, py):
                rect = pygame.Rect(
                    canvas.x + px * canvas.pixel_size,
                    canvas.y + py * canvas.pixel_size,
                    canvas.pixel_size,
                    canvas.pixel_size
                )
                # Create a surface for alpha blending
                preview_surface = pygame.Surface((canvas.pixel_size, canvas.pixel_size))
                preview_surface.set_alpha(100)
                preview_surface.fill(preview_color)
                screen.blit(preview_surface, rect.topleft)


class BrushTool(Tool):
    def __init__(self, size=1, shape="square"):
        super().__init__("Brush", size, shape)

    def apply(self, canvas, mouse_x, mouse_y):
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        cx, cy = coords
        
        pixels = self.get_affected_pixels(cx, cy)
        for px, py in pixels:
            canvas.set_pixel(px, py, canvas.current_color)

    def get_preview_color(self):
        return (100, 100, 100)  # Gray preview for brush


class EraserTool(Tool):
    def __init__(self, size=1, shape="square"):
        super().__init__("Eraser", size, shape)

    def apply(self, canvas, mouse_x, mouse_y):
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        cx, cy = coords
        
        pixels = self.get_affected_pixels(cx, cy)
        for px, py in pixels:
            canvas.erase_pixel(px, py)

    def get_preview_color(self):
        return (255, 100, 100)  # Red preview for eraser


class FillTool(Tool):
    def __init__(self, size=1, shape="square"):
        super().__init__("Fill", size, shape)

    def apply(self, canvas, mouse_x, mouse_y):
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        start_x, start_y = coords
        
        # Get the color at the starting position
        target_color = canvas.pixels.get((start_x, start_y), None)
        fill_color = canvas.current_color
        
        # Don't fill if the target color is the same as fill color
        if target_color == fill_color:
            return
        
        # Flood fill algorithm
        self.flood_fill(canvas, start_x, start_y, target_color, fill_color)
    
    def flood_fill(self, canvas, x, y, target_color, fill_color):
        """Flood fill algorithm using stack to avoid recursion limits"""
        stack = [(x, y)]
        filled = set()
        
        while stack:
            curr_x, curr_y = stack.pop()
            
            # Skip if out of bounds or already processed
            if not canvas.in_bounds(curr_x, curr_y) or (curr_x, curr_y) in filled:
                continue
            
            # Check if current pixel matches target color
            current_pixel_color = canvas.pixels.get((curr_x, curr_y), None)
            if current_pixel_color != target_color:
                continue
            
            # Fill the pixel
            canvas.set_pixel(curr_x, curr_y, fill_color)
            filled.add((curr_x, curr_y))
            
            # Add adjacent pixels to stack
            stack.extend([
                (curr_x + 1, curr_y),
                (curr_x - 1, curr_y),
                (curr_x, curr_y + 1),
                (curr_x, curr_y - 1)
            ])

    def get_preview_color(self):
        return (100, 255, 100)  # Green preview for fill

    def render_preview(self, screen, mouse_x, mouse_y, canvas):
        """Fill tool shows a single pixel preview at cursor"""
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        px, py = coords
        
        if canvas.in_bounds(px, py):
            rect = pygame.Rect(
                canvas.x + px * canvas.pixel_size,
                canvas.y + py * canvas.pixel_size,
                canvas.pixel_size,
                canvas.pixel_size
            )
            preview_surface = pygame.Surface((canvas.pixel_size, canvas.pixel_size))
            preview_surface.set_alpha(150)
            preview_surface.fill(self.get_preview_color())
            screen.blit(preview_surface, rect.topleft)


class LineTool(Tool):
    def __init__(self, size=1, shape="square"):
        super().__init__("Line", size, shape)
        self.start_pos = None
        self.preview_pixels = []

    def start_line(self, canvas, mouse_x, mouse_y):
        """Start drawing a line"""
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if coords:
            self.start_pos = coords
            self.preview_pixels = []

    def update_preview(self, canvas, mouse_x, mouse_y):
        """Update line preview"""
        if not self.start_pos:
            return
        
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        
        end_x, end_y = coords
        start_x, start_y = self.start_pos
        
        # Use Bresenham's line algorithm
        self.preview_pixels = self._get_line_pixels(start_x, start_y, end_x, end_y)

    def apply(self, canvas, mouse_x, mouse_y):
        """Apply the line to the canvas"""
        if not self.start_pos:
            return
        
        for px, py in self.preview_pixels:
            if canvas.in_bounds(px, py):
                canvas.set_pixel(px, py, canvas.current_color)
        
        self.start_pos = None
        self.preview_pixels = []

    def _get_line_pixels(self, x0, y0, x1, y1):
        """Bresenham's line algorithm"""
        pixels = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0
        while True:
            pixels.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return pixels

    def get_preview_color(self):
        return (0, 100, 200)  # Blue preview for line

    def render_preview(self, screen, mouse_x, mouse_y, canvas):
        """Render line preview"""
        if not self.start_pos or not self.preview_pixels:
            return
        
        preview_color = self.get_preview_color()
        for px, py in self.preview_pixels:
            if canvas.in_bounds(px, py):
                rect = pygame.Rect(
                    canvas.x + px * canvas.pixel_size,
                    canvas.y + py * canvas.pixel_size,
                    canvas.pixel_size,
                    canvas.pixel_size
                )
                preview_surface = pygame.Surface((canvas.pixel_size, canvas.pixel_size))
                preview_surface.set_alpha(150)
                preview_surface.fill(preview_color)
                screen.blit(preview_surface, rect.topleft)


class RectangleTool(Tool):
    def __init__(self, size=1, shape="square"):
        super().__init__("Rectangle", size, shape)
        self.start_pos = None
        self.preview_pixels = []
        self.fill_mode = "hollow"  # "hollow" or "fill"

    def toggle_fill_mode(self):
        """Toggle between hollow and fill mode"""
        self.fill_mode = "fill" if self.fill_mode == "hollow" else "hollow"
    
    def set_fill_mode(self, mode):
        """Set fill mode: 'hollow' or 'fill'"""
        if mode in ["hollow", "fill"]:
            self.fill_mode = mode

    def start_rectangle(self, canvas, mouse_x, mouse_y):
        """Start drawing a rectangle"""
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if coords:
            self.start_pos = coords
            self.preview_pixels = []

    def update_preview(self, canvas, mouse_x, mouse_y):
        """Update rectangle preview"""
        if not self.start_pos:
            return
        
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        
        end_x, end_y = coords
        start_x, start_y = self.start_pos
        
        self.preview_pixels = self._get_rectangle_pixels(start_x, start_y, end_x, end_y)

    def apply(self, canvas, mouse_x, mouse_y):
        """Apply the rectangle to the canvas"""
        if not self.start_pos:
            return
        
        for px, py in self.preview_pixels:
            if canvas.in_bounds(px, py):
                canvas.set_pixel(px, py, canvas.current_color)
        
        self.start_pos = None
        self.preview_pixels = []

    def _get_rectangle_pixels(self, x0, y0, x1, y1):
        """Get pixels for rectangle outline or filled"""
        pixels = []
        min_x, max_x = min(x0, x1), max(x0, x1)
        min_y, max_y = min(y0, y1), max(y0, y1)
        
        if self.filled:
            # Filled rectangle
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    pixels.append((x, y))
        else:
            # Rectangle outline
            for x in range(min_x, max_x + 1):
                pixels.append((x, min_y))  # Top edge
                pixels.append((x, max_y))  # Bottom edge
            for y in range(min_y + 1, max_y):
                pixels.append((min_x, y))  # Left edge
                pixels.append((max_x, y))  # Right edge
        
        return pixels

    def toggle_filled(self):
        """Toggle between filled and outline rectangle"""
        self.filled = not self.filled

    def get_preview_color(self):
        return (200, 100, 0)  # Orange preview for rectangle

    def render_preview(self, screen, mouse_x, mouse_y, canvas):
        """Render rectangle preview"""
        if not self.start_pos or not self.preview_pixels:
            return
        
        preview_color = self.get_preview_color()
        for px, py in self.preview_pixels:
            if canvas.in_bounds(px, py):
                rect = pygame.Rect(
                    canvas.x + px * canvas.pixel_size,
                    canvas.y + py * canvas.pixel_size,
                    canvas.pixel_size,
                    canvas.pixel_size
                )
                preview_surface = pygame.Surface((canvas.pixel_size, canvas.pixel_size))
                preview_surface.set_alpha(150)
                preview_surface.fill(preview_color)
                screen.blit(preview_surface, rect.topleft)


class EyedropperTool(Tool):
    def __init__(self, size=1, shape="square"):
        super().__init__("Eyedropper", size, shape)

    def apply(self, canvas, mouse_x, mouse_y):
        """Pick color from canvas"""
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return None
        
        px, py = coords
        if canvas.in_bounds(px, py):
            color = canvas.pixels.get((px, py), None)
            if color:
                canvas.current_color = color
                return color
        return None

    def get_preview_color(self):
        return (100, 200, 100)  # Green preview for eyedropper

    def render_preview(self, screen, mouse_x, mouse_y, canvas):
        """Render eyedropper preview - just a single pixel"""
        coords = canvas.get_pixel_coords(mouse_x, mouse_y)
        if not coords:
            return
        px, py = coords
        
        if canvas.in_bounds(px, py):
            rect = pygame.Rect(
                canvas.x + px * canvas.pixel_size,
                canvas.y + py * canvas.pixel_size,
                canvas.pixel_size,
                canvas.pixel_size
            )
            preview_surface = pygame.Surface((canvas.pixel_size, canvas.pixel_size))
            preview_surface.set_alpha(150)
            preview_surface.fill(self.get_preview_color())
            screen.blit(preview_surface, rect.topleft)


class ToolManager:
    def __init__(self):
        self.tools = {
            "brush": BrushTool(),
            "eraser": EraserTool(),
            "fill": FillTool(),
            "line": LineTool(),
            "rectangle": RectangleTool(),
            "eyedropper": EyedropperTool()
        }
        self.current_tool_name = "brush"
    
    def get_current_tool(self):
        return self.tools[self.current_tool_name]
    
    def set_tool(self, tool_name):
        if tool_name in self.tools:
            self.current_tool_name = tool_name
    
    def get_tool_names(self):
        return list(self.tools.keys())
    
    def sync_tool_properties(self, size, shape):
        """Sync size and shape across all tools"""
        for tool in self.tools.values():
            tool.set_size(size)
            tool.shape = shape
