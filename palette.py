import pygame

# Predefined color palettes
DEFAULT_PALETTE = [
    (0, 0, 0),        # Black
    (255, 255, 255),  # White
    (255, 0, 0),      # Red
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (255, 255, 0),    # Yellow
    (255, 0, 255),    # Magenta
    (0, 255, 255),    # Cyan
    (128, 128, 128),  # Gray
    (255, 128, 0),    # Orange
    (128, 0, 255),    # Purple
    (0, 128, 0),      # Dark Green
    (128, 0, 0),      # Dark Red
    (0, 0, 128),      # Dark Blue
    (255, 192, 203),  # Pink
    (165, 42, 42),    # Brown
]

class Palette:
    def __init__(self, x, y, colors=None):
        self.x = x
        self.y = y
        self.colors = colors or DEFAULT_PALETTE.copy()
        self.current_color = self.colors[0]  # Black by default
        self.color_size = 20
        self.cols = 4
        self.rows = (len(self.colors) + self.cols - 1) // self.cols
        self.width = self.cols * self.color_size
        self.height = self.rows * self.color_size
        
    def get_color_rect(self, index):
        """Get the rectangle for a color at given index"""
        if index >= len(self.colors):
            return None
        row = index // self.cols
        col = index % self.cols
        return pygame.Rect(
            self.x + col * self.color_size,
            self.y + row * self.color_size,
            self.color_size,
            self.color_size
        )
    
    def handle_click(self, mouse_pos):
        """Handle mouse click on palette, return True if color was selected"""
        mx, my = mouse_pos
        for i, color in enumerate(self.colors):
            rect = self.get_color_rect(i)
            if rect and rect.collidepoint(mx, my):
                self.current_color = color
                return True
        return False
    
    def render(self, screen):
        """Render the color palette"""
        # Background
        bg_rect = pygame.Rect(self.x - 2, self.y - 2, self.width + 4, self.height + 4)
        pygame.draw.rect(screen, (200, 200, 200), bg_rect)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect, 1)
        
        # Color swatches
        for i, color in enumerate(self.colors):
            rect = self.get_color_rect(i)
            if rect:
                pygame.draw.rect(screen, color, rect)
                
                # Highlight current color
                if color == self.current_color:
                    pygame.draw.rect(screen, (255, 255, 255), rect, 3)
                else:
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)
    
    def add_color(self, color):
        """Add a new color to the palette"""
        if color not in self.colors and len(self.colors) < 32:  # Limit to 32 colors
            self.colors.append(color)
            self.rows = (len(self.colors) + self.cols - 1) // self.cols
            self.height = self.rows * self.color_size
