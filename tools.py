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


class ToolManager:
    def __init__(self):
        self.tools = {
            "brush": BrushTool(),
            "eraser": EraserTool(),
            "fill": FillTool()
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
