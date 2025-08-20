import pygame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)

class PixelCanvas:
    def __init__(self, width, height, pixel_size, x, y):
        self.canvas_width = width // pixel_size
        self.canvas_height = height // pixel_size
        self.pixel_size = pixel_size
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pixels = {}  # Dictionary to store colored pixels
        self.current_color = BLACK
    
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
        """Set a pixel to a specific color"""
        if self.in_bounds(pixel_x, pixel_y):
            self.pixels[(pixel_x, pixel_y)] = color
    
    def erase_pixel(self, pixel_x, pixel_y):
        """Erase a pixel (remove it from the canvas)"""
        if self.in_bounds(pixel_x, pixel_y):
            self.pixels.pop((pixel_x, pixel_y), None)
    
    def render(self, screen):
        """Render the canvas and all pixels"""
        # Draw canvas background
        canvas_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, WHITE, canvas_rect)
        pygame.draw.rect(screen, BLACK, canvas_rect, 2)
        
        # Draw grid
        for x in range(0, self.width + 1, self.pixel_size):
            pygame.draw.line(screen, LIGHT_GRAY, 
                           (self.x + x, self.y), 
                           (self.x + x, self.y + self.height))
        
        for y in range(0, self.height + 1, self.pixel_size):
            pygame.draw.line(screen, LIGHT_GRAY, 
                           (self.x, self.y + y), 
                           (self.x + self.width, self.y + y))
        
        # Draw pixels
        for (pixel_x, pixel_y), color in self.pixels.items():
            rect = pygame.Rect(
                self.x + pixel_x * self.pixel_size,
                self.y + pixel_y * self.pixel_size,
                self.pixel_size,
                self.pixel_size
            )
            pygame.draw.rect(screen, color, rect)
