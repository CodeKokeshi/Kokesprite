import pygame
import os

class IconManager:
    def __init__(self, icon_size=24):
        self.icon_size = icon_size
        self.icons = {}
        self.load_icons()
    
    def load_icons(self):
        """Load all icons from the icons directory"""
        icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
        
        icon_mappings = {
            'brush': 'pencil.png',
            'pencil': 'pencil.png',
            'eraser': 'eraser.png', 
            'fill': 'paint-bucket.png',
            'paint-bucket': 'paint-bucket.png',
            'line': 'line.png',
            'rectangle': 'rectangle.png',
            'eyedropper': 'eyedropper.png',
            'plus': 'plus.png',
            'minus': 'minus.png',
            'square': 'square.png',
            'circle': 'circle.png'
        }
        
        for icon_name, filename in icon_mappings.items():
            icon_path = os.path.join(icons_dir, filename)
            if os.path.exists(icon_path):
                try:
                    # Load and scale the icon
                    icon = pygame.image.load(icon_path)
                    icon = pygame.transform.scale(icon, (self.icon_size, self.icon_size))
                    self.icons[icon_name] = icon
                except Exception as e:
                    print(f"Failed to load icon {filename}: {e}")
                    # Create a fallback colored rectangle
                    fallback = pygame.Surface((self.icon_size, self.icon_size))
                    fallback.fill((128, 128, 128))
                    self.icons[icon_name] = fallback
            else:
                # Create a fallback colored rectangle if file doesn't exist
                fallback = pygame.Surface((self.icon_size, self.icon_size))
                fallback.fill((200, 100, 100))  # Reddish to indicate missing
                self.icons[icon_name] = fallback
    
    def get_icon(self, name):
        """Get an icon by name, returns None if not found"""
        return self.icons.get(name)
    
    def render_icon(self, screen, name, x, y, center=False):
        """Render an icon at the specified position"""
        icon = self.get_icon(name)
        if icon:
            if center:
                rect = icon.get_rect(center=(x, y))
                screen.blit(icon, rect)
            else:
                screen.blit(icon, (x, y))
