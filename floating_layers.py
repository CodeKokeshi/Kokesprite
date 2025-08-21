import pygame
import sys

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 150, 255)

class FloatingLayersWindow:
    """A floating window for layer management"""
    
    def __init__(self, width=300, height=400, font=None):
        self.width = width
        self.height = height
        self.font = font or pygame.font.SysFont(None, 24)
        self.window = None
        self.screen = None
        self.running = False
        self.layer_manager = None
        
        # UI settings
        self.layer_height = 35
        self.button_width = 30
        self.scroll_y = 0
        self.header_height = 35
        self.margin = 5
        
    def create_window(self):
        """Create the floating window"""
        if not self.window:
            pygame.display.init()
            self.window = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Layers Panel")
            self.screen = self.window
            self.running = True
            return True
        return False
    
    def close_window(self):
        """Close the floating window"""
        if self.window:
            pygame.display.quit()
            self.window = None
            self.screen = None
            self.running = False
    
    def set_layer_manager(self, layer_manager):
        """Set the layer manager to display"""
        self.layer_manager = layer_manager
    
    def handle_events(self):
        """Handle window events"""
        if not self.running or not self.window:
            return {"action": None}
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_window()
                return {"action": "close"}
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self._handle_click(pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_scroll(event.y)
        
        return {"action": None}
    
    def _handle_click(self, mouse_pos):
        """Handle mouse clicks"""
        if not self.layer_manager:
            return {"action": None}
        
        mx, my = mouse_pos
        
        # Check buttons in header
        if my < self.header_height:
            button_spacing = self.button_width + 5
            total_buttons_width = 4 * button_spacing - 5
            start_x = self.width - total_buttons_width - self.margin
            
            for i, action in enumerate(["new_layer", "duplicate_layer", "delete_layer", "merge_down"]):
                btn_x = start_x + i * button_spacing
                if btn_x <= mx <= btn_x + self.button_width:
                    return {"action": action}
            return {"action": None}
        
        # Check layer clicks
        local_y = my - self.header_height
        layer_index = (local_y + self.scroll_y) // self.layer_height
        
        if 0 <= layer_index < len(self.layer_manager.layers):
            # Check if clicking on visibility toggle (left side)
            if mx <= 35:
                layer = self.layer_manager.layers[layer_index]
                layer.visible = not layer.visible
                return {"action": "toggle_visibility", "layer": layer_index}
            else:
                # Select layer
                self.layer_manager.set_current_layer(layer_index)
                return {"action": "select_layer", "layer": layer_index}
        
        return {"action": None}
    
    def _handle_scroll(self, scroll_y):
        """Handle scroll wheel"""
        if self.layer_manager:
            max_scroll = max(0, len(self.layer_manager.layers) * self.layer_height - (self.height - self.header_height))
            self.scroll_y = max(0, min(max_scroll, self.scroll_y - scroll_y * 20))
    
    def render(self):
        """Render the layers window"""
        if not self.running or not self.window or not self.layer_manager:
            return
        
        # Clear background
        self.screen.fill((240, 240, 240))
        
        # Header
        header_rect = pygame.Rect(0, 0, self.width, self.header_height)
        pygame.draw.rect(self.screen, (220, 220, 220), header_rect)
        pygame.draw.rect(self.screen, BLACK, header_rect, 1)
        
        # Header title
        title = self.font.render("Layers", True, BLACK)
        self.screen.blit(title, (self.margin, 8))
        
        # Header buttons
        button_spacing = self.button_width + 5
        total_buttons_width = 4 * button_spacing - 5
        start_x = self.width - total_buttons_width - self.margin
        
        buttons = [
            ("+", "New Layer"),
            ("D", "Duplicate"), 
            ("X", "Delete"),
            ("M", "Merge Down")
        ]
        
        for i, (btn_text, tooltip) in enumerate(buttons):
            btn_x = start_x + i * button_spacing
            btn_rect = pygame.Rect(btn_x, 3, self.button_width, self.header_height - 6)
            pygame.draw.rect(self.screen, WHITE, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            
            text = self.font.render(btn_text, True, BLACK)
            text_rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, text_rect)
        
        # Layers list area
        layers_rect = pygame.Rect(0, self.header_height, self.width, self.height - self.header_height)
        pygame.draw.rect(self.screen, WHITE, layers_rect)
        
        # Clip rendering to layers area
        self.screen.set_clip(layers_rect)
        
        # Render layers (in reverse order - top layer first)
        for i in range(len(self.layer_manager.layers)):
            actual_index = len(self.layer_manager.layers) - 1 - i
            layer = self.layer_manager.layers[actual_index]
            layer_y = self.header_height + i * self.layer_height - self.scroll_y
            
            # Skip layers outside visible area
            if layer_y + self.layer_height < self.header_height:
                continue
            if layer_y > self.height:
                break
            
            # Layer background
            is_current = actual_index == self.layer_manager.current_layer_index
            layer_color = (150, 180, 255) if is_current else WHITE
            layer_rect = pygame.Rect(0, layer_y, self.width, self.layer_height)
            pygame.draw.rect(self.screen, layer_color, layer_rect)
            pygame.draw.rect(self.screen, BLACK, layer_rect, 1)
            
            # Visibility toggle
            vis_rect = pygame.Rect(self.margin, layer_y + 7, 25, 20)
            vis_color = (200, 255, 200) if layer.visible else (255, 200, 200)
            pygame.draw.rect(self.screen, vis_color, vis_rect)
            pygame.draw.rect(self.screen, BLACK, vis_rect, 1)
            
            # Eye icon
            if layer.visible:
                pygame.draw.circle(self.screen, BLACK, (vis_rect.centerx, vis_rect.centery), 4)
                pygame.draw.circle(self.screen, WHITE, (vis_rect.centerx, vis_rect.centery), 2)
            else:
                # X mark for hidden
                pygame.draw.line(self.screen, BLACK, 
                               (vis_rect.left + 3, vis_rect.top + 3),
                               (vis_rect.right - 3, vis_rect.bottom - 3), 2)
                pygame.draw.line(self.screen, BLACK,
                               (vis_rect.right - 3, vis_rect.top + 3),
                               (vis_rect.left + 3, vis_rect.bottom - 3), 2)
            
            # Layer name
            name_color = WHITE if is_current else BLACK
            name_text = layer.name
            if len(name_text) > 15:  # Truncate long names
                name_text = name_text[:12] + "..."
            name_surface = self.font.render(name_text, True, name_color)
            self.screen.blit(name_surface, (40, layer_y + 8))
            
            # Opacity indicator
            opacity_text = f"{int(layer.opacity * 100)}%"
            opacity_surface = self.font.render(opacity_text, True, name_color)
            opacity_x = self.width - opacity_surface.get_width() - self.margin
            self.screen.blit(opacity_surface, (opacity_x, layer_y + 8))
        
        # Remove clipping
        self.screen.set_clip(None)
        
        # Scroll indicator if needed
        if len(self.layer_manager.layers) * self.layer_height > layers_rect.height:
            # Draw scroll bar
            scroll_track = pygame.Rect(self.width - 8, self.header_height, 6, layers_rect.height)
            pygame.draw.rect(self.screen, LIGHT_GRAY, scroll_track)
            
            # Scroll thumb
            max_scroll = max(0, len(self.layer_manager.layers) * self.layer_height - layers_rect.height)
            if max_scroll > 0:
                thumb_height = max(10, int(layers_rect.height * layers_rect.height / (len(self.layer_manager.layers) * self.layer_height)))
                thumb_y = self.header_height + int((self.scroll_y / max_scroll) * (layers_rect.height - thumb_height))
                thumb_rect = pygame.Rect(self.width - 8, thumb_y, 6, thumb_height)
                pygame.draw.rect(self.screen, GRAY, thumb_rect)
        
        # Update display
        pygame.display.flip()
