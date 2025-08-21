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
        self.current_index = 0
        self.color_size = 20
        self.cols = 4
        self.rows = (len(self.colors) + self.cols - 1) // self.cols
        self.width = self.cols * self.color_size
        self.height = self.rows * self.color_size
        # Viewport and scrolling
        self.viewport_height = self.height
        self.scroll_offset = 0

    def set_viewport_height(self, height):
        """Set the visible height for palette rendering (enables scrolling)."""
        self.viewport_height = max(self.color_size, int(height))
        # Clamp scroll position
        max_scroll = max(0, self.height - self.viewport_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

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
        # Check if within viewport
        viewport_rect = pygame.Rect(self.x - 2, self.y - 2, self.width + 4, self.viewport_height + 4)
        if not viewport_rect.collidepoint(mx, my):
            return False
        # Convert to scrolled local coordinates
        local_y = (my - self.y) + self.scroll_offset
        if local_y < 0:
            return False
        row = local_y // self.color_size
        col = (mx - self.x) // self.color_size
        if col < 0 or col >= self.cols:
            return False
        index = int(row * self.cols + col)
        if 0 <= index < len(self.colors):
            self.current_index = index
            self.current_color = self.colors[index]
            return True
        return False

    def render(self, screen):
        """Render the color palette (scrollable)."""
        # Background with viewport
        bg_rect = pygame.Rect(self.x - 2, self.y - 2, self.width + 4, self.viewport_height + 4)
        pygame.draw.rect(screen, (200, 200, 200), bg_rect)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect, 1)

        # Clip to viewport
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(self.x, self.y, self.width, self.viewport_height))

        # Determine visible rows
        start_row = max(0, self.scroll_offset // self.color_size)
        end_row = min(self.rows, (self.scroll_offset + self.viewport_height) // self.color_size + 1)

        for row in range(start_row, end_row):
            for col in range(self.cols):
                index = row * self.cols + col
                if index >= len(self.colors):
                    break
                color = self.colors[index]
                rect = pygame.Rect(
                    self.x + col * self.color_size,
                    self.y + row * self.color_size - self.scroll_offset,
                    self.color_size,
                    self.color_size
                )
                pygame.draw.rect(screen, color, rect)
                if index == self.current_index:
                    pygame.draw.rect(screen, (255, 255, 255), rect, 3)
                else:
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)

        # Restore clip
        screen.set_clip(prev_clip)

        # Optional scrollbar indicator
        max_scroll = max(0, self.height - self.viewport_height)
        if max_scroll > 0:
            track = pygame.Rect(self.x + self.width + 6, self.y, 6, self.viewport_height)
            pygame.draw.rect(screen, (220, 220, 220), track)
            thumb_h = max(10, int(self.viewport_height * self.viewport_height / self.height))
            thumb_y = self.y + int((self.scroll_offset / max_scroll) * (self.viewport_height - thumb_h))
            thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_h)
            pygame.draw.rect(screen, (150, 150, 150), thumb)

    def add_color(self, color):
        """Add a new color to the palette"""
        if color not in self.colors and len(self.colors) < 256:  # Limit to 256 colors
            self.colors.append(color)
            self.rows = (len(self.colors) + self.cols - 1) // self.cols
            self.height = self.rows * self.color_size
            # Adjust viewport clamp after adding
            self.set_viewport_height(self.viewport_height)
            # Select the newly added color
            self.current_index = len(self.colors) - 1
            self.current_color = color

    def set_current_color(self, color):
        """Set the currently selected palette color to a new value."""
        if 0 <= self.current_index < len(self.colors):
            self.colors[self.current_index] = color
            self.current_color = color

    def handle_scroll(self, dy):
        """Scroll the palette by dy steps (positive scrolls down)."""
        # Each wheel step scrolls by one swatch row
        delta = dy * self.color_size
        max_scroll = max(0, self.height - self.viewport_height)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + delta))
