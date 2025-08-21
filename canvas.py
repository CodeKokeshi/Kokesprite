import pygame
from layers import LayerManager

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
GRID_COLOR = (220, 220, 220)

class PixelCanvas:
    def __init__(self, width, height, pixel_size, x, y):
        self.canvas_width = width // pixel_size
        self.canvas_height = height // pixel_size
        self.pixel_size = pixel_size
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Layer support
        self.layer_manager = LayerManager()
        self.layer_manager.set_canvas_center(self.canvas_width, self.canvas_height)
        
        # Legacy pixel access (for compatibility)
        self.pixels = {}  # This will be dynamically updated from current layer
        self.current_color = BLACK
        
        # Display options
        self.show_grid = True
        self.background_pattern = "transparent"  # "transparent", "white", "checkerboard"

    def set_pixel_size(self, new_size):
        """Update zoom level (pixel size), adjusting render width/height."""
        self.pixel_size = max(1, int(new_size))
        self.width = self.canvas_width * self.pixel_size
        self.height = self.canvas_height * self.pixel_size
    
    def in_bounds(self, pixel_x, pixel_y):
        return 0 <= pixel_x < self.canvas_width and 0 <= pixel_y < self.canvas_height
        
    def get_pixel_coords(self, mouse_x, mouse_y):
        """Convert mouse coordinates to pixel grid coordinates"""
        if (self.x <= mouse_x < self.x + self.width and 
            self.y <= mouse_y < self.y + self.height):
            
            pixel_x = (mouse_x - self.x) // self.pixel_size
            pixel_y = (mouse_y - self.y) // self.pixel_size
            return pixel_x, pixel_y
        return None
    
    def set_pixel(self, pixel_x, pixel_y, color):
        """Set a pixel to a specific color on current layer"""
        if self.in_bounds(pixel_x, pixel_y):
            current_layer = self.layer_manager.get_current_layer()
            if current_layer:
                current_layer.set_pixel(pixel_x, pixel_y, color)
                self._update_legacy_pixels()
    
    def erase_pixel(self, pixel_x, pixel_y):
        """Erase a pixel (remove it from current layer)"""
        if self.in_bounds(pixel_x, pixel_y):
            current_layer = self.layer_manager.get_current_layer()
            if current_layer:
                current_layer.erase_pixel(pixel_x, pixel_y)
                self._update_legacy_pixels()
    
    def get_pixel(self, pixel_x, pixel_y):
        """Get pixel color at position from flattened view"""
        flattened = self.layer_manager.flatten_layers(self.canvas_width, self.canvas_height)
        return flattened.get((pixel_x, pixel_y), None)
    
    def get_pixel_color(self, pixel_x, pixel_y):
        """Get pixel color at position (alias for get_pixel)"""
        return self.get_pixel(pixel_x, pixel_y)
    
    def _update_legacy_pixels(self):
        """Update the legacy pixels dict for compatibility"""
        self.pixels = self.layer_manager.flatten_layers(self.canvas_width, self.canvas_height)
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid
        return self.show_grid
    
    def set_background_pattern(self, pattern):
        """Set background pattern: 'transparent', 'white', 'checkerboard'"""
        if pattern in ["transparent", "white", "checkerboard"]:
            self.background_pattern = pattern
    
    def render(self, screen):
        """Render the canvas and all pixels"""
        # Draw canvas background
        canvas_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        if self.background_pattern == "white":
            pygame.draw.rect(screen, WHITE, canvas_rect)
        elif self.background_pattern == "checkerboard":
            self._draw_checkerboard_background(screen, canvas_rect)
        else:  # transparent
            pygame.draw.rect(screen, WHITE, canvas_rect)
        
        pygame.draw.rect(screen, BLACK, canvas_rect, 2)
        
        # Draw grid
        if self.show_grid and self.pixel_size >= 4:  # Only show grid when zoomed in enough
            for x in range(0, self.width + 1, self.pixel_size):
                pygame.draw.line(screen, GRID_COLOR, 
                               (self.x + x, self.y), 
                               (self.x + x, self.y + self.height))
            
            for y in range(0, self.height + 1, self.pixel_size):
                pygame.draw.line(screen, GRID_COLOR, 
                               (self.x, self.y + y), 
                               (self.x + self.width, self.y + y))
        
        # Draw flattened pixels from all layers
        self._update_legacy_pixels()
        for (pixel_x, pixel_y), color in self.pixels.items():
            rect = pygame.Rect(
                self.x + pixel_x * self.pixel_size,
                self.y + pixel_y * self.pixel_size,
                self.pixel_size,
                self.pixel_size
            )
            pygame.draw.rect(screen, color, rect)

    def render_to_surface(self):
        """Render the canvas onto an offscreen surface and return it."""
        surface = pygame.Surface((self.width, self.height))
        
        # Background
        if self.background_pattern == "white":
            surface.fill(WHITE)
        elif self.background_pattern == "checkerboard":
            self._draw_checkerboard_background_to_surface(surface)
        else:  # transparent
            surface.fill(WHITE)
        
        pygame.draw.rect(surface, BLACK, pygame.Rect(0, 0, self.width, self.height), 2)

        # Grid
        if self.show_grid and self.pixel_size >= 4:
            for x in range(0, self.width + 1, self.pixel_size):
                pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, self.height))
            for y in range(0, self.height + 1, self.pixel_size):
                pygame.draw.line(surface, GRID_COLOR, (0, y), (self.width, y))

        # Pixels
        self._update_legacy_pixels()
        for (px, py), color in self.pixels.items():
            rect = pygame.Rect(px * self.pixel_size, py * self.pixel_size, self.pixel_size, self.pixel_size)
            pygame.draw.rect(surface, color, rect)
        
        return surface
    
    def _draw_checkerboard_background(self, screen, canvas_rect):
        """Draw a checkerboard pattern background"""
        checker_size = max(8, self.pixel_size * 2)
        for y in range(0, canvas_rect.height, checker_size):
            for x in range(0, canvas_rect.width, checker_size):
                if (x // checker_size + y // checker_size) % 2 == 0:
                    color = (240, 240, 240)
                else:
                    color = (200, 200, 200)
                
                rect = pygame.Rect(
                    canvas_rect.x + x,
                    canvas_rect.y + y,
                    min(checker_size, canvas_rect.width - x),
                    min(checker_size, canvas_rect.height - y)
                )
                pygame.draw.rect(screen, color, rect)
    
    def _draw_checkerboard_background_to_surface(self, surface):
        """Draw checkerboard pattern to a surface"""
        checker_size = max(8, self.pixel_size * 2)
        for y in range(0, self.height, checker_size):
            for x in range(0, self.width, checker_size):
                if (x // checker_size + y // checker_size) % 2 == 0:
                    color = (240, 240, 240)
                else:
                    color = (200, 200, 200)
                
                rect = pygame.Rect(x, y, min(checker_size, self.width - x), min(checker_size, self.height - y))
                pygame.draw.rect(surface, color, rect)
