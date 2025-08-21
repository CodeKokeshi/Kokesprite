class SymmetryManager:
    """Manages symmetry painting modes"""
    
    def __init__(self):
        self.horizontal_symmetry = False
        self.vertical_symmetry = False
        self.diagonal_symmetry = False
        self.center_x = 64  # Canvas center X
        self.center_y = 64  # Canvas center Y
    
    def set_canvas_center(self, width, height):
        """Update the symmetry center based on canvas size"""
        self.center_x = width // 2
        self.center_y = height // 2
    
    def toggle_horizontal_symmetry(self):
        """Toggle horizontal (vertical axis) symmetry"""
        self.horizontal_symmetry = not self.horizontal_symmetry
        return self.horizontal_symmetry
    
    def toggle_vertical_symmetry(self):
        """Toggle vertical (horizontal axis) symmetry"""
        self.vertical_symmetry = not self.vertical_symmetry
        return self.vertical_symmetry
    
    def toggle_diagonal_symmetry(self):
        """Toggle diagonal symmetry (experimental)"""
        self.diagonal_symmetry = not self.diagonal_symmetry
        return self.diagonal_symmetry
    
    def get_symmetry_points(self, x, y, canvas_width, canvas_height):
        """Get all symmetry points for a given pixel position"""
        points = [(x, y)]  # Original point
        
        if self.horizontal_symmetry:
            # Mirror across vertical axis (center line)
            mirror_x = (self.center_x * 2) - x
            if 0 <= mirror_x < canvas_width:
                points.append((mirror_x, y))
        
        if self.vertical_symmetry:
            # Mirror across horizontal axis (center line)
            mirror_y = (self.center_y * 2) - y
            if 0 <= mirror_y < canvas_height:
                if self.horizontal_symmetry:
                    # Add both horizontal and vertical mirrors
                    mirror_x = (self.center_x * 2) - x
                    if 0 <= mirror_x < canvas_width:
                        points.append((mirror_x, mirror_y))
                points.append((x, mirror_y))
        
        if self.diagonal_symmetry:
            # Mirror across main diagonal (x,y) -> (y,x)
            if 0 <= y < canvas_width and 0 <= x < canvas_height:
                points.append((y, x))
                
                # If both horizontal and vertical symmetry are on, add more diagonal points
                if self.horizontal_symmetry and self.vertical_symmetry:
                    mirror_x = (self.center_x * 2) - y
                    mirror_y = (self.center_y * 2) - x
                    if 0 <= mirror_x < canvas_width and 0 <= mirror_y < canvas_height:
                        points.append((mirror_x, mirror_y))
        
        # Remove duplicates and out-of-bounds points
        valid_points = []
        seen = set()
        for px, py in points:
            if (px, py) not in seen and 0 <= px < canvas_width and 0 <= py < canvas_height:
                valid_points.append((px, py))
                seen.add((px, py))
        
        return valid_points
    
    def apply_symmetry_to_pixels(self, pixels, canvas_width, canvas_height):
        """Apply symmetry to a list of pixel coordinates"""
        all_pixels = []
        for x, y in pixels:
            symmetry_points = self.get_symmetry_points(x, y, canvas_width, canvas_height)
            all_pixels.extend(symmetry_points)
        
        # Remove duplicates
        return list(set(all_pixels))
    
    def is_any_symmetry_active(self):
        """Check if any symmetry mode is active"""
        return self.horizontal_symmetry or self.vertical_symmetry or self.diagonal_symmetry
    
    def get_status_text(self):
        """Get a text description of active symmetry modes"""
        modes = []
        if self.horizontal_symmetry:
            modes.append("H")
        if self.vertical_symmetry:
            modes.append("V")
        if self.diagonal_symmetry:
            modes.append("D")
        
        if modes:
            return f"Symmetry: {'+'.join(modes)}"
        return "Symmetry: Off"
