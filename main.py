import pygame
import sys
from canvas import PixelCanvas
from tools import ToolManager
from ui import UI
from palette import Palette

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1000  # Increased for palette
WINDOW_HEIGHT = 600
CANVAS_WIDTH = 400
CANVAS_HEIGHT = 400
CANVAS_X = 50
CANVAS_Y = 120  # More room for toolbar
PIXEL_SIZE = 10
TOOLBAR_Y = 10
TOOLBAR_HEIGHT = 100
PALETTE_X = 500  # To the right of canvas
PALETTE_Y = 120

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

def _apply_tool_at_pixel_cell(canvas, tool, px, py):
    """Apply current tool centered on a specific canvas pixel cell (px, py)."""
    if not canvas.in_bounds(px, py):
        return
    # Map cell coords to a screen position inside the cell so get_pixel_coords hits (px,py)
    screen_x = canvas.x + px * canvas.pixel_size + canvas.pixel_size // 2
    screen_y = canvas.y + py * canvas.pixel_size + canvas.pixel_size // 2
    tool.apply(canvas, screen_x, screen_y)

def draw_pixel_perfect_line(canvas, tool, x1, y1, x2, y2):
    """Draw a pixel perfect line using Bresenham-like algorithm for clean diagonals"""
    # Convert screen coordinates to canvas pixel coordinates
    coords1 = canvas.get_pixel_coords(x1, y1)
    coords2 = canvas.get_pixel_coords(x2, y2)
    
    if not coords1 or not coords2:
        return
    
    px1, py1 = coords1
    px2, py2 = coords2
    
    # Bresenham-like algorithm for pixel perfect diagonal lines
    dx = abs(px2 - px1)
    dy = abs(py2 - py1)
    
    x_step = 1 if px1 < px2 else -1
    y_step = 1 if py1 < py2 else -1
    
    x, y = px1, py1
    
    if dx > dy:
        # More horizontal movement
        error = dx / 2
        while x != px2:
            _apply_tool_at_pixel_cell(canvas, tool, x, y)
            error -= dy
            if error < 0:
                y += y_step
                error += dx
            x += x_step
        _apply_tool_at_pixel_cell(canvas, tool, px2, py2)  # Draw final pixel
    else:
        # More vertical movement
        error = dy / 2
        while y != py2:
            _apply_tool_at_pixel_cell(canvas, tool, x, y)
            error -= dx
            if error < 0:
                x += x_step
                error += dy
            y += y_step
        _apply_tool_at_pixel_cell(canvas, tool, px2, py2)  # Draw final pixel

