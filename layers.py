import pygame
from copy import deepcopy

class Layer:
    """Represents a single drawing layer"""
    
    def __init__(self, name="Layer", visible=True, opacity=1.0):
        self.name = name
        self.visible = visible
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp to 0-1
        self.pixels = {}  # Dictionary of {(x, y): (r, g, b)}
    
    def set_pixel(self, x, y, color):
        """Set a pixel on this layer"""
        self.pixels[(x, y)] = color
    
    def erase_pixel(self, x, y):
        """Erase a pixel from this layer"""
        self.pixels.pop((x, y), None)
    
    def get_pixel(self, x, y):
        """Get pixel color at position, returns None if no pixel"""
        return self.pixels.get((x, y), None)
    
    def clear(self):
        """Clear all pixels from this layer"""
        self.pixels.clear()
    
    def copy(self):
        """Create a copy of this layer"""
        new_layer = Layer(self.name + " Copy", self.visible, self.opacity)
        new_layer.pixels = deepcopy(self.pixels)
        return new_layer


class LayerManager:
    """Manages multiple drawing layers"""
    
    def __init__(self):
        self.layers = []
        self.current_layer_index = 0
        self.add_layer("Background")  # Create initial layer
    
    def add_layer(self, name=None, index=None):
        """Add a new layer"""
        if name is None:
            name = f"Layer {len(self.layers) + 1}"
        
        layer = Layer(name)
        
        if index is None:
            self.layers.append(layer)
            self.current_layer_index = len(self.layers) - 1
        else:
            self.layers.insert(index, layer)
            if index <= self.current_layer_index:
                self.current_layer_index += 1
        
        return layer
    
    def remove_layer(self, index):
        """Remove a layer by index"""
        if len(self.layers) <= 1:  # Don't remove the last layer
            return False
        
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            
            # Adjust current layer index
            if index < self.current_layer_index:
                self.current_layer_index -= 1
            elif index == self.current_layer_index:
                self.current_layer_index = min(self.current_layer_index, len(self.layers) - 1)
            
            return True
        return False
    
    def move_layer(self, from_index, to_index):
        """Move a layer from one position to another"""
        if 0 <= from_index < len(self.layers) and 0 <= to_index < len(self.layers):
            layer = self.layers.pop(from_index)
            self.layers.insert(to_index, layer)
            
            # Update current layer index
            if from_index == self.current_layer_index:
                self.current_layer_index = to_index
            elif from_index < self.current_layer_index <= to_index:
                self.current_layer_index -= 1
            elif to_index <= self.current_layer_index < from_index:
                self.current_layer_index += 1
            
            return True
        return False
    
    def get_current_layer(self):
        """Get the currently active layer"""
        if 0 <= self.current_layer_index < len(self.layers):
            return self.layers[self.current_layer_index]
        return None
    
    def set_current_layer(self, index):
        """Set the active layer by index"""
        if 0 <= index < len(self.layers):
            self.current_layer_index = index
            return True
        return False
    
    def duplicate_layer(self, index=None):
        """Duplicate a layer"""
        if index is None:
            index = self.current_layer_index
        
        if 0 <= index < len(self.layers):
            original_layer = self.layers[index]
            new_layer = original_layer.copy()
            self.layers.insert(index + 1, new_layer)
            self.current_layer_index = index + 1
            return new_layer
        return None
    
    def flatten_layers(self, canvas_width, canvas_height):
        """Flatten all visible layers into a single pixel dictionary"""
        flattened = {}
        
        # Process layers from bottom to top
        for layer in self.layers:
            if not layer.visible:
                continue
            
            for (x, y), color in layer.pixels.items():
                if 0 <= x < canvas_width and 0 <= y < canvas_height:
                    if layer.opacity >= 1.0:
                        # Fully opaque
                        flattened[(x, y)] = color
                    else:
                        # Blend with existing pixel
                        existing = flattened.get((x, y), (255, 255, 255))  # Default to white
                        r1, g1, b1 = existing
                        r2, g2, b2 = color
                        alpha = layer.opacity
                        
                        # Alpha blending
                        r = int(r1 * (1 - alpha) + r2 * alpha)
                        g = int(g1 * (1 - alpha) + g2 * alpha)
                        b = int(b1 * (1 - alpha) + b2 * alpha)
                        
                        flattened[(x, y)] = (r, g, b)
        
        return flattened
    
    def merge_down(self, index=None):
        """Merge layer with the one below it"""
        if index is None:
            index = self.current_layer_index
        
        if index > 0 and index < len(self.layers):
            current_layer = self.layers[index]
            below_layer = self.layers[index - 1]
            
            # Merge current layer into the one below
            for (x, y), color in current_layer.pixels.items():
                if current_layer.opacity >= 1.0:
                    below_layer.set_pixel(x, y, color)
                else:
                    # Blend colors
                    existing = below_layer.get_pixel(x, y)
                    if existing:
                        r1, g1, b1 = existing
                        r2, g2, b2 = color
                        alpha = current_layer.opacity
                        
                        r = int(r1 * (1 - alpha) + r2 * alpha)
                        g = int(g1 * (1 - alpha) + g2 * alpha)
                        b = int(b1 * (1 - alpha) + b2 * alpha)
                        
                        below_layer.set_pixel(x, y, (r, g, b))
                    else:
                        below_layer.set_pixel(x, y, color)
            
            # Remove the merged layer
            self.remove_layer(index)
            return True
        return False
    
    def set_canvas_center(self, width, height):
        """Set canvas dimensions for center calculations (compatibility method)"""
        pass  # This method is for compatibility with existing canvas code
