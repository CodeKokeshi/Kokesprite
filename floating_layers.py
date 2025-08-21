try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TK = True
except Exception:
    HAS_TK = False


class FloatingLayersWindow:
    """A floating window for layer management (Tkinter-based)."""

    def __init__(self, width=300, height=420, font=None):
        self.width = width
        self.height = height
        self.layer_manager = None
        self.root = None
        self.listbox = None
        self.running = False

    def create_window(self):
        if not HAS_TK or self.root:
            return False
        self.root = tk.Tk()
        self.root.title("Layers")
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        # List frame
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.listbox = tk.Listbox(frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Buttons
        btns = ttk.Frame(self.root)
        btns.pack(fill=tk.X, padx=6, pady=6)

        ttk.Button(btns, text="New", command=self._new_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Duplicate", command=self._dup_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self._del_layer).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Merge Down", command=self._merge_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Toggle Vis", command=self._toggle_vis).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Close", command=self.close_window).pack(side=tk.RIGHT, padx=2)

        self.running = True
        self._refresh_list()
        return True

    def close_window(self):
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
        self.root = None
        self.listbox = None
        self.running = False

    def set_layer_manager(self, layer_manager):
        self.layer_manager = layer_manager
        self._refresh_list()

    def handle_events(self):
        # No discrete event pump; return close action if window vanished
        if self.running and (self.root is None or not HAS_TK):
            return {"action": "close"}
        return {"action": None}

    def render(self):
        if not self.running or not self.root:
            return
        self._refresh_list()
        try:
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            self.close_window()

    # Internal helpers
    def _refresh_list(self):
        if not self.listbox or not self.layer_manager:
            return
        # Build list top-first
        items = []
        current = self.layer_manager.current_layer_index
        for i in range(len(self.layer_manager.layers)):
            idx = len(self.layer_manager.layers) - 1 - i
            layer = self.layer_manager.layers[idx]
            eye = "👁" if getattr(layer, 'visible', True) else "✖"
            name = getattr(layer, 'name', f"Layer {idx+1}")
            mark = "* " if idx == current else "  "
            items.append(f"{mark}{eye} {name}")
        # Update listbox only if changed
        existing = list(self.listbox.get(0, tk.END))
        if existing != items:
            self.listbox.delete(0, tk.END)
            for it in items:
                self.listbox.insert(tk.END, it)
            # Restore selection
            sel_top_index = (len(self.layer_manager.layers) - 1 - current) if 0 <= current < len(self.layer_manager.layers) else None
            if sel_top_index is not None:
                try:
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(sel_top_index)
                except Exception:
                    pass

    def _map_selection_to_actual(self):
        if not self.listbox or not self.layer_manager:
            return None
        sel = self.listbox.curselection()
        if not sel:
            return None
        top_index = sel[0]
        actual_index = len(self.layer_manager.layers) - 1 - top_index
        if 0 <= actual_index < len(self.layer_manager.layers):
            return actual_index
        return None

    def _on_select(self, event=None):
        idx = self._map_selection_to_actual()
        if idx is not None and self.layer_manager:
            self.layer_manager.set_current_layer(idx)

    def _new_layer(self):
        if self.layer_manager:
            self.layer_manager.add_layer()
            self._refresh_list()

    def _dup_layer(self):
        if self.layer_manager:
            self.layer_manager.duplicate_layer()
            self._refresh_list()

    def _del_layer(self):
        if self.layer_manager and len(self.layer_manager.layers) > 1:
            self.layer_manager.remove_layer(self.layer_manager.current_layer_index)
            self._refresh_list()

    def _merge_down(self):
        if self.layer_manager:
            self.layer_manager.merge_down(self.layer_manager.current_layer_index)
            self._refresh_list()

    def _toggle_vis(self):
        if not self.layer_manager:
            return
        idx = self._map_selection_to_actual()
        if idx is None:
            idx = self.layer_manager.current_layer_index
        if 0 <= idx < len(self.layer_manager.layers):
            layer = self.layer_manager.layers[idx]
            layer.visible = not getattr(layer, 'visible', True)
            self._refresh_list()
