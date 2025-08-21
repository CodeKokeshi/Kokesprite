import pygame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 150, 255)

class LayersPanel:
    """UI panel for managing layers"""
    
    def __init__(self, x, y, width, height, font):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.layer_height = 35  # Increased for better spacing
        self.button_width = 30  # Larger buttons
        self.scroll_y = 0
        self.dragging_layer = None
        self.drag_offset = 0
        self.header_height = 35  # Taller header
        self.margin = 5
    
    def update_size(self, x, y, width, height):
        """Update panel dimensions for flexibility"""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def handle_click(self, mouse_pos, layer_manager):
        """Handle mouse clicks on the layers panel"""
        mx, my = mouse_pos
        if not (self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height):
            return {"action": None}
        
        # Adjust for panel position
        local_y = my - self.y - self.header_height  # Account for header
        
        # Check buttons in header
        if my < self.y + self.header_height:
            # Dynamic button positioning based on panel width
            button_spacing = self.button_width + 5
            total_buttons_width = 4 * button_spacing - 5  # 4 buttons
            start_x = self.x + self.width - total_buttons_width - self.margin
            
            for i, action in enumerate(["new_layer", "duplicate_layer", "delete_layer", "merge_down"]):
                btn_x = start_x + i * button_spacing
                if btn_x <= mx <= btn_x + self.button_width:
                    return {"action": action}
            return {"action": None}
        
        # Check layer clicks
        layer_index = (local_y + self.scroll_y) // self.layer_height
        if 0 <= layer_index < len(layer_manager.layers):
            # Check if clicking on visibility toggle (left side)
            if mx <= self.x + 35:
                layer = layer_manager.layers[layer_index]
                layer.visible = not layer.visible
                return {"action": "toggle_visibility", "layer": layer_index}
            else:
                # Select layer
                layer_manager.set_current_layer(layer_index)
                return {"action": "select_layer", "layer": layer_index}
        
        return {"action": None}
    
    def handle_scroll(self, scroll_y):
        """Handle scroll wheel in layers panel"""
        self.scroll_y = max(0, self.scroll_y + scroll_y * 20)
    
    def render(self, screen, layer_manager):
        """Render the layers panel"""
        # Panel background
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (240, 240, 240), panel_rect)
        pygame.draw.rect(screen, BLACK, panel_rect, 2)
        
        # Header
        header_rect = pygame.Rect(self.x, self.y, self.width, self.header_height)
        pygame.draw.rect(screen, (220, 220, 220), header_rect)
        pygame.draw.rect(screen, BLACK, header_rect, 1)
        
        # Header title
        title = self.font.render("Layers", True, BLACK)
        screen.blit(title, (self.x + self.margin, self.y + 8))
        
        # Header buttons - dynamically positioned
        button_spacing = self.button_width + 5
        total_buttons_width = 4 * button_spacing - 5
        start_x = self.x + self.width - total_buttons_width - self.margin
        
        buttons = [
            ("+", "New Layer"),
            ("D", "Duplicate"), 
            ("X", "Delete"),
            ("M", "Merge Down")
        ]
        
        for i, (btn_text, tooltip) in enumerate(buttons):
            btn_x = start_x + i * button_spacing
            btn_rect = pygame.Rect(btn_x, self.y + 3, self.button_width, self.header_height - 6)
            pygame.draw.rect(screen, WHITE, btn_rect)
            pygame.draw.rect(screen, BLACK, btn_rect, 1)
            
            text = self.font.render(btn_text, True, BLACK)
            text_rect = text.get_rect(center=btn_rect.center)
            screen.blit(text, text_rect)
        
        # Layers list area
        layers_rect = pygame.Rect(self.x, self.y + self.header_height, self.width, self.height - self.header_height)
        pygame.draw.rect(screen, WHITE, layers_rect)
        
        # Clip rendering to layers area
        screen.set_clip(layers_rect)
        
        # Calculate visible area
        visible_start = max(0, self.scroll_y // self.layer_height)
        visible_end = min(len(layer_manager.layers), 
                         (self.scroll_y + layers_rect.height) // self.layer_height + 1)
        
        # Render layers (in reverse order - top layer first)
        for i in range(len(layer_manager.layers)):
            actual_index = len(layer_manager.layers) - 1 - i
            layer = layer_manager.layers[actual_index]
            layer_y = self.y + self.header_height + i * self.layer_height - self.scroll_y
            
            # Skip layers outside visible area
            if layer_y + self.layer_height < self.y + self.header_height:
                continue
            if layer_y > self.y + self.height:
                break
            
            # Layer background
            is_current = actual_index == layer_manager.current_layer_index
            layer_color = (150, 180, 255) if is_current else WHITE
            layer_rect = pygame.Rect(self.x, layer_y, self.width, self.layer_height)
            pygame.draw.rect(screen, layer_color, layer_rect)
            pygame.draw.rect(screen, BLACK, layer_rect, 1)
            
            # Visibility toggle
            vis_rect = pygame.Rect(self.x + self.margin, layer_y + 7, 25, 20)
            vis_color = (200, 255, 200) if layer.visible else (255, 200, 200)
            pygame.draw.rect(screen, vis_color, vis_rect)
            pygame.draw.rect(screen, BLACK, vis_rect, 1)
            
            # Eye icon
            if layer.visible:
                pygame.draw.circle(screen, BLACK, (vis_rect.centerx, vis_rect.centery), 4)
                pygame.draw.circle(screen, WHITE, (vis_rect.centerx, vis_rect.centery), 2)
            else:
                # X mark for hidden
                pygame.draw.line(screen, BLACK, 
                               (vis_rect.left + 3, vis_rect.top + 3),
                               (vis_rect.right - 3, vis_rect.bottom - 3), 2)
                pygame.draw.line(screen, BLACK,
                               (vis_rect.right - 3, vis_rect.top + 3),
                               (vis_rect.left + 3, vis_rect.bottom - 3), 2)
            
            # Layer name - fit to available space
            name_color = WHITE if is_current else BLACK
            name_text = layer.name
            if len(name_text) > 12:  # Truncate long names
                name_text = name_text[:9] + "..."
            name_surface = self.font.render(name_text, True, name_color)
            screen.blit(name_surface, (self.x + 40, layer_y + 8))
            
            # Opacity indicator - positioned based on panel width
            opacity_text = f"{int(layer.opacity * 100)}%"
            opacity_surface = self.font.render(opacity_text, True, name_color)
            opacity_x = self.x + self.width - opacity_surface.get_width() - self.margin
            screen.blit(opacity_surface, (opacity_x, layer_y + 8))
        
        # Remove clipping
        screen.set_clip(None)
        
        # Scroll indicator if needed
        if len(layer_manager.layers) * self.layer_height > layers_rect.height:
            # Draw scroll bar
            scroll_track = pygame.Rect(self.x + self.width - 8, self.y + self.header_height, 
                                     6, layers_rect.height)
            pygame.draw.rect(screen, LIGHT_GRAY, scroll_track)
            
            # Scroll thumb
            max_scroll = max(0, len(layer_manager.layers) * self.layer_height - layers_rect.height)
            if max_scroll > 0:
                thumb_height = max(10, int(layers_rect.height * layers_rect.height / (len(layer_manager.layers) * self.layer_height)))
                thumb_y = self.y + self.header_height + int((self.scroll_y / max_scroll) * (layers_rect.height - thumb_height))
                thumb_rect = pygame.Rect(self.x + self.width - 8, thumb_y, 6, thumb_height)
                pygame.draw.rect(screen, GRAY, thumb_rect)


class StatusBar:
    """Bottom status bar showing current tool, canvas info, etc."""
    
    def __init__(self, x, y, width, height, font):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
    
    def render(self, screen, tool_manager, canvas, symmetry_manager=None, layer_manager=None):
        """Render the status bar"""
        # Background
        bar_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (250, 250, 250), bar_rect)
        pygame.draw.rect(screen, BLACK, bar_rect, 1)
        
        # Status items
        items = []
        
        # Current tool
        current_tool = tool_manager.get_current_tool()
        items.append(f"Tool: {current_tool.name}")
        items.append(f"Size: {current_tool.size}")
        items.append(f"Shape: {current_tool.shape}")
        
        # Canvas info
        items.append(f"Canvas: {canvas.canvas_width}×{canvas.canvas_height}")
        items.append(f"Zoom: {canvas.pixel_size}x")
        
        # Layer info
        if layer_manager:
            current_layer = layer_manager.get_current_layer()
            if current_layer:
                items.append(f"Layer: {current_layer.name}")
        
        # Symmetry info
        if symmetry_manager and symmetry_manager.is_any_symmetry_active():
            items.append(symmetry_manager.get_status_text())
        
        # Render items
        x_offset = self.x + 10
        for item in items:
            text = self.font.render(item, True, BLACK)
            screen.blit(text, (x_offset, self.y + 5))
            x_offset += text.get_width() + 20
            
            if x_offset > self.x + self.width - 100:  # Don't overflow
                break
