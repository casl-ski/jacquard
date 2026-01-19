#!/usr/bin/env python3
"""
Knitting Pattern Designer
A simple app for designing knitting patterns on a grid.
"""

import tkinter as tk
from tkinter import colorchooser
import json
import os


class KnittingDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("Knitting Pattern Designer")
        self.root.configure(bg="#2d2d2d")

        # Configuration
        self.grid_size = 128
        self.tile_size = 5  # pixels per tile
        self.min_tile_size = 2
        self.max_tile_size = 20
        self.max_colors = 15

        # State
        self.selected_color_index = 0
        self.colors = ["#ffffff"] * self.max_colors
        self.colors[0] = "#3a6ea5"  # Default first color
        self.grid_data = [["#f5f5f5" for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.color_buttons = []

        # Track mouse state for dragging
        self.is_dragging = False
        self.current_stroke = []  # Tiles painted in current stroke

        # Undo history
        self.undo_history = []
        self.max_undo = 50

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#2d2d2d")
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Left panel - Color selector
        self.setup_color_panel(main_frame)

        # Right panel - Grid canvas
        self.setup_grid_panel(main_frame)

    def setup_color_panel(self, parent):
        color_frame = tk.Frame(parent, bg="#2d2d2d")
        color_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        # Title
        title = tk.Label(color_frame, text="Colors", fg="#cccccc", bg="#2d2d2d", font=("Arial", 11))
        title.pack(pady=(0, 10))

        # Color slots
        for i in range(self.max_colors):
            frame = tk.Frame(color_frame, bg="#2d2d2d")
            frame.pack(pady=2)

            # Color button
            btn = tk.Button(
                frame,
                width=3,
                height=1,
                bg=self.colors[i],
                relief=tk.FLAT,
                borderwidth=2,
                highlightthickness=2,
                highlightbackground="#2d2d2d"
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            btn.bind("<Button-1>", lambda e, idx=i: self.select_color(idx))
            btn.bind("<Button-3>", lambda e, idx=i: self.edit_color(idx))  # Right-click to edit
            self.color_buttons.append(btn)

            # Label
            label = tk.Label(frame, text=f"{i+1:2d}", fg="#888888", bg="#2d2d2d", font=("Arial", 9))
            label.pack(side=tk.LEFT)

        # Instructions
        instructions = tk.Label(
            color_frame,
            text="Left-click: Select\nRight-click: Edit\nCtrl+Z: Undo\nScroll: Zoom",
            fg="#666666",
            bg="#2d2d2d",
            font=("Arial", 8),
            justify=tk.LEFT
        )
        instructions.pack(pady=(15, 0))

        # Zoom controls
        zoom_frame = tk.Frame(color_frame, bg="#2d2d2d")
        zoom_frame.pack(pady=(10, 0))

        zoom_out_btn = tk.Button(
            zoom_frame,
            text="-",
            command=lambda: self.zoom(-1),
            bg="#444444",
            fg="#cccccc",
            relief=tk.FLAT,
            width=2
        )
        zoom_out_btn.pack(side=tk.LEFT, padx=2)

        self.zoom_label = tk.Label(
            zoom_frame,
            text="100%",
            fg="#888888",
            bg="#2d2d2d",
            font=("Arial", 9),
            width=5
        )
        self.zoom_label.pack(side=tk.LEFT, padx=2)

        zoom_in_btn = tk.Button(
            zoom_frame,
            text="+",
            command=lambda: self.zoom(1),
            bg="#444444",
            fg="#cccccc",
            relief=tk.FLAT,
            width=2
        )
        zoom_in_btn.pack(side=tk.LEFT, padx=2)

        # Clear button
        clear_btn = tk.Button(
            color_frame,
            text="Clear Grid",
            command=self.clear_grid,
            bg="#444444",
            fg="#cccccc",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        clear_btn.pack(pady=(20, 0))

        # Highlight initially selected color
        self.update_color_selection()

    def setup_grid_panel(self, parent):
        grid_frame = tk.Frame(parent, bg="#2d2d2d")
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas with scrollbars
        canvas_frame = tk.Frame(grid_frame, bg="#2d2d2d")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas
        canvas_size = self.grid_size * self.tile_size
        self.canvas = tk.Canvas(
            canvas_frame,
            width=min(640, canvas_size),
            height=min(640, canvas_size),
            bg="#3d3d3d",
            highlightthickness=0,
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)

        # Set scroll region
        self.canvas.config(scrollregion=(0, 0, canvas_size, canvas_size))

        # Draw initial grid
        self.draw_grid()

        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Zoom with mouse wheel
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows/Mac
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down

        # Keyboard shortcuts
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-Z>", self.undo)
        self.root.bind("<Control-plus>", lambda e: self.zoom(1))
        self.root.bind("<Control-equal>", lambda e: self.zoom(1))
        self.root.bind("<Control-minus>", lambda e: self.zoom(-1))

    def draw_grid(self):
        """Draw the entire grid."""
        self.canvas.delete("all")
        self.tile_ids = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                x1 = col * self.tile_size
                y1 = row * self.tile_size
                x2 = x1 + self.tile_size
                y2 = y1 + self.tile_size

                tile_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=self.grid_data[row][col],
                    outline="#4a4a4a",
                    width=1
                )
                self.tile_ids[row][col] = tile_id

    def select_color(self, index):
        """Select a color for painting."""
        self.selected_color_index = index
        self.update_color_selection()

    def edit_color(self, index):
        """Open color picker to edit a color slot."""
        color = colorchooser.askcolor(
            initialcolor=self.colors[index],
            title=f"Choose Color {index + 1}"
        )
        if color[1]:
            self.colors[index] = color[1]
            self.color_buttons[index].configure(bg=color[1])
            self.save_settings()

    def update_color_selection(self):
        """Update visual indication of selected color."""
        for i, btn in enumerate(self.color_buttons):
            if i == self.selected_color_index:
                btn.configure(highlightbackground="#ffffff", highlightthickness=3)
            else:
                btn.configure(highlightbackground="#2d2d2d", highlightthickness=2)

    def get_tile_at(self, event):
        """Get tile coordinates from canvas event."""
        # Convert to canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        col = int(canvas_x // self.tile_size)
        row = int(canvas_y // self.tile_size)

        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            return row, col
        return None

    def paint_tile(self, row, col, record_undo=True):
        """Paint a tile with the selected color."""
        color = self.colors[self.selected_color_index]
        old_color = self.grid_data[row][col]

        if old_color == color:
            return  # No change needed

        if record_undo:
            self.current_stroke.append((row, col, old_color))

        self.grid_data[row][col] = color
        self.canvas.itemconfig(self.tile_ids[row][col], fill=color)

    def on_canvas_click(self, event):
        """Handle canvas click."""
        self.is_dragging = True
        self.current_stroke = []
        pos = self.get_tile_at(event)
        if pos:
            self.paint_tile(*pos)

    def on_canvas_drag(self, event):
        """Handle canvas drag for continuous painting."""
        if self.is_dragging:
            pos = self.get_tile_at(event)
            if pos:
                self.paint_tile(*pos)

    def on_canvas_release(self, event):
        """Handle mouse release."""
        self.is_dragging = False
        if self.current_stroke:
            self.undo_history.append(self.current_stroke)
            if len(self.undo_history) > self.max_undo:
                self.undo_history.pop(0)
        self.current_stroke = []

    def on_mousewheel(self, event):
        """Handle mouse wheel for zooming."""
        # Determine scroll direction
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.zoom(1)
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.zoom(-1)

    def zoom(self, direction):
        """Zoom in or out."""
        old_size = self.tile_size
        if direction > 0:
            self.tile_size = min(self.tile_size + 1, self.max_tile_size)
        else:
            self.tile_size = max(self.tile_size - 1, self.min_tile_size)

        if self.tile_size != old_size:
            # Update zoom label
            zoom_percent = int((self.tile_size / 5) * 100)
            self.zoom_label.config(text=f"{zoom_percent}%")

            # Redraw grid
            self.draw_grid()

            # Update scroll region
            canvas_size = self.grid_size * self.tile_size
            self.canvas.config(scrollregion=(0, 0, canvas_size, canvas_size))

    def undo(self, _event=None):
        """Undo the last stroke."""
        if not self.undo_history:
            return

        stroke = self.undo_history.pop()
        for row, col, old_color in stroke:
            self.grid_data[row][col] = old_color
            self.canvas.itemconfig(self.tile_ids[row][col], fill=old_color)

    def clear_grid(self):
        """Clear the entire grid to default color."""
        default_color = "#f5f5f5"
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                self.grid_data[row][col] = default_color
                self.canvas.itemconfig(self.tile_ids[row][col], fill=default_color)

    def save_settings(self):
        """Save color presets to file."""
        settings = {"colors": self.colors}
        settings_path = os.path.join(os.path.dirname(__file__), "knitting_settings.json")
        try:
            with open(settings_path, "w") as f:
                json.dump(settings, f)
        except Exception:
            pass

    def load_settings(self):
        """Load color presets from file."""
        settings_path = os.path.join(os.path.dirname(__file__), "knitting_settings.json")
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
                if "colors" in settings:
                    self.colors = settings["colors"][:self.max_colors]
                    # Pad if needed
                    while len(self.colors) < self.max_colors:
                        self.colors.append("#ffffff")
                    # Update buttons
                    for i, btn in enumerate(self.color_buttons):
                        btn.configure(bg=self.colors[i])
        except Exception:
            pass


def main():
    root = tk.Tk()
    root.minsize(800, 700)
    app = KnittingDesigner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
