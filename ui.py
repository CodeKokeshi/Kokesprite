import pygame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)


class UI:
    def __init__(self, x, y, width, height, font, icon_manager=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.icon_manager = icon_manager
        # Options bar: size/shape and pixel-perfect; tools moved to right panel
        self.tool_buttons = {}
        self.size_controls = self.setup_size_controls()

    def setup_tool_buttons(self):
        # Deprecated in this layout; tools are shown on the right panel.
        self.tool_buttons = {}

    def setup_size_controls(self):
        """Setup size control elements, anchored to current x/y/width/height."""
        controls = {}
        
        # Brush Size section (left side)
        size_start_x = self.x + 10
        size_y = self.y + 40  # Raised up a bit
        controls['minus'] = pygame.Rect(size_start_x, size_y, 25, 25)
        controls['plus'] = pygame.Rect(size_start_x + 30, size_y, 25, 25)
        controls['slider'] = pygame.Rect(size_start_x + 60, size_y + 2, 160, 20)
        controls['input'] = pygame.Rect(size_start_x + 230, size_y, 50, 25)
        
        # Brush Options section (right side)
        options_start_x = self.x + 320
        options_y = self.y + 40  # Same height as size controls
        controls['shape'] = pygame.Rect(options_start_x, options_y, 80, 25)
        controls['pixel_perfect'] = pygame.Rect(options_start_x + 90, options_y, 100, 25)
        
        return controls

    def handle_click(self, mouse_pos, tool_manager, size_input_text, previous_valid_size, pixel_perfect):
        """Handle UI clicks and return updated state"""
        # Ensure rects are current
        self.size_controls = self.setup_size_controls()
        mx, my = mouse_pos
        result = {
            'tool_changed': False,
            'size_changed': False,
            'shape_changed': False,
            'slider_dragging': False,
            'input_active': False,
            'pixel_perfect_changed': False,
            'size_input_text': size_input_text,
            'previous_valid_size': previous_valid_size,
            'pixel_perfect': pixel_perfect
        }

        # No tool buttons in options bar in this layout.

        current_tool = tool_manager.get_current_tool()

        if self.size_controls['minus'].collidepoint(mx, my):
            current_tool.increase(-1)
            tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
            result['size_changed'] = True
            result['size_input_text'] = str(current_tool.size)
            result['previous_valid_size'] = result['size_input_text']

        elif self.size_controls['plus'].collidepoint(mx, my):
            current_tool.increase(1)
            tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
            result['size_changed'] = True
            result['size_input_text'] = str(current_tool.size)
            result['previous_valid_size'] = result['size_input_text']

        elif self.size_controls['shape'].collidepoint(mx, my):
            current_tool.toggle_shape()
            tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
            result['shape_changed'] = True

        elif self.size_controls['pixel_perfect'].collidepoint(mx, my):
            result['pixel_perfect'] = not pixel_perfect
            result['pixel_perfect_changed'] = True

        elif self.size_controls['slider'].collidepoint(mx, my):
            result['slider_dragging'] = True
            relative_x = mx - self.size_controls['slider'].x
            slider_w = self.size_controls['slider'].width - 10
            new_size = max(1, min(256, int(relative_x / max(1, slider_w) * 255) + 1))
            current_tool.set_size(new_size)
            tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
            result['size_changed'] = True
            result['size_input_text'] = str(current_tool.size)
            result['previous_valid_size'] = result['size_input_text']

        elif self.size_controls['input'].collidepoint(mx, my):
            result['input_active'] = True

        return result

    def handle_slider_drag(self, mouse_pos, tool_manager):
        """Handle slider dragging"""
        self.size_controls = self.setup_size_controls()
        mx, my = mouse_pos
        relative_x = mx - self.size_controls['slider'].x
        slider_w = self.size_controls['slider'].width - 10
        new_size = max(1, min(256, int(relative_x / max(1, slider_w) * 255) + 1))
        current_tool = tool_manager.get_current_tool()
        current_tool.set_size(new_size)
        tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
        return str(current_tool.size)

    def render(self, screen, tool_manager, size_input_text, size_input_active, pixel_perfect):
        """Render the options bar"""
        self.size_controls = self.setup_size_controls()
        # Background
        ui_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (240, 240, 240), ui_rect)
        pygame.draw.rect(screen, BLACK, ui_rect, 1)

        # Section labels
        size_label = self.font.render("Brush Size", True, BLACK)
        screen.blit(size_label, (self.x + 10, self.y + 10))
        
        options_label = self.font.render("Brush Options", True, BLACK)
        screen.blit(options_label, (self.x + 320, self.y + 10))

        # Size controls
        current_tool = tool_manager.get_current_tool()
        size_controls_info = [
            ('minus', self.size_controls['minus'], "minus"),
            ('plus', self.size_controls['plus'], "plus"),
        ]
        for name, rect, icon_name in size_controls_info:
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
            if self.icon_manager:
                self.icon_manager.render_icon(screen, icon_name, rect.centerx, rect.centery, center=True)
            else:
                # Fallback to text
                text_fallback = "-" if icon_name == "minus" else "+"
                text = self.font.render(text_fallback, True, BLACK)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

        # Option controls
        shape_icon = "square" if current_tool.shape == "square" else "circle"
        option_controls_info = [
            ('shape', self.size_controls['shape'], shape_icon),
            ('pixel_perfect', self.size_controls['pixel_perfect'], None),  # No icon for pixel perfect yet
        ]
        for name, rect, icon_name in option_controls_info:
            color = (200, 255, 200) if name == 'pixel_perfect' and pixel_perfect else WHITE
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
            
            if icon_name and self.icon_manager:
                # Render shape icon
                self.icon_manager.render_icon(screen, icon_name, rect.centerx, rect.centery, center=True)
            else:
                # Fallback to text for pixel perfect or if no icon manager
                if name == 'pixel_perfect':
                    text_content = "PIXEL"
                else:
                    text_content = "SQR" if current_tool.shape == "square" else "CIR"
                text = self.font.render(text_content, True, BLACK)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

        # Size slider
        slider_rect = self.size_controls['slider']
        pygame.draw.rect(screen, WHITE, slider_rect)
        pygame.draw.rect(screen, BLACK, slider_rect, 1)
        handle_x = slider_rect.x + int((current_tool.size - 1) / 255 * (slider_rect.width - 10))
        handle_rect = pygame.Rect(handle_x, slider_rect.y - 2, 10, 24)
        pygame.draw.rect(screen, (50, 50, 50), handle_rect)

        # Size input field
        input_rect = self.size_controls['input']
        input_color = (255, 255, 200) if size_input_active else WHITE
        pygame.draw.rect(screen, input_color, input_rect)
        pygame.draw.rect(screen, BLACK, input_rect, 1)
        display_text = size_input_text if size_input_text else "..."
        text_color = BLACK if size_input_text else GRAY
        input_text_surface = self.font.render(display_text, True, text_color)
        screen.blit(input_text_surface, (input_rect.x + 5, input_rect.y + 3))
