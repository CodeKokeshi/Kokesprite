import pygame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

class UI:
    def __init__(self, x, y, width, height, font):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        
        # Tool selection area
        self.tool_buttons = {}
        self.setup_tool_buttons()
        
        # Size controls
        self.size_controls = self.setup_size_controls()
    
    def setup_tool_buttons(self):
        """Setup tool selection buttons"""
        button_width = 50
        button_height = 25
        spacing = 5
        start_x = self.x + 5
        start_y = self.y + 5
        
        tools = ["brush", "eraser", "fill"]
        for i, tool in enumerate(tools):
            self.tool_buttons[tool] = pygame.Rect(
                start_x + i * (button_width + spacing),
                start_y,
                button_width,
                button_height
            )
    
    def setup_size_controls(self):
        """Setup size control elements"""
        controls = {}
        
        # Row 2: Size controls
        row2_y = self.y + 35
        
        controls['minus'] = pygame.Rect(self.x + 5, row2_y, 25, 25)
        controls['plus'] = pygame.Rect(self.x + 35, row2_y, 25, 25)
        controls['shape'] = pygame.Rect(self.x + 70, row2_y, 80, 25)
        
        # Pixel Perfect toggle
        controls['pixel_perfect'] = pygame.Rect(self.x + 160, row2_y, 100, 25)
        
        # Size slider
        controls['slider'] = pygame.Rect(self.x + 5, row2_y + 30, 200, 20)
        controls['input'] = pygame.Rect(self.x + 220, row2_y + 28, 60, 24)
        
        return controls
    
    def handle_click(self, mouse_pos, tool_manager, size_input_text, previous_valid_size, pixel_perfect):
        """Handle UI clicks and return updated state"""
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
        
        # Check tool buttons
        for tool_name, rect in self.tool_buttons.items():
            if rect.collidepoint(mx, my):
                tool_manager.set_tool(tool_name)
                result['tool_changed'] = True
                break
        
        # Check size controls
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
            
        elif (self.size_controls['slider'].collidepoint(mx, my)):
            result['slider_dragging'] = True
            # Calculate new size based on click position
            relative_x = mx - self.size_controls['slider'].x
            new_size = max(1, min(256, int(relative_x / 190 * 255) + 1))
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
        mx, my = mouse_pos
        relative_x = mx - self.size_controls['slider'].x
        new_size = max(1, min(256, int(relative_x / 190 * 255) + 1))
        current_tool = tool_manager.get_current_tool()
        current_tool.set_size(new_size)
        tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
        return str(current_tool.size)
    
    def render(self, screen, tool_manager, size_input_text, size_input_active, pixel_perfect):
        """Render the UI"""
        # Background
        ui_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (240, 240, 240), ui_rect)
        pygame.draw.rect(screen, BLACK, ui_rect, 1)
        
        # Tool buttons
        current_tool_name = tool_manager.current_tool_name
        for tool_name, rect in self.tool_buttons.items():
            # Highlight current tool
            color = (200, 200, 255) if tool_name == current_tool_name else WHITE
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
            
            text = self.font.render(tool_name.capitalize(), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
        
        # Size controls
        current_tool = tool_manager.get_current_tool()
        
        # [-] [+] [Shape] [Pixel Perfect] buttons
        controls_info = [
            ('minus', self.size_controls['minus'], "-"),
            ('plus', self.size_controls['plus'], "+"),
            ('shape', self.size_controls['shape'], current_tool.shape.capitalize()),
            ('pixel_perfect', self.size_controls['pixel_perfect'], "Pixel Perfect")
        ]
        
        for name, rect, text_content in controls_info:
            if name == 'pixel_perfect':
                color = (200, 255, 200) if pixel_perfect else WHITE
            else:
                color = WHITE
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
            
            text = self.font.render(text_content, True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
        
        # Size slider
        slider_rect = self.size_controls['slider']
        pygame.draw.rect(screen, WHITE, slider_rect)
        pygame.draw.rect(screen, BLACK, slider_rect, 1)
        
        # Slider handle
        handle_x = slider_rect.x + int((current_tool.size - 1) / 255 * 190)
        handle_rect = pygame.Rect(handle_x, slider_rect.y - 2, 10, 24)
        pygame.draw.rect(screen, (50, 50, 50), handle_rect)
        
        # Size input field
        input_rect = self.size_controls['input']
        input_color = (255, 255, 200) if size_input_active else WHITE
        pygame.draw.rect(screen, input_color, input_rect)
        pygame.draw.rect(screen, BLACK, input_rect, 1)
        
        # Size label and input text
        size_label = self.font.render("Size:", True, BLACK)
        screen.blit(size_label, (input_rect.x - 40, input_rect.y + 3))
        
        display_text = size_input_text if size_input_text else "..."
        text_color = BLACK if size_input_text else GRAY
        input_text_surface = self.font.render(display_text, True, text_color)
        screen.blit(input_text_surface, (input_rect.x + 5, input_rect.y + 3))
