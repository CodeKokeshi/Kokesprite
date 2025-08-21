class Command:
    """Base class for undoable commands"""
    def execute(self):
        """Execute the command"""
        pass
    
    def undo(self):
        """Undo the command"""
        pass


class DrawCommand(Command):
    """Command for drawing operations (brush, eraser)"""
    def __init__(self, canvas, pixels_changed, already_executed=True):
        self.canvas = canvas
        self.pixels_changed = pixels_changed  # Dict of {(x, y): (old_color, new_color)}
        self.already_executed = already_executed  # Track if this command was already applied to canvas
    
    def execute(self):
        """Apply the new pixel states"""
        if not self.already_executed:
            for (x, y), (old_color, new_color) in self.pixels_changed.items():
                if new_color is None:
                    self.canvas.erase_pixel(x, y)
                else:
                    self.canvas.set_pixel(x, y, new_color)
        self.already_executed = True
    
    def undo(self):
        """Restore the old pixel states"""
        for (x, y), (old_color, new_color) in self.pixels_changed.items():
            if old_color is None:
                self.canvas.erase_pixel(x, y)
            else:
                self.canvas.set_pixel(x, y, old_color)
        self.already_executed = False  # After undo, will need to execute again for redo


class FillCommand(Command):
    """Command for fill operations"""
    def __init__(self, canvas, pixels_changed, already_executed=True):
        self.canvas = canvas
        self.pixels_changed = pixels_changed  # Dict of {(x, y): (old_color, new_color)}
        self.already_executed = already_executed  # Track if this command was already applied to canvas
    
    def execute(self):
        """Apply the fill"""
        if not self.already_executed:
            for (x, y), (old_color, new_color) in self.pixels_changed.items():
                if new_color is None:
                    self.canvas.erase_pixel(x, y)
                else:
                    self.canvas.set_pixel(x, y, new_color)
        self.already_executed = True
    
    def undo(self):
        """Restore pre-fill state"""
        for (x, y), (old_color, new_color) in self.pixels_changed.items():
            if old_color is None:
                self.canvas.erase_pixel(x, y)
            else:
                self.canvas.set_pixel(x, y, old_color)
        self.already_executed = False  # After undo, will need to execute again for redo


class UndoRedoManager:
    """Manages undo/redo history"""
    def __init__(self, max_history=50):
        self.history = []  # List of commands
        self.current_index = -1  # Current position in history
        self.max_history = max_history
    
    def add_command(self, command):
        """Add a command to history without executing it (for already-applied commands)"""
        # Remove any commands after current index (when we add after undoing)
        self.history = self.history[:self.current_index + 1]
        
        # Add new command
        self.history.append(command)
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1
    
    def execute_command(self, command):
        """Execute a command and add it to history"""
        # Remove any commands after current index (when we execute after undoing)
        self.history = self.history[:self.current_index + 1]
        
        # Add new command
        self.history.append(command)
        self.current_index += 1
        
        # Execute the command
        command.execute()
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1
    
    def undo(self):
        """Undo the last command"""
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            return True
        return False
    
    def redo(self):
        """Redo the next command"""
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            return True
        return False
    
    def can_undo(self):
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self):
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1
    
    def clear(self):
        """Clear all history"""
        self.history = []
        self.current_index = -1