def main():
    # Create the display window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Kokesprite - Pixel Art Editor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    
    # Create components
    canvas = PixelCanvas(CANVAS_WIDTH, CANVAS_HEIGHT, PIXEL_SIZE, CANVAS_X, CANVAS_Y)
    tool_manager = ToolManager()
    ui = UI(CANVAS_X, TOOLBAR_Y, CANVAS_WIDTH, TOOLBAR_HEIGHT, font)
    palette = Palette(PALETTE_X, PALETTE_Y)
    
    # Variables for drawing and UI state
    drawing = False
    last_pos = None
    slider_dragging = False
    size_input_active = False
    size_input_text = "1"
    previous_valid_size = "1"
    pixel_perfect = False

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check palette first
                    if palette.handle_click(mouse_pos):
                        canvas.current_color = palette.current_color
                        continue
                    
                    # Handle UI interactions
                    ui_result = ui.handle_click(mouse_pos, tool_manager, size_input_text, previous_valid_size, pixel_perfect)
                    
                    # Update state from UI interactions
                    size_input_text = ui_result['size_input_text']
                    previous_valid_size = ui_result['previous_valid_size']
                    slider_dragging = ui_result['slider_dragging']
                    size_input_active = ui_result['input_active']
                    pixel_perfect = ui_result['pixel_perfect']
                    
                    # If no UI interaction, start drawing
                    if not any([ui_result['tool_changed'], ui_result['size_changed'], 
                              ui_result['shape_changed'], ui_result['slider_dragging'], 
                              ui_result['input_active'], ui_result['pixel_perfect_changed']]):
                        current_tool = tool_manager.get_current_tool()
                        # For fill tool, apply only once on click; do not start drag drawing
                        if tool_manager.current_tool_name == "fill":
                            current_tool.apply(canvas, mouse_pos[0], mouse_pos[1])
                        else:
                            drawing = True
                            current_tool.apply(canvas, mouse_pos[0], mouse_pos[1])
                            last_pos = mouse_pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    drawing = False
                    slider_dragging = False
                    last_pos = None

            elif event.type == pygame.MOUSEMOTION:
                if slider_dragging:
                    size_input_text = ui.handle_slider_drag(mouse_pos, tool_manager)
                    previous_valid_size = size_input_text
                elif drawing:
                    # Interpolate between last_pos and current position
                    if last_pos is not None:
                        x1, y1 = last_pos
                        x2, y2 = mouse_pos
                        current_tool = tool_manager.get_current_tool()
                        # Safety: if tool got switched to fill while dragging, stop dragging
                        if tool_manager.current_tool_name == "fill":
                            drawing = False
                            last_pos = None
                            continue

                        if pixel_perfect:
                            # Pixel perfect mode: create clean diagonal steps
                            draw_pixel_perfect_line(canvas, current_tool, x1, y1, x2, y2)
                        else:
                            # Normal interpolated drawing
                            dx = x2 - x1
                            dy = y2 - y1
                            steps = max(abs(dx), abs(dy))
                            
                            if steps == 0:
                                current_tool.apply(canvas, x2, y2)
                            else:
                                for i in range(steps + 1):
                                    x = int(x1 + (dx * i) / steps)
                                    y = int(y1 + (dy * i) / steps)
                                    current_tool.apply(canvas, x, y)
                    last_pos = mouse_pos

            elif event.type == pygame.KEYDOWN:
                if size_input_active:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if size_input_text.strip() == "":
                            size_input_text = previous_valid_size
                        else:
                            try:
                                new_size = int(size_input_text)
                                if 1 <= new_size <= 256:
                                    current_tool = tool_manager.get_current_tool()
                                    current_tool.set_size(new_size)
                                    tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
                                    size_input_text = str(current_tool.size)
                                    previous_valid_size = size_input_text
                                else:
                                    size_input_text = previous_valid_size
                            except ValueError:
                                size_input_text = previous_valid_size
                        size_input_active = False
                    elif event.key == pygame.K_ESCAPE:
                        size_input_text = previous_valid_size
                        size_input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        size_input_text = size_input_text[:-1]
                    elif event.unicode.isdigit() and len(size_input_text) < 3:
                        size_input_text += event.unicode
                else:
                    # Tool shortcuts
                    current_tool = tool_manager.get_current_tool()
                    if event.key == pygame.K_LEFTBRACKET:  # '['
                        current_tool.increase(-1)
                        tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
                        size_input_text = str(current_tool.size)
                        previous_valid_size = size_input_text
                    elif event.key == pygame.K_RIGHTBRACKET:  # ']'
                        current_tool.increase(1)
                        tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
                        size_input_text = str(current_tool.size)
                        previous_valid_size = size_input_text
                    elif event.key == pygame.K_t:  # toggle shape
                        current_tool.toggle_shape()
                        tool_manager.sync_tool_properties(current_tool.size, current_tool.shape)
                    elif event.key == pygame.K_b:  # brush tool
                        tool_manager.set_tool("brush")
                    elif event.key == pygame.K_e:  # eraser tool
                        tool_manager.set_tool("eraser")
                    elif event.key == pygame.K_f:  # fill tool
                        tool_manager.set_tool("fill")
                    elif event.key == pygame.K_p:  # toggle pixel perfect
                        pixel_perfect = not pixel_perfect

        # Clear screen
        screen.fill(GRAY)

        # Render UI
        ui.render(screen, tool_manager, size_input_text, size_input_active, pixel_perfect)
        
        # Render canvas
        canvas.render(screen)
        
        # Render palette
        palette.render(screen)
        
        # Show current color
        color_display = pygame.Rect(PALETTE_X, PALETTE_Y - 30, 50, 25)
        pygame.draw.rect(screen, palette.current_color, color_display)
        pygame.draw.rect(screen, BLACK, color_display, 2)
        color_text = font.render("Current Color", True, BLACK)
        screen.blit(color_text, (PALETTE_X + 60, PALETTE_Y - 25))
        
        # Render tool preview if mouse is over canvas
        if (canvas.x <= mouse_pos[0] < canvas.x + canvas.width and 
            canvas.y <= mouse_pos[1] < canvas.y + canvas.height):
            current_tool = tool_manager.get_current_tool()
            current_tool.render_preview(screen, mouse_pos[0], mouse_pos[1], canvas)

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
