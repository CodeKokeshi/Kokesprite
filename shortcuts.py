import pygame

class KeyboardShortcuts:
    """Handles and displays keyboard shortcuts"""
    
    SHORTCUTS = {
        "Tools": {
            "B": "Brush Tool",
            "E": "Eraser Tool", 
            "F": "Fill Tool",
            "L": "Line Tool",
            "R": "Rectangle Tool",
            "I": "Eyedropper Tool",
            "T": "Toggle Rectangle Fill/Hollow"
        },
        "Brush": {
            "[": "Decrease Size",
            "]": "Increase Size",
            "T": "Toggle Shape"
        },
        "Canvas": {
            "P": "Toggle Pixel Perfect",
            "G": "Toggle Grid",
            "Ctrl + Mouse Wheel": "Zoom In/Out",
            "Shift + Mouse Wheel": "Scroll Horizontal",
            "Mouse Wheel": "Scroll Vertical"
        },
        "File": {
            "Ctrl + S": "Save Project",
            "Ctrl + O": "Open Project",
            "Ctrl + E": "Export PNG",
            "Ctrl + N": "New File"
        },
        "Edit": {
            "Ctrl + Z": "Undo",
            "Ctrl + Y": "Redo",
            "Ctrl + Shift + Z": "Redo (Alt)"
        },
        "Layers": {
            "Ctrl + N": "New Layer",
            "Delete": "Delete Layer",
            "Ctrl + D": "Duplicate Layer",
            "Page Up": "Move Layer Up",
            "Page Down": "Move Layer Down"
        },
        "Symmetry": {
            "H": "Toggle Horizontal Symmetry",
            "V": "Toggle Vertical Symmetry",
            "D": "Toggle Diagonal Symmetry"
        },
        "View": {
            "F1": "Toggle Help",
            "F2": "Toggle Floating Layers Window",
            "Space": "Pan Canvas (hold)",
            "Ctrl + 0": "Zoom to Fit",
            "Ctrl + 1": "Zoom 100%",
            "F11": "Toggle Fullscreen"
        }
    }
    
    @classmethod
    def get_all_shortcuts(cls):
        """Get all shortcuts organized by category"""
        return cls.SHORTCUTS
    
    @classmethod
    def render_help_overlay(cls, screen, font, small_font=None):
        """Render keyboard shortcuts overlay"""
        if small_font is None:
            small_font = font
        
        # Semi-transparent background
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = font.render("Keyboard Shortcuts", True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 50))
        screen.blit(title, title_rect)
        
        # Instructions
        instruction = small_font.render("Press ESC or H to close", True, (200, 200, 200))
        instruction_rect = instruction.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(instruction, instruction_rect)
        
        # Shortcuts in columns
        start_y = 120
        col_width = screen.get_width() // 3
        col = 0
        y = start_y
        
        for category, shortcuts in cls.SHORTCUTS.items():
            # Category header
            header = font.render(category, True, (255, 255, 100))
            screen.blit(header, (50 + col * col_width, y))
            y += 30
            
            # Shortcuts
            for key, description in shortcuts.items():
                key_text = small_font.render(key, True, (150, 255, 150))
                desc_text = small_font.render(description, True, (255, 255, 255))
                
                screen.blit(key_text, (70 + col * col_width, y))
                screen.blit(desc_text, (170 + col * col_width, y))
                y += 25
            
            y += 20  # Space between categories
            
            # Move to next column if needed
            if y > screen.get_height() - 100:
                col += 1
                y = start_y
                if col >= 3:  # Maximum 3 columns
                    break
