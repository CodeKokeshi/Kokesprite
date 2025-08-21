import pygame
import sys
from canvas import PixelCanvas
from tools import ToolManager
from ui import UI
from palette import Palette
from icons import IconManager
from undo import UndoRedoManager, DrawCommand, FillCommand
from file_manager import FileManager
from symmetry import SymmetryManager
from panels import LayersPanel, StatusBar
from shortcuts import KeyboardShortcuts
from floating_layers import FloatingLayersWindow
try:
    # Optional: use a system file dialog for selecting PNGs on the Home screen
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    from tkinter import colorchooser
except Exception:
    tk = None
    filedialog = None
    colorchooser = None

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1000  # Base window size
WINDOW_HEIGHT = 600
PIXEL_SIZE = 10
TOOLBAR_Y = 10
TOOLBAR_HEIGHT = 100
LEFT_PALETTE_W = 120
RIGHT_TOOLS_W = 120
TOP_OPTIONS_H = 100

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

def draw_pixel_perfect_line(canvas, tool, x1, y1, x2, y2, changes_dict=None):
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
            if changes_dict is not None:
                # Apply brush size effect for line
                pixels = tool.get_affected_pixels(x, y)
                for px, py in pixels:
                    if canvas.in_bounds(px, py):
                        apply_tool_with_undo_tracking_at_pixel(canvas, tool, px, py, changes_dict)
            else:
                pixels = tool.get_affected_pixels(x, y)
                for px, py in pixels:
                    if canvas.in_bounds(px, py):
                        _apply_tool_at_pixel_cell(canvas, tool, px, py)
            error -= dy
            if error < 0:
                y += y_step
                error += dx
            x += x_step
        # Draw final pixel
        if changes_dict is not None:
            pixels = tool.get_affected_pixels(px2, py2)
            for px, py in pixels:
                if canvas.in_bounds(px, py):
                    apply_tool_with_undo_tracking_at_pixel(canvas, tool, px, py, changes_dict)
        else:
            pixels = tool.get_affected_pixels(px2, py2)
            for px, py in pixels:
                if canvas.in_bounds(px, py):
                    _apply_tool_at_pixel_cell(canvas, tool, px, py)
    else:
        # More vertical movement
        error = dy / 2
        while y != py2:
            if changes_dict is not None:
                pixels = tool.get_affected_pixels(x, y)
                for px, py in pixels:
                    if canvas.in_bounds(px, py):
                        apply_tool_with_undo_tracking_at_pixel(canvas, tool, px, py, changes_dict)
            else:
                pixels = tool.get_affected_pixels(x, y)
                for px, py in pixels:
                    if canvas.in_bounds(px, py):
                        _apply_tool_at_pixel_cell(canvas, tool, px, py)
            error -= dx
            if error < 0:
                x += x_step
                error += dy
            y += y_step
        # Draw final pixel
        if changes_dict is not None:
            pixels = tool.get_affected_pixels(px2, py2)
            for px, py in pixels:
                if canvas.in_bounds(px, py):
                    apply_tool_with_undo_tracking_at_pixel(canvas, tool, px, py, changes_dict)
        else:
            pixels = tool.get_affected_pixels(px2, py2)
            for px, py in pixels:
                if canvas.in_bounds(px, py):
                    _apply_tool_at_pixel_cell(canvas, tool, px, py)



def apply_tool_with_undo_tracking(canvas, tool, mouse_x, mouse_y, changes_dict):
    """Apply tool and track changes for undo"""
    coords = canvas.get_pixel_coords(mouse_x, mouse_y)
    if not coords:
        return
    cx, cy = coords
    
    if tool.name == "Fill":
        # For fill, we need to track all affected pixels
        old_pixels = canvas.pixels.copy()
        tool.apply(canvas, mouse_x, mouse_y)
        # Record all changes
        new_pixels = canvas.pixels.copy()
        for (x, y), new_color in new_pixels.items():
            if (x, y) not in old_pixels or old_pixels[(x, y)] != new_color:
                record_pixel_change(changes_dict, canvas, x, y, new_color)
        # Also record erased pixels
        for (x, y), old_color in old_pixels.items():
            if (x, y) not in new_pixels:
                record_pixel_change(changes_dict, canvas, x, y, None)
    else:
        # For brush/eraser, track individual pixels
        pixels = tool.get_affected_pixels(cx, cy)
        for px, py in pixels:
            if canvas.in_bounds(px, py):
                if tool.name == "Brush":
                    record_pixel_change(changes_dict, canvas, px, py, canvas.current_color)
                    canvas.set_pixel(px, py, canvas.current_color)
                elif tool.name == "Eraser":
                    record_pixel_change(changes_dict, canvas, px, py, None)
                    canvas.erase_pixel(px, py)

def apply_tool_with_undo_tracking_at_pixel(canvas, tool, px, py, changes_dict):
    """Apply tool with undo tracking at pixel coordinates"""
    if not canvas.in_bounds(px, py):
        return
        
    if tool.name == "Brush":
        record_pixel_change(changes_dict, canvas, px, py, canvas.current_color)
        canvas.set_pixel(px, py, canvas.current_color)
    elif tool.name == "Eraser":
        record_pixel_change(changes_dict, canvas, px, py, None)
        canvas.erase_pixel(px, py)

