# Kokesprite

## Why this project
Kokesprite exists to attempt the creation of the "perfect" sprite editor — fast, precise, and focused on pixel art. The goal is to blend a frictionless workflow with pixel-perfect tools, minimal UI clutter, and a keyboard-friendly experience inspired by great editors while staying simple and open.

Design principles:
- Pixel-first accuracy (no blurry edges, consistent grid alignment)
- Smooth, gap-free strokes and true pixel-perfect lines
- Immediate feedback (clear previews, intuitive controls)
- Minimal ceremony: draw quickly, switch tools instantly

## Status (what works today)
- Canvas for pixel-by-pixel drawing with a visible grid
- Brush tool with size 1–256 and shape toggle (square/circle) + live preview
- Eraser tool (shares size/shape controls with brush)
- Fill/Bucket tool (click to flood-fill)
- Pixel Perfect toggle for single-pixel stair-step diagonals
- Color palette panel with swatch selection and current color display

## Roadmap (from `process.txt`)
- New file dialog with custom canvas dimensions (e.g., 128×128)
- Symmetry toggle (e.g., vertical/horizontal mirror painting)
- Layers

Have ideas that make sprite editing faster or more delightful? Please propose them!

## Run locally (Windows / PowerShell)
Prerequisites:
- Python 3.10+ installed

Install dependency:
```powershell
python -m pip install pygame
```

Run the app:
```powershell
python .\main.py
```

Tip: Use the toolbar to switch tools and tweak settings. Keyboard shortcuts include:
- [ / ] to decrease/increase brush size
- T to toggle brush shape

## Project structure
- `main.py` — App entry point and event loop
- `canvas.py` — Pixel grid, coordinate math, and rendering
- `tools.py` — Tools (Brush, Eraser, Fill) and tool manager
- `ui.py` — Toolbar, slider, numeric input, and toggles
- `palette.py` — Palette UI and color selection
- `process.txt` — Feature checklist/roadmap

## License
No license specified yet. If you plan to use this project beyond local experimentation, consider adding a license file first.
