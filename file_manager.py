import pygame
import json
import os
from PIL import Image
import io

class FileManager:
    """Handles saving, loading, and exporting canvas data"""
    
    def __init__(self):
        self.current_file_path = None
        self.project_extension = ".kks"  # Kokesprite project file
    
    def save_project(self, canvas, palette, file_path=None):
        """Save canvas and palette data to a project file"""
        if file_path is None:
            file_path = self.current_file_path
        if file_path is None:
            return False
        
        try:
            # Prepare project data
            project_data = {
                "version": "1.0",
                "canvas": {
                    "width": canvas.canvas_width,
                    "height": canvas.canvas_height,
                    "pixels": {f"{x},{y}": list(color) for (x, y), color in canvas.pixels.items()}
                },
                "palette": {
                    "colors": [list(color) for color in palette.colors],
                    "current_index": palette.current_index
                }
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            self.current_file_path = file_path
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    def load_project(self, file_path):
        """Load canvas and palette data from a project file"""
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            # Extract canvas data
            canvas_data = project_data.get("canvas", {})
            canvas_width = canvas_data.get("width", 128)
            canvas_height = canvas_data.get("height", 128)
            pixel_data = canvas_data.get("pixels", {})
            
            # Extract palette data
            palette_data = project_data.get("palette", {})
            palette_colors = [tuple(color) for color in palette_data.get("colors", [])]
            current_index = palette_data.get("current_index", 0)
            
            # Convert pixel data back to proper format
            pixels = {}
            for coord_str, color_list in pixel_data.items():
                x, y = map(int, coord_str.split(','))
                pixels[(x, y)] = tuple(color_list)
            
            self.current_file_path = file_path
            return {
                "canvas_width": canvas_width,
                "canvas_height": canvas_height,
                "pixels": pixels,
                "palette_colors": palette_colors,
                "current_index": current_index
            }
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def export_png(self, canvas, file_path, scale=1):
        """Export canvas as PNG image"""
        try:
            # Create PIL Image
            img_width = canvas.canvas_width * scale
            img_height = canvas.canvas_height * scale
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            
            # Fill pixels
            for (x, y), color in canvas.pixels.items():
                if scale == 1:
                    img.putpixel((x, y), color + (255,))  # Add alpha
                else:
                    # Scale up the pixel
                    for sx in range(scale):
                        for sy in range(scale):
                            px = x * scale + sx
                            py = y * scale + sy
                            if px < img_width and py < img_height:
                                img.putpixel((px, py), color + (255,))
            
            img.save(file_path, 'PNG')
            return True
        except Exception as e:
            print(f"Error exporting PNG: {e}")
            return False
    
    def import_png(self, file_path):
        """Import PNG image and convert to canvas pixels"""
        try:
            img = Image.open(file_path).convert('RGBA')
            width, height = img.size
            
            pixels = {}
            for y in range(height):
                for x in range(width):
                    r, g, b, a = img.getpixel((x, y))
                    if a > 128:  # Only import non-transparent pixels
                        pixels[(x, y)] = (r, g, b)
            
            return {
                "canvas_width": width,
                "canvas_height": height,
                "pixels": pixels
            }
        except Exception as e:
            print(f"Error importing PNG: {e}")
            return None
    
    def get_project_name(self):
        """Get current project name from file path"""
        if self.current_file_path:
            return os.path.splitext(os.path.basename(self.current_file_path))[0]
        return "Untitled"