def record_pixel_change(changes_dict, canvas, x, y, new_color):
    """Record a pixel change for undo purposes"""
    if (x, y) not in changes_dict:
        old_color = canvas.pixels.get((x, y), None)
        changes_dict[(x, y)] = (old_color, new_color)

def main():
    # Create the display window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Kokesprite - Pixel Art Editor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # Initialize icon manager
    icon_manager = IconManager(icon_size=20)
    
    # Initialize managers
    file_manager = FileManager()
    symmetry_manager = SymmetryManager()
    floating_layers_window = None  # Will be created when needed

    # Scene management: 'home' | 'new_file' | 'editor'
    scene = 'home'
    show_help = False  # For keyboard shortcuts overlay

    # Home scene UI
    home_title_font = pygame.font.SysFont(None, 48)
    btn_w, btn_h = 220, 48
    new_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, WINDOW_HEIGHT // 2 - 70, btn_w, btn_h)
    open_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, WINDOW_HEIGHT // 2 + 10, btn_w, btn_h)
    last_open_path = None

    # New File scene state
    nf_width_text = "128"
    nf_height_text = "128"
    nf_active = 'width'  # 'width' or 'height' or None
    field_w, field_h = 120, 36
    fields_y = WINDOW_HEIGHT // 2 - 60
    width_rect = pygame.Rect(WINDOW_WIDTH // 2 - field_w - 20, fields_y, field_w, field_h)
    height_rect = pygame.Rect(WINDOW_WIDTH // 2 + 20, fields_y, field_w, field_h)
    create_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 80, fields_y + 60, 160, 40)
    back_btn_rect = pygame.Rect(20, 20, 80, 36)

    # Editor state (initialized after creating a file)
    canvas = None
    tool_manager = None
    ui = None
    palette = None
    undo_manager = None
    layers_panel = None
    status_bar = None
    # Layout rects (computed when entering editor)
    left_rect = None
    right_rect = None
    holder_rect = None
    options_rect = None
    bottom_rect = None
    # Scroll/zoom
    scroll_x = 0
    scroll_y = 0
    h_drag = False
    v_drag = False
    h_drag_offset = 0
    v_drag_offset = 0
    sb_thickness = 12

    # Editor interaction state
    drawing = False
    last_pos = None
    slider_dragging = False
    size_input_active = False
    size_input_text = "1"
    previous_valid_size = "1"
    pixel_perfect = False
    # Tool mode state
    current_tool_mode = "normal"  # "normal", "line_preview", "rect_preview"
    preview_start_pos = None  # Starting position for line/rect preview
    
    # Undo tracking
    current_stroke_changes = {}  # Track changes during current drawing operation

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Scene-specific input handling
            if scene == 'home':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if new_btn_rect.collidepoint(mouse_pos):
                        scene = 'new_file'
                    elif open_btn_rect.collidepoint(mouse_pos):
                        # Optional PNG selection (non-functional for now)
                        if tk and filedialog:
                            try:
                                root = tk.Tk()
                                root.withdraw()
                                path = filedialog.askopenfilename(
                                    title="Open PNG",
                                    filetypes=[("PNG Images", "*.png")]
                                )
                                root.destroy()
                                if path:
                                    last_open_path = path
                            except Exception:
                                last_open_path = None
                        else:
                            last_open_path = None

            elif scene == 'new_file':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if width_rect.collidepoint(mouse_pos):
                        nf_active = 'width'
                    elif height_rect.collidepoint(mouse_pos):
                        nf_active = 'height'
                    elif create_btn_rect.collidepoint(mouse_pos):
                        # Validate and create canvas
                        try:
                            w_cells = max(1, int(nf_width_text))
                            h_cells = max(1, int(nf_height_text))
                        except ValueError:
                            w_cells, h_cells = 128, 128

                        canvas_screen_w = w_cells * PIXEL_SIZE
                        canvas_screen_h = h_cells * PIXEL_SIZE

                        canvas = PixelCanvas(canvas_screen_w, canvas_screen_h, PIXEL_SIZE, 0, 0)
                        tool_manager = ToolManager()
                        ui = UI(0, 0, WINDOW_WIDTH, TOP_OPTIONS_H, font, icon_manager)
                        palette = Palette(10, TOP_OPTIONS_H + 10)
                        undo_manager = UndoRedoManager()
                        
                        # Make layers panel more flexible - position it better
                        layers_panel = LayersPanel(10, TOP_OPTIONS_H + 250, LEFT_PALETTE_W - 20, 300, font)
                        status_bar = StatusBar(0, WINDOW_HEIGHT - 30, WINDOW_WIDTH, 30, font)
                        
                        # Update symmetry manager with canvas size
                        symmetry_manager.set_canvas_center(canvas.canvas_width, canvas.canvas_height)
                        
                        # Reset editor state
                        drawing = False
                        last_pos = None
                        slider_dragging = False
                        size_input_active = False
                        size_input_text = "1"
                        previous_valid_size = "1"
                        pixel_perfect = False
                        current_tool_mode = "normal"

                        scene = 'editor'
                    elif back_btn_rect.collidepoint(mouse_pos):
                        scene = 'home'
                        nf_active = None
                elif event.type == pygame.KEYDOWN and nf_active in ('width', 'height'):
                    target = nf_width_text if nf_active == 'width' else nf_height_text
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        # Same as clicking Create
                        try:
                            w_cells = max(1, int(nf_width_text))
                            h_cells = max(1, int(nf_height_text))
                        except ValueError:
                            w_cells, h_cells = 128, 128
                        canvas_screen_w = w_cells * PIXEL_SIZE
                        canvas_screen_h = h_cells * PIXEL_SIZE
                        canvas = PixelCanvas(canvas_screen_w, canvas_screen_h, PIXEL_SIZE, 0, 0)
                        tool_manager = ToolManager()
                        ui = UI(0, 0, WINDOW_WIDTH, TOP_OPTIONS_H, font, icon_manager)
                        palette = Palette(10, TOP_OPTIONS_H + 10)
                        undo_manager = UndoRedoManager()
                        drawing = False
                        last_pos = None
                        slider_dragging = False
                        size_input_active = False
                        size_input_text = "1"
                        previous_valid_size = "1"
                        pixel_perfect = False
                        scene = 'editor'
                    elif event.key == pygame.K_ESCAPE:
                        scene = 'home'
                        nf_active = None
                    elif event.key == pygame.K_BACKSPACE:
                        target = target[:-1]
                    elif event.unicode.isdigit() and len(target) < 4:
                        target += event.unicode
                    # Assign back
                    if nf_active == 'width':
                        nf_width_text = target
                    else:
                        nf_height_text = target

            elif scene == 'editor':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        # Check palette (left panel)
                        if palette and palette.handle_click(mouse_pos):
                            canvas.current_color = palette.current_color
                            continue

                        # Click on current color display to edit selected swatch
                        if palette:
                            color_display = pygame.Rect(left_rect.x + 10, left_rect.y + left_rect.height - 30, 50, 20)
                            if color_display.collidepoint(mouse_pos) and colorchooser:
                                try:
                                    root = tk.Tk(); root.withdraw()
                                    rgb, hexv = colorchooser.askcolor(color=palette.current_color, title="Pick Color")
                                    root.destroy()
                                    if rgb:
                                        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
                                        palette.set_current_color((r, g, b))
                                        canvas.current_color = palette.current_color
                                except Exception:
                                    pass

                        # Scrollbar dragging start
                        content_w = canvas.width
                        content_h = canvas.height
                        show_h = content_w > holder_rect.width
                        show_v = content_h > holder_rect.height
                        # Horizontal scrollbar rects
                        if show_h:
                            track_h = pygame.Rect(holder_rect.x, holder_rect.bottom - sb_thickness, holder_rect.width - (sb_thickness if show_v else 0), sb_thickness)
                            thumb_w = max(20, int(holder_rect.width * holder_rect.width / content_w))
                            max_thumb_x = track_h.width - thumb_w
                            thumb_x = track_h.x + (0 if content_w == holder_rect.width else int((scroll_x / (content_w - holder_rect.width)) * max_thumb_x))
                            thumb_h_rect = pygame.Rect(thumb_x, track_h.y, thumb_w, sb_thickness)
                            if thumb_h_rect.collidepoint(mouse_pos):
                                h_drag = True
                                h_drag_offset = mouse_pos[0] - thumb_x
                                continue
                        # Vertical scrollbar rects
                        if show_v:
                            track_v = pygame.Rect(holder_rect.right - sb_thickness, holder_rect.y, sb_thickness, holder_rect.height - (sb_thickness if show_h else 0))
                            thumb_hg = max(20, int(holder_rect.height * holder_rect.height / content_h))
                            max_thumb_y = track_v.height - thumb_hg
                            thumb_y = track_v.y + (0 if content_h == holder_rect.height else int((scroll_y / (content_h - holder_rect.height)) * max_thumb_y))
                            thumb_v_rect = pygame.Rect(track_v.x, thumb_y, sb_thickness, thumb_hg)
                            if thumb_v_rect.collidepoint(mouse_pos):
                                v_drag = True
                                v_drag_offset = mouse_pos[1] - thumb_y
                                continue

                        # Handle UI interactions
                        ui_result = ui.handle_click(mouse_pos, tool_manager, size_input_text, previous_valid_size, pixel_perfect)

                        # Update state from UI interactions
                        size_input_text = ui_result['size_input_text']
                        previous_valid_size = ui_result['previous_valid_size']
                        slider_dragging = ui_result['slider_dragging']
                        size_input_active = ui_result['input_active']
                        pixel_perfect = ui_result['pixel_perfect']

                        # Handle layers panel interactions
                        if layers_panel and canvas:
                            layer_result = layers_panel.handle_click(mouse_pos, canvas.layer_manager)
                            if layer_result["action"] == "new_layer":
                                canvas.layer_manager.add_layer()
                            elif layer_result["action"] == "duplicate_layer":
                                canvas.layer_manager.duplicate_layer()
                            elif layer_result["action"] == "delete_layer":
                                if len(canvas.layer_manager.layers) > 1:  # Keep at least one layer
                                    canvas.layer_manager.remove_layer(canvas.layer_manager.current_layer_index)
                            elif layer_result["action"] == "merge_down":
                                canvas.layer_manager.merge_down(canvas.layer_manager.current_layer_index)
                            elif layer_result["action"] in ["toggle_visibility", "select_layer"]:
                                pass  # Already handled in the panel

                        # If no UI interaction and mouse is inside holder viewport, start drawing
                        if not any([ui_result['tool_changed'], ui_result['size_changed'],
                                    ui_result['shape_changed'], ui_result['slider_dragging'],
                                    ui_result['input_active'], ui_result['pixel_perfect_changed']]):
                            if holder_rect.collidepoint(mouse_pos):
                                current_tool = tool_manager.get_current_tool()
                                
                                # Handle different tool types
                                if tool_manager.current_tool_name == "fill":
                                    current_stroke_changes = {}
                                    apply_tool_with_undo_tracking(canvas, current_tool, mouse_pos[0], mouse_pos[1], current_stroke_changes)
                                    if current_stroke_changes:
                                        command = FillCommand(canvas, current_stroke_changes.copy())
                                        undo_manager.execute_command(command)
                                elif tool_manager.current_tool_name == "eyedropper":
                                    # Pick color from canvas
                                    coords = canvas.get_pixel_coords(mouse_pos[0], mouse_pos[1])
                                    if coords:
                                        cx, cy = coords
                                        picked_color = canvas.get_pixel_color(cx, cy)
                                        if picked_color and palette:
                                            palette.set_current_color(picked_color)
                                            canvas.current_color = picked_color
                                elif tool_manager.current_tool_name == "line":
                                    # Start line preview mode
                                    current_tool_mode = "line_preview"
                                    preview_start_pos = mouse_pos
                                    drawing = True
                                elif tool_manager.current_tool_name == "rectangle":
                                    # Start rectangle preview mode
                                    current_tool_mode = "rectangle_preview"
                                    preview_start_pos = mouse_pos
                                    drawing = True
                                else:
                                    # Normal brush/eraser drawing
                                    drawing = True
                                    current_stroke_changes = {}
                                    apply_tool_with_undo_tracking(canvas, current_tool, mouse_pos[0], mouse_pos[1], current_stroke_changes)
                                    last_pos = mouse_pos

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button released
                        if drawing:
                            if current_tool_mode in ["line_preview", "rectangle_preview"]:
                                # Finalize line or rectangle
                                if preview_start_pos:
                                    current_tool = tool_manager.get_current_tool()
                                    current_stroke_changes = {}
                                    
                                    if current_tool_mode == "line_preview":
                                        # Draw line from start to current position
                                        draw_pixel_perfect_line(canvas, current_tool, 
                                                             preview_start_pos[0], preview_start_pos[1],
                                                             mouse_pos[0], mouse_pos[1], current_stroke_changes)
                                    elif current_tool_mode == "rectangle_preview":
                                        # Draw rectangle from start to current position
                                        coords1 = canvas.get_pixel_coords(preview_start_pos[0], preview_start_pos[1])
                                        coords2 = canvas.get_pixel_coords(mouse_pos[0], mouse_pos[1])
                                        if coords1 and coords2:
                                            x1, y1 = coords1
                                            x2, y2 = coords2
                                            # Ensure proper ordering
                                            left = min(x1, x2)
                                            right = max(x1, x2)
                                            top = min(y1, y2)
                                            bottom = max(y1, y2)
                                            
                                            # Get brush size for thickness
                                            brush_size = current_tool.size
                                            
                                            if hasattr(current_tool, 'fill_mode') and current_tool.fill_mode == "fill":
                                                # Fill the entire rectangle
                                                for y in range(top, bottom + 1):
                                                    for x in range(left, right + 1):
                                                        # Apply brush size effect
                                                        pixels = current_tool.get_affected_pixels(x, y)
                                                        for px, py in pixels:
                                                            if canvas.in_bounds(px, py):
                                                                apply_tool_with_undo_tracking_at_pixel(canvas, current_tool, px, py, current_stroke_changes)
                                            else:
                                                # Draw hollow rectangle with brush thickness
                                                # Top and bottom edges
                                                for x in range(left, right + 1):
                                                    pixels_top = current_tool.get_affected_pixels(x, top)
                                                    pixels_bottom = current_tool.get_affected_pixels(x, bottom)
                                                    for px, py in pixels_top:
                                                        if canvas.in_bounds(px, py):
                                                            apply_tool_with_undo_tracking_at_pixel(canvas, current_tool, px, py, current_stroke_changes)
                                                    for px, py in pixels_bottom:
                                                        if canvas.in_bounds(px, py):
                                                            apply_tool_with_undo_tracking_at_pixel(canvas, current_tool, px, py, current_stroke_changes)
                                                # Left and right edges (excluding corners already drawn)
                                                for y in range(top + 1, bottom):
                                                    pixels_left = current_tool.get_affected_pixels(left, y)
                                                    pixels_right = current_tool.get_affected_pixels(right, y)
                                                    for px, py in pixels_left:
                                                        if canvas.in_bounds(px, py):
                                                            apply_tool_with_undo_tracking_at_pixel(canvas, current_tool, px, py, current_stroke_changes)
                                                    for px, py in pixels_right:
                                                        if canvas.in_bounds(px, py):
                                                            apply_tool_with_undo_tracking_at_pixel(canvas, current_tool, px, py, current_stroke_changes)
                                    
                                    # Save as command for undo
                                    if current_stroke_changes:
                                        command = DrawCommand(canvas, current_stroke_changes.copy())
                                        undo_manager.execute_command(command)
                                    
                                    # Reset preview mode
                                    current_tool_mode = "normal"
                                    preview_start_pos = None
                            else:
                                # Normal drawing completion
                                if current_stroke_changes:
                                    command = DrawCommand(canvas, current_stroke_changes.copy())
                                    undo_manager.execute_command(command)
                                    current_stroke_changes = {}
                            drawing = False
                        else:
                            drawing = False
                        slider_dragging = False
                        last_pos = None
                        h_drag = False
                        v_drag = False

                elif event.type == pygame.MOUSEMOTION:
                    # Scrollbar dragging
                    if h_drag:
                        content_w = canvas.width
                        if content_w > holder_rect.width:
                            track_w = holder_rect.width - (sb_thickness if canvas.height > holder_rect.height else 0)
                            thumb_w = max(20, int(holder_rect.width * holder_rect.width / content_w))
                            max_thumb_x = track_w - thumb_w
                            new_thumb_x = max(0, min(max_thumb_x, mouse_pos[0] - holder_rect.x - h_drag_offset))
                            scroll_x = int((new_thumb_x / max_thumb_x) * (content_w - holder_rect.width)) if max_thumb_x > 0 else 0
                        continue
                    if v_drag:
                        content_h = canvas.height
                        if content_h > holder_rect.height:
                            track_hh = holder_rect.height - (sb_thickness if canvas.width > holder_rect.width else 0)
                            thumb_hg = max(20, int(holder_rect.height * holder_rect.height / content_h))
                            max_thumb_y = track_hh - thumb_hg
                            new_thumb_y = max(0, min(max_thumb_y, mouse_pos[1] - holder_rect.y - v_drag_offset))
                            scroll_y = int((new_thumb_y / max_thumb_y) * (content_h - holder_rect.height)) if max_thumb_y > 0 else 0
                        continue

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
                                draw_pixel_perfect_line(canvas, current_tool, x1, y1, x2, y2, current_stroke_changes)
                            else:
                                # Normal interpolated drawing
                                dx = x2 - x1
                                dy = y2 - y1
                                steps = max(abs(dx), abs(dy))

                                if steps == 0:
                                    apply_tool_with_undo_tracking(canvas, current_tool, x2, y2, current_stroke_changes)
                                else:
                                    for i in range(steps + 1):
                                        x = int(x1 + (dx * i) / steps)
                                        y = int(y1 + (dy * i) / steps)
                                        apply_tool_with_undo_tracking(canvas, current_tool, x, y, current_stroke_changes)
                        last_pos = mouse_pos

                elif event.type == pygame.MOUSEWHEEL:
                    mods = pygame.key.get_mods()
                    ctrl = mods & pygame.KMOD_CTRL
                    shift = mods & pygame.KMOD_SHIFT
                    if ctrl:
                        # Zoom around mouse position
                        old_ps = canvas.pixel_size
                        old_scroll_x, old_scroll_y = scroll_x, scroll_y
                        mouse_x, mouse_y = mouse_pos
                        # Convert mouse to canvas cell before zoom
                        if holder_rect.collidepoint(mouse_pos):
                            cell_x = int((mouse_x - holder_rect.x + scroll_x) / old_ps)
                            cell_y = int((mouse_y - holder_rect.y + scroll_y) / old_ps)
                        else:
                            cell_x = cell_y = None
                        delta = 1 if event.y > 0 else -1
                        new_ps = max(1, min(64, old_ps + delta))
                        if new_ps != old_ps:
                            canvas.set_pixel_size(new_ps)
                            # Adjust scroll to keep cell under mouse fixed
                            if cell_x is not None:
                                scroll_x = max(0, min(canvas.width - holder_rect.width, cell_x * new_ps - (mouse_x - holder_rect.x)))
                            if cell_y is not None:
                                scroll_y = max(0, min(canvas.height - holder_rect.height, cell_y * new_ps - (mouse_y - holder_rect.y)))
                            # Clamp if content smaller than viewport
                            if canvas.width <= holder_rect.width:
                                scroll_x = 0
                            if canvas.height <= holder_rect.height:
                                scroll_y = 0
                    else:
                        # Scroll
                        if shift:
                            # Horizontal scroll
                            content_w = canvas.width
                            if content_w > holder_rect.width:
                                scroll_x = max(0, min(content_w - holder_rect.width, scroll_x - event.y * 30))
                        else:
                            content_h = canvas.height
                            if content_h > holder_rect.height:
                                scroll_y = max(0, min(content_h - holder_rect.height, scroll_y - event.y * 30))

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
                        # Check for undo/redo shortcuts
                        mods = pygame.key.get_mods()
                        ctrl = mods & pygame.KMOD_CTRL
                        shift = mods & pygame.KMOD_SHIFT
                        
                        if ctrl and event.key == pygame.K_z and not shift:
                            # Ctrl+Z - Undo
                            undo_manager.undo()
                        elif ctrl and ((event.key == pygame.K_y) or (shift and event.key == pygame.K_z)):
                            # Ctrl+Y or Ctrl+Shift+Z - Redo
                            undo_manager.redo()
                        
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
                        elif event.key == pygame.K_l:  # line tool
                            tool_manager.set_tool("line")
                        elif event.key == pygame.K_r:  # rectangle tool
                            tool_manager.set_tool("rectangle")
                        elif event.key == pygame.K_i:  # eyedropper tool
                            tool_manager.set_tool("eyedropper")
                        elif event.key == pygame.K_p:  # toggle pixel perfect
                            pixel_perfect = not pixel_perfect
                        elif event.key == pygame.K_g:  # toggle grid
                            canvas.toggle_grid()
                        elif event.key == pygame.K_h:  # toggle symmetry modes or help
                            if shift:
                                symmetry_manager.toggle_horizontal_symmetry()
                            else:
                                show_help = not show_help
                        elif event.key == pygame.K_v:  # toggle vertical symmetry
                            symmetry_manager.toggle_vertical_symmetry()
                        elif event.key == pygame.K_d:  # toggle diagonal symmetry or duplicate layer
                            if ctrl:
                                if canvas and canvas.layer_manager:
                                    canvas.layer_manager.duplicate_layer()
                            else:
                                symmetry_manager.toggle_diagonal_symmetry()
                        elif event.key == pygame.K_n:  # new layer
                            if ctrl and canvas and canvas.layer_manager:
                                canvas.layer_manager.add_layer()
                        elif event.key == pygame.K_DELETE:  # delete layer
                            if canvas and canvas.layer_manager and len(canvas.layer_manager.layers) > 1:
                                canvas.layer_manager.remove_layer(canvas.layer_manager.current_layer_index)
                        elif event.key == pygame.K_F2:  # toggle floating layers window
                            if canvas:
                                if floating_layers_window and floating_layers_window.running:
                                    floating_layers_window.close_window()
                                    floating_layers_window = None
                                else:
                                    floating_layers_window = FloatingLayersWindow(font=font)
                                    floating_layers_window.create_window()
                                    floating_layers_window.set_layer_manager(canvas.layer_manager)
                        elif event.key == pygame.K_t:  # toggle rectangle fill mode
                            if tool_manager.current_tool_name == "rectangle":
                                rect_tool = tool_manager.get_current_tool()
                                rect_tool.toggle_fill_mode()
                        elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                            # Zoom in
                            pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL, {'y': 1}))
                        elif event.key == pygame.K_MINUS:
                            pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL, {'y': -1}))
                        elif event.key == pygame.K_ESCAPE:
                            show_help = False  # Close help if open

        # Clear screen
        screen.fill(GRAY)
        
        # Handle floating layers window
        if floating_layers_window and floating_layers_window.running:
            result = floating_layers_window.handle_events()
            if result["action"] == "close":
                floating_layers_window = None
            elif result["action"] == "new_layer" and canvas:
                canvas.layer_manager.add_layer()
            elif result["action"] == "duplicate_layer" and canvas:
                canvas.layer_manager.duplicate_layer()
            elif result["action"] == "delete_layer" and canvas:
                if len(canvas.layer_manager.layers) > 1:
                    canvas.layer_manager.remove_layer(canvas.layer_manager.current_layer_index)
            elif result["action"] == "merge_down" and canvas:
                canvas.layer_manager.merge_down(canvas.layer_manager.current_layer_index)
            
            # Render the floating window
            floating_layers_window.render()

    # Scene-specific rendering
        if scene == 'home':
            title = home_title_font.render("Kokesprite", True, BLACK)
            subtitle = font.render("Aiming for the perfect sprite editor", True, BLACK)
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 140))
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 110))
            screen.blit(title, title_rect)
            screen.blit(subtitle, subtitle_rect)

            for rect, label in ((new_btn_rect, "New File"), (open_btn_rect, "Open File (PNG)")):
                pygame.draw.rect(screen, WHITE, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)
                txt = font.render(label, True, BLACK)
                txt_rect = txt.get_rect(center=rect.center)
                screen.blit(txt, txt_rect)

            if last_open_path:
                info = font.render(f"Selected: {last_open_path}", True, BLACK)
                screen.blit(info, (20, WINDOW_HEIGHT - 40))

        elif scene == 'new_file':
            # Back button
            pygame.draw.rect(screen, WHITE, back_btn_rect)
            pygame.draw.rect(screen, BLACK, back_btn_rect, 2)
            screen.blit(font.render("Back", True, BLACK), back_btn_rect.move(10, 8))

            # Labels
            prompt = font.render("New File — Set canvas size (pixels)", True, BLACK)
            prompt_rect = prompt.get_rect(center=(WINDOW_WIDTH // 2, fields_y - 40))
            screen.blit(prompt, prompt_rect)

            # Width field
            w_label = font.render("Width", True, BLACK)
            w_label_rect = w_label.get_rect(center=(width_rect.centerx, width_rect.top - 16))
            screen.blit(w_label, w_label_rect)
            pygame.draw.rect(screen, (255, 255, 200) if nf_active == 'width' else WHITE, width_rect)
            pygame.draw.rect(screen, BLACK, width_rect, 2)
            w_text = nf_width_text if nf_width_text else "..."
            screen.blit(font.render(w_text, True, BLACK if nf_width_text else (128, 128, 128)), width_rect.move(8, 8))

            # Height field
            h_label = font.render("Height", True, BLACK)
            h_label_rect = h_label.get_rect(center=(height_rect.centerx, height_rect.top - 16))
            screen.blit(h_label, h_label_rect)
            pygame.draw.rect(screen, (255, 255, 200) if nf_active == 'height' else WHITE, height_rect)
            pygame.draw.rect(screen, BLACK, height_rect, 2)
            h_text = nf_height_text if nf_height_text else "..."
            screen.blit(font.render(h_text, True, BLACK if nf_height_text else (128, 128, 128)), height_rect.move(8, 8))

            # Create button
            pygame.draw.rect(screen, WHITE, create_btn_rect)
            pygame.draw.rect(screen, BLACK, create_btn_rect, 2)
            txt = font.render("Create", True, BLACK)
            txt_rect = txt.get_rect(center=create_btn_rect.center)
            screen.blit(txt, txt_rect)

        elif scene == 'editor':
            # Compute layout rects if needed
            if not options_rect:
                options_rect = pygame.Rect(0, 0, WINDOW_WIDTH, TOP_OPTIONS_H)
                left_rect = pygame.Rect(0, TOP_OPTIONS_H, LEFT_PALETTE_W, WINDOW_HEIGHT - TOP_OPTIONS_H - 30)
                right_rect = pygame.Rect(WINDOW_WIDTH - RIGHT_TOOLS_W, TOP_OPTIONS_H, RIGHT_TOOLS_W, WINDOW_HEIGHT - TOP_OPTIONS_H - 30)
                holder_rect = pygame.Rect(LEFT_PALETTE_W, TOP_OPTIONS_H, WINDOW_WIDTH - LEFT_PALETTE_W - RIGHT_TOOLS_W, WINDOW_HEIGHT - TOP_OPTIONS_H - 30)
                bottom_rect = pygame.Rect(0, WINDOW_HEIGHT - 30, WINDOW_WIDTH, 30)
                
                # Update layers panel size to fit better in left panel
                if layers_panel:
                    # Position after palette with some spacing
                    layers_y = TOP_OPTIONS_H + 200  # After palette
                    layers_height = left_rect.height - 210  # Use remaining space
                    layers_panel.update_size(10, layers_y, LEFT_PALETTE_W - 20, layers_height)

            # Options bar
            ui.x = 10
            ui.y = 10
            ui.width = WINDOW_WIDTH - 20
            ui.height = TOP_OPTIONS_H - 20
            ui.render(screen, tool_manager, size_input_text, size_input_active, pixel_perfect)

            # Left palette panel
            pygame.draw.rect(screen, (235, 235, 235), left_rect)
            pygame.draw.rect(screen, BLACK, left_rect, 1)
            if palette:
                palette.x = left_rect.x + 10
                palette.y = left_rect.y + 10
                palette.render(screen)
                # Show current color above palette
                color_display = pygame.Rect(left_rect.x + 10, left_rect.y + left_rect.height - 60, 80, 40)
                pygame.draw.rect(screen, palette.current_color, color_display)
                pygame.draw.rect(screen, BLACK, color_display, 2)
                
                # Add text label
                color_text = font.render("Current Color", True, BLACK)
                screen.blit(color_text, (left_rect.x + 10, left_rect.y + left_rect.height - 100))
            
            # Add floating layers hint
            if not floating_layers_window or not floating_layers_window.running:
                hint_text = font.render("Press F2 for Layers Panel", True, BLACK)
                screen.blit(hint_text, (left_rect.x + 10, left_rect.y + left_rect.height - 30))

            # Right tools panel
            pygame.draw.rect(screen, (235, 235, 235), right_rect)
            pygame.draw.rect(screen, BLACK, right_rect, 1)
            # Tool buttons stacked vertically with icons
            tool_labels = [("brush", "pencil"), ("eraser", "eraser"), ("fill", "paint-bucket"), 
                          ("line", "line"), ("rectangle", "rectangle"), ("eyedropper", "eyedropper")]
            tool_btns = {}
            ty = right_rect.y + 10
            for name, icon_name in tool_labels:
                rect = pygame.Rect(right_rect.x + 10, ty, right_rect.width - 20, 36)
                tool_btns[name] = rect
                color = (200, 200, 255) if tool_manager.current_tool_name == name else WHITE
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)
                # Render icon centered in button
                icon_manager.render_icon(screen, icon_name, rect.centerx, rect.centery, center=True)
                ty += 46

            # Add rectangle fill mode toggle
            if tool_manager.current_tool_name == "rectangle":
                rect_tool = tool_manager.get_current_tool()
                fill_rect = pygame.Rect(right_rect.x + 10, ty, right_rect.width - 20, 30)
                fill_color = (200, 255, 200) if rect_tool.fill_mode == "fill" else (255, 200, 200)
                pygame.draw.rect(screen, fill_color, fill_rect)
                pygame.draw.rect(screen, BLACK, fill_rect, 1)
                fill_text = font.render(f"Mode: {rect_tool.fill_mode.title()}", True, BLACK)
                text_rect = fill_text.get_rect(center=fill_rect.center)
                screen.blit(fill_text, text_rect)
                tool_btns["rect_fill_toggle"] = fill_rect

            # Handle clicks on tool buttons (simple re-check when mouse is pressed)
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                for name, rect in tool_btns.items():
                    if rect.collidepoint(mouse_pos):
                        if name == "rect_fill_toggle":
                            if tool_manager.current_tool_name == "rectangle":
                                rect_tool = tool_manager.get_current_tool()
                                rect_tool.toggle_fill_mode()
                        else:
                            tool_manager.set_tool(name)

            # Canvas holder (outer canvas that contains the drawing canvas)
            pygame.draw.rect(screen, (250, 250, 250), holder_rect)
            pygame.draw.rect(screen, BLACK, holder_rect, 1)

            # Render canvas to offscreen surface and blit with scroll
            # Set canvas screen position for input mapping
            canvas.x = holder_rect.x - scroll_x
            canvas.y = holder_rect.y - scroll_y
            surface = canvas.render_to_surface()
            # Clip to holder
            prev_clip = screen.get_clip()
            screen.set_clip(holder_rect)
            screen.blit(surface, (canvas.x, canvas.y))
            
            # Draw preview for line/rectangle tools
            if current_tool_mode in ["line_preview", "rectangle_preview"] and preview_start_pos and drawing:
                # Draw preview overlay
                current_mouse = pygame.mouse.get_pos()
                preview_color = (255, 255, 0, 128)  # Yellow preview
                
                if current_tool_mode == "line_preview":
                    # Draw line preview
                    start_screen = (preview_start_pos[0] - scroll_x, preview_start_pos[1] - scroll_y)
                    end_screen = (current_mouse[0] - scroll_x, current_mouse[1] - scroll_y)
                    pygame.draw.line(screen, preview_color[:3], start_screen, end_screen, 2)
                elif current_tool_mode == "rectangle_preview":
                    # Draw rectangle preview
                    start_x = preview_start_pos[0] - scroll_x
                    start_y = preview_start_pos[1] - scroll_y
                    end_x = current_mouse[0] - scroll_x
                    end_y = current_mouse[1] - scroll_y
                    
                    left = min(start_x, end_x)
                    top = min(start_y, end_y)
                    width = abs(end_x - start_x)
                    height = abs(end_y - start_y)
                    
                    if width > 0 and height > 0:
                        preview_rect = pygame.Rect(left, top, width, height)
                        pygame.draw.rect(screen, preview_color[:3], preview_rect, 2)
            
            screen.set_clip(prev_clip)

            # Scrollbars (appear when content exceeds viewport)
            content_w, content_h = canvas.width, canvas.height
            show_h = content_w > holder_rect.width
            show_v = content_h > holder_rect.height

            if show_h:
                track_h = pygame.Rect(holder_rect.x, holder_rect.bottom - sb_thickness, holder_rect.width - (sb_thickness if show_v else 0), sb_thickness)
                pygame.draw.rect(screen, (230, 230, 230), track_h)
                pygame.draw.rect(screen, BLACK, track_h, 1)
                thumb_w = max(20, int(holder_rect.width * holder_rect.width / content_w))
                max_thumb_x = track_h.width - thumb_w
                thumb_x = track_h.x + (0 if content_w == holder_rect.width else int((scroll_x / (content_w - holder_rect.width)) * max_thumb_x))
                thumb_h_rect = pygame.Rect(thumb_x, track_h.y, thumb_w, sb_thickness)
                pygame.draw.rect(screen, (180, 180, 180), thumb_h_rect)
                pygame.draw.rect(screen, BLACK, thumb_h_rect, 1)

            if show_v:
                track_v = pygame.Rect(holder_rect.right - sb_thickness, holder_rect.y, sb_thickness, holder_rect.height - (sb_thickness if show_h else 0))
                pygame.draw.rect(screen, (230, 230, 230), track_v)
                pygame.draw.rect(screen, BLACK, track_v, 1)
                thumb_hg = max(20, int(holder_rect.height * holder_rect.height / content_h))
                max_thumb_y = track_v.height - thumb_hg
                thumb_y = track_v.y + (0 if content_h == holder_rect.height else int((scroll_y / (content_h - holder_rect.height)) * max_thumb_y))
                thumb_v_rect = pygame.Rect(track_v.x, thumb_y, sb_thickness, thumb_hg)
                pygame.draw.rect(screen, (180, 180, 180), thumb_v_rect)
                pygame.draw.rect(screen, BLACK, thumb_v_rect, 1)
            
            # Status bar
            if status_bar:
                status_bar.render(screen, tool_manager, canvas, symmetry_manager, canvas.layer_manager)
            
            # Help overlay
            if show_help:
                KeyboardShortcuts.render_help_overlay(screen, font, font)

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
