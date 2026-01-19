#!/usr/bin/env python3
"""
Knitting Pattern Designer
A simple app for designing knitting patterns on a grid.
"""

import tkinter as tk
import json
import os
import colorsys
import math


class ModernColorPicker(tk.Toplevel):
    """A modern color picker with HSV wheel, saturation/value square, and hex input."""

    def __init__(self, parent, initial_color="#ffffff", title="Choose Color", recent_colors=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="#2d2d2d")
        self.resizable(False, False)
        self.transient(parent)

        self.result = None
        self.recent_colors = recent_colors or []

        # Parse initial color
        self.current_hue = 0.0
        self.current_sat = 1.0
        self.current_val = 1.0
        self._set_color_from_hex(initial_color)
        self.initial_color = initial_color

        # Dimensions
        self.wheel_size = 200
        self.wheel_radius = self.wheel_size // 2
        self.wheel_inner_radius = self.wheel_radius - 25
        self.sv_size = 150

        self._setup_ui()
        self._draw_color_wheel()
        self._draw_sv_square()
        self._update_indicators()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.bind("<Return>", lambda e: self._on_ok())

        # Grab focus after window is visible
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _setup_ui(self):
        main_frame = tk.Frame(self, bg="#2d2d2d", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section: wheel and SV square
        top_frame = tk.Frame(main_frame, bg="#2d2d2d")
        top_frame.pack(fill=tk.X)

        # Color wheel
        wheel_frame = tk.Frame(top_frame, bg="#2d2d2d")
        wheel_frame.pack(side=tk.LEFT, padx=(0, 15))

        self.wheel_canvas = tk.Canvas(
            wheel_frame,
            width=self.wheel_size,
            height=self.wheel_size,
            bg="#2d2d2d",
            highlightthickness=0
        )
        self.wheel_canvas.pack()
        self.wheel_canvas.bind("<Button-1>", self._on_wheel_click)
        self.wheel_canvas.bind("<B1-Motion>", self._on_wheel_click)

        # SV square
        sv_frame = tk.Frame(top_frame, bg="#2d2d2d")
        sv_frame.pack(side=tk.LEFT)

        self.sv_canvas = tk.Canvas(
            sv_frame,
            width=self.sv_size,
            height=self.sv_size,
            bg="#2d2d2d",
            highlightthickness=0
        )
        self.sv_canvas.pack()
        self.sv_canvas.bind("<Button-1>", self._on_sv_click)
        self.sv_canvas.bind("<B1-Motion>", self._on_sv_click)

        # Preview and input section
        middle_frame = tk.Frame(main_frame, bg="#2d2d2d")
        middle_frame.pack(fill=tk.X, pady=(15, 0))

        # Color preview (old vs new)
        preview_frame = tk.Frame(middle_frame, bg="#2d2d2d")
        preview_frame.pack(side=tk.LEFT)

        tk.Label(preview_frame, text="Old", fg="#888888", bg="#2d2d2d", font=("Arial", 8)).pack()
        self.old_preview = tk.Canvas(preview_frame, width=50, height=30, highlightthickness=1, highlightbackground="#555555")
        self.old_preview.pack()
        self.old_preview.create_rectangle(0, 0, 50, 30, fill=self.initial_color, outline="")

        tk.Label(preview_frame, text="New", fg="#888888", bg="#2d2d2d", font=("Arial", 8)).pack(pady=(5, 0))
        self.new_preview = tk.Canvas(preview_frame, width=50, height=30, highlightthickness=1, highlightbackground="#555555")
        self.new_preview.pack()

        # Hex input
        input_frame = tk.Frame(middle_frame, bg="#2d2d2d")
        input_frame.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(input_frame, text="Hex", fg="#888888", bg="#2d2d2d", font=("Arial", 9)).pack(anchor=tk.W)

        hex_entry_frame = tk.Frame(input_frame, bg="#444444")
        hex_entry_frame.pack(fill=tk.X)

        tk.Label(hex_entry_frame, text="#", fg="#888888", bg="#444444", font=("Arial", 10)).pack(side=tk.LEFT, padx=(5, 0))

        self.hex_var = tk.StringVar()
        self.hex_entry = tk.Entry(
            hex_entry_frame,
            textvariable=self.hex_var,
            width=8,
            font=("Consolas", 10),
            bg="#444444",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            borderwidth=5
        )
        self.hex_entry.pack(side=tk.LEFT, pady=2)
        self.hex_entry.bind("<Return>", self._on_hex_change)
        self.hex_entry.bind("<FocusOut>", self._on_hex_change)

        # RGB values display
        rgb_frame = tk.Frame(input_frame, bg="#2d2d2d")
        rgb_frame.pack(fill=tk.X, pady=(10, 0))

        self.rgb_label = tk.Label(rgb_frame, text="R: 255  G: 255  B: 255", fg="#666666", bg="#2d2d2d", font=("Arial", 8))
        self.rgb_label.pack(anchor=tk.W)

        # Recent colors
        if self.recent_colors:
            recent_frame = tk.Frame(main_frame, bg="#2d2d2d")
            recent_frame.pack(fill=tk.X, pady=(15, 0))

            tk.Label(recent_frame, text="Recent", fg="#888888", bg="#2d2d2d", font=("Arial", 9)).pack(anchor=tk.W)

            colors_row = tk.Frame(recent_frame, bg="#2d2d2d")
            colors_row.pack(fill=tk.X, pady=(5, 0))

            for color in self.recent_colors[:10]:
                btn = tk.Canvas(colors_row, width=20, height=20, highlightthickness=1, highlightbackground="#555555", cursor="hand2")
                btn.pack(side=tk.LEFT, padx=2)
                btn.create_rectangle(0, 0, 20, 20, fill=color, outline="")
                btn.bind("<Button-1>", lambda e, c=color: self._select_recent(c))

        # Buttons
        btn_frame = tk.Frame(main_frame, bg="#2d2d2d")
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            bg="#444444",
            fg="#cccccc",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=self._on_ok,
            bg="#3a6ea5",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        ok_btn.pack(side=tk.RIGHT)

        self._update_preview()

    def _draw_color_wheel(self):
        """Draw the hue wheel."""
        self.wheel_image = tk.PhotoImage(width=self.wheel_size, height=self.wheel_size)
        cx, cy = self.wheel_radius, self.wheel_radius

        for y in range(self.wheel_size):
            row_colors = []
            for x in range(self.wheel_size):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx*dx + dy*dy)

                if self.wheel_inner_radius <= dist <= self.wheel_radius:
                    angle = math.atan2(dy, dx)
                    hue = (angle + math.pi) / (2 * math.pi)
                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                    color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                    row_colors.append(color)
                else:
                    row_colors.append("#2d2d2d")

            self.wheel_image.put("{" + " ".join(row_colors) + "}", to=(0, y))

        self.wheel_canvas.create_image(0, 0, image=self.wheel_image, anchor=tk.NW)

    def _draw_sv_square(self):
        """Draw the saturation/value square for current hue."""
        self.sv_image = tk.PhotoImage(width=self.sv_size, height=self.sv_size)

        for y in range(self.sv_size):
            row_colors = []
            val = 1.0 - (y / self.sv_size)
            for x in range(self.sv_size):
                sat = x / self.sv_size
                r, g, b = colorsys.hsv_to_rgb(self.current_hue, sat, val)
                color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                row_colors.append(color)
            self.sv_image.put("{" + " ".join(row_colors) + "}", to=(0, y))

        self.sv_canvas.delete("all")
        self.sv_canvas.create_image(0, 0, image=self.sv_image, anchor=tk.NW)

    def _update_indicators(self):
        """Update the position indicators on wheel and SV square."""
        # Wheel indicator
        self.wheel_canvas.delete("indicator")
        angle = self.current_hue * 2 * math.pi - math.pi
        mid_radius = (self.wheel_inner_radius + self.wheel_radius) / 2
        ix = self.wheel_radius + mid_radius * math.cos(angle)
        iy = self.wheel_radius + mid_radius * math.sin(angle)

        self.wheel_canvas.create_oval(
            ix - 6, iy - 6, ix + 6, iy + 6,
            outline="#ffffff", width=2, tags="indicator"
        )
        self.wheel_canvas.create_oval(
            ix - 5, iy - 5, ix + 5, iy + 5,
            outline="#000000", width=1, tags="indicator"
        )

        # SV indicator
        self.sv_canvas.delete("indicator")
        sx = self.current_sat * self.sv_size
        sy = (1.0 - self.current_val) * self.sv_size

        # Use contrasting color for indicator
        indicator_color = "#ffffff" if self.current_val < 0.5 else "#000000"
        self.sv_canvas.create_oval(
            sx - 6, sy - 6, sx + 6, sy + 6,
            outline=indicator_color, width=2, tags="indicator"
        )

    def _update_preview(self):
        """Update the color preview and hex display."""
        hex_color = self._get_hex()
        self.new_preview.delete("all")
        self.new_preview.create_rectangle(0, 0, 50, 30, fill=hex_color, outline="")

        # Update hex entry
        self.hex_var.set(hex_color[1:])

        # Update RGB label
        r, g, b = self._get_rgb()
        self.rgb_label.config(text=f"R: {r}  G: {g}  B: {b}")

    def _get_rgb(self):
        """Get current color as RGB tuple."""
        r, g, b = colorsys.hsv_to_rgb(self.current_hue, self.current_sat, self.current_val)
        return int(r * 255), int(g * 255), int(b * 255)

    def _get_hex(self):
        """Get current color as hex string."""
        r, g, b = self._get_rgb()
        return f"#{r:02x}{g:02x}{b:02x}"

    def _set_color_from_hex(self, hex_color):
        """Set HSV values from hex color."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            self.current_hue = h
            self.current_sat = s
            self.current_val = v

    def _on_wheel_click(self, event):
        """Handle click on color wheel."""
        cx, cy = self.wheel_radius, self.wheel_radius
        dx = event.x - cx
        dy = event.y - cy
        dist = math.sqrt(dx*dx + dy*dy)

        if self.wheel_inner_radius <= dist <= self.wheel_radius:
            angle = math.atan2(dy, dx)
            self.current_hue = (angle + math.pi) / (2 * math.pi)
            self._draw_sv_square()
            self._update_indicators()
            self._update_preview()

    def _on_sv_click(self, event):
        """Handle click on SV square."""
        x = max(0, min(event.x, self.sv_size))
        y = max(0, min(event.y, self.sv_size))

        self.current_sat = x / self.sv_size
        self.current_val = 1.0 - (y / self.sv_size)

        self._update_indicators()
        self._update_preview()

    def _on_hex_change(self, event=None):
        """Handle hex input change."""
        hex_val = self.hex_var.get().strip().lstrip("#")
        if len(hex_val) == 6:
            try:
                int(hex_val, 16)
                self._set_color_from_hex(hex_val)
                self._draw_sv_square()
                self._update_indicators()
                self._update_preview()
            except ValueError:
                pass

    def _select_recent(self, color):
        """Select a color from recent colors."""
        self._set_color_from_hex(color)
        self._draw_sv_square()
        self._update_indicators()
        self._update_preview()

    def _on_ok(self):
        """Confirm selection."""
        self.result = self._get_hex()
        self.destroy()

    def _on_cancel(self):
        """Cancel selection."""
        self.result = None
        self.destroy()

    @staticmethod
    def ask_color(parent, initial_color="#ffffff", title="Choose Color", recent_colors=None):
        """Static method to show picker and get result."""
        picker = ModernColorPicker(parent, initial_color, title, recent_colors)
        picker.wait_window()
        return picker.result


class KnittingDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("Knitting Pattern Designer")
        self.root.configure(bg="#2d2d2d")

        # Configuration
        self.grid_size = 64
        self.tile_size = 100# pixels per tile
        self.min_tile_size = 50
        self.max_tile_size = 200
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

        # Recent colors for color picker
        self.recent_colors = []
        self.max_recent_colors = 10

        # Selection state
        self.selection_start = None
        self.selection_end = None
        self.selection_rect_id = None
        self.is_selecting = False
        self.clipboard = None  # Stores copied/cut data as 2D list of colors

        # Mark mode state (for tracking completed stitches)
        self.mark_mode = False
        self.marked_tiles = set()  # Set of (row, col) tuples
        self.mark_ids = {}  # Maps (row, col) to canvas item IDs for the X marks

        self.setup_ui()
        self.load_settings()
        self.load_project()

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

        # Mark button (16th slot) - for tracking completed stitches
        mark_frame = tk.Frame(color_frame, bg="#2d2d2d")
        mark_frame.pack(pady=2)

        self.mark_button = tk.Button(
            mark_frame,
            text="X",
            width=3,
            height=1,
            bg="#555555",
            fg="#ff6666",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            borderwidth=2,
            highlightthickness=2,
            highlightbackground="#2d2d2d"
        )
        self.mark_button.pack(side=tk.LEFT, padx=(0, 5))
        self.mark_button.bind("<Button-1>", lambda e: self.toggle_mark_mode())

        mark_label = tk.Label(mark_frame, text="Mark", fg="#888888", bg="#2d2d2d", font=("Arial", 9))
        mark_label.pack(side=tk.LEFT)

        # Instructions
        instructions = tk.Label(
            color_frame,
            text="Left-click: Paint\nRight-drag: Select\nCtrl+C/X/V: Copy/Cut/Paste\nCtrl+Z: Undo\nScroll: Zoom\nEsc: Deselect",
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

        # Header size
        self.header_size = 20

        # Canvas with scrollbars using grid layout
        canvas_frame = tk.Frame(grid_frame, bg="#2d2d2d")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Corner spacer (top-left)
        corner = tk.Frame(canvas_frame, bg="#3d3d3d", width=self.header_size, height=self.header_size)
        corner.grid(row=0, column=0, sticky="nsew")

        # Column header canvas (top)
        self.col_header_canvas = tk.Canvas(
            canvas_frame,
            height=self.header_size,
            bg="#3d3d3d",
            highlightthickness=0
        )
        self.col_header_canvas.grid(row=0, column=1, sticky="ew")

        # Row header canvas (left)
        self.row_header_canvas = tk.Canvas(
            canvas_frame,
            width=self.header_size,
            bg="#3d3d3d",
            highlightthickness=0
        )
        self.row_header_canvas.grid(row=1, column=0, sticky="ns")

        # Main canvas
        canvas_size = self.grid_size * self.tile_size
        self.canvas = tk.Canvas(
            canvas_frame,
            width=min(640, canvas_size),
            height=min(640, canvas_size),
            bg="#3d3d3d",
            highlightthickness=0
        )
        self.canvas.grid(row=1, column=1, sticky="nsew")

        # Scrollbars
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self._on_h_scroll)
        h_scroll.grid(row=2, column=1, sticky="ew")

        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self._on_v_scroll)
        v_scroll.grid(row=1, column=2, sticky="ns")

        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        # Configure grid weights for resizing
        canvas_frame.grid_rowconfigure(1, weight=1)
        canvas_frame.grid_columnconfigure(1, weight=1)

        # Set scroll region
        self.canvas.config(scrollregion=(0, 0, canvas_size, canvas_size))
        self.col_header_canvas.config(scrollregion=(0, 0, canvas_size, self.header_size))
        self.row_header_canvas.config(scrollregion=(0, 0, self.header_size, canvas_size))

        # Draw initial grid
        self.draw_grid()

        # Bind events - Left click for painting
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Right click for selection
        self.canvas.bind("<Button-3>", self.on_selection_start)
        self.canvas.bind("<B3-Motion>", self.on_selection_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_selection_end)

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

        # Copy/Cut/Paste shortcuts
        self.root.bind("<Control-c>", self.copy_selection)
        self.root.bind("<Control-C>", self.copy_selection)
        self.root.bind("<Control-x>", self.cut_selection)
        self.root.bind("<Control-X>", self.cut_selection)
        self.root.bind("<Control-v>", self.paste_selection)
        self.root.bind("<Control-V>", self.paste_selection)
        self.root.bind("<Control-s>", self.save_project)
        self.root.bind("<Control-S>", self.save_project)
        self.root.bind("<Escape>", self.clear_selection)

    def _on_h_scroll(self, *args):
        """Handle horizontal scrolling - sync main canvas and column header."""
        self.canvas.xview(*args)
        self.col_header_canvas.xview(*args)

    def _on_v_scroll(self, *args):
        """Handle vertical scrolling - sync main canvas and row header."""
        self.canvas.yview(*args)
        self.row_header_canvas.yview(*args)

    def _col_to_excel(self, col):
        """Convert column number to Excel-style letter (0=A, 25=Z, 26=AA, etc.)."""
        result = ""
        col += 1  # 1-indexed
        while col > 0:
            col -= 1
            result = chr(ord('A') + col % 26) + result
            col //= 26
        return result

    def draw_headers(self):
        """Draw row and column headers."""
        # Clear existing headers
        self.col_header_canvas.delete("all")
        self.row_header_canvas.delete("all")

        canvas_size = self.grid_size * self.tile_size

        # Update scroll regions
        self.col_header_canvas.config(scrollregion=(0, 0, canvas_size, self.header_size))
        self.row_header_canvas.config(scrollregion=(0, 0, self.header_size, canvas_size))

        # Determine font size based on tile size
        font_size = max(6, min(10, self.tile_size - 2))
        header_font = ("Arial", font_size)

        # Draw col headers (1, 2, 3, ...)
        for col in range(self.grid_size):
            x = col * self.tile_size + self.tile_size // 2
            label = str(col + 1)
            self.col_header_canvas.create_text(
                x, self.header_size // 2,
                text=label,
                fill="#888888",
                font=header_font
            )

        # Draw row headers (1, 2, 3, ...)
        for row in range(self.grid_size):
            y = row * self.tile_size + self.tile_size // 2
            label = str(row + 1)
            self.row_header_canvas.create_text(
                self.header_size // 2, y,
                text=label,
                fill="#888888",
                font=header_font
            )

    def draw_grid(self):
        """Draw the entire grid."""
        self.canvas.delete("all")
        self.selection_rect_id = None  # Reset since canvas was cleared
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

        # Draw headers
        self.draw_headers()

        # Redraw marks
        self.redraw_all_marks()

        # Redraw selection if active
        if self.selection_start and self.selection_end:
            self._draw_selection_rect()

    def select_color(self, index):
        """Select a color for painting."""
        self.selected_color_index = index
        self.mark_mode = False
        self.update_color_selection()

    def toggle_mark_mode(self):
        """Toggle mark mode for tracking completed stitches."""
        self.mark_mode = True
        self.selected_color_index = -1  # Deselect color
        self.update_color_selection()

    def edit_color(self, index):
        """Open color picker to edit a color slot."""
        color = ModernColorPicker.ask_color(
            self.root,
            initial_color=self.colors[index],
            title=f"Choose Color {index + 1}",
            recent_colors=self.recent_colors
        )
        if color:
            self.colors[index] = color
            self.color_buttons[index].configure(bg=color)
            # Add to recent colors
            if color in self.recent_colors:
                self.recent_colors.remove(color)
            self.recent_colors.insert(0, color)
            self.recent_colors = self.recent_colors[:self.max_recent_colors]
            self.save_settings()

    def update_color_selection(self):
        """Update visual indication of selected color."""
        for i, btn in enumerate(self.color_buttons):
            if i == self.selected_color_index:
                btn.configure(highlightbackground="#ffffff", highlightthickness=3)
            else:
                btn.configure(highlightbackground="#2d2d2d", highlightthickness=2)

        # Update mark button highlight
        if self.mark_mode:
            self.mark_button.configure(highlightbackground="#ffffff", highlightthickness=3)
        else:
            self.mark_button.configure(highlightbackground="#2d2d2d", highlightthickness=2)

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

    def toggle_mark(self, row, col):
        """Toggle the X mark on a tile."""
        if (row, col) in self.marked_tiles:
            # Remove mark
            self.marked_tiles.discard((row, col))
            if (row, col) in self.mark_ids:
                for item_id in self.mark_ids[(row, col)]:
                    self.canvas.delete(item_id)
                del self.mark_ids[(row, col)]
        else:
            # Add mark
            self.marked_tiles.add((row, col))
            self.draw_mark(row, col)

    def draw_mark(self, row, col):
        """Draw an X mark on the specified tile."""
        x1 = col * self.tile_size
        y1 = row * self.tile_size
        x2 = x1 + self.tile_size
        y2 = y1 + self.tile_size

        # Padding from edges
        padding = max(2, self.tile_size // 6)

        # Draw X with two lines
        line1 = self.canvas.create_line(
            x1 + padding, y1 + padding,
            x2 - padding, y2 - padding,
            fill="#ff0000", width=max(2, self.tile_size // 20), tags="mark"
        )
        line2 = self.canvas.create_line(
            x2 - padding, y1 + padding,
            x1 + padding, y2 - padding,
            fill="#ff0000", width=max(2, self.tile_size // 20), tags="mark"
        )
        self.mark_ids[(row, col)] = [line1, line2]

    def redraw_all_marks(self):
        """Redraw all X marks (called after zoom or grid redraw)."""
        # Clear existing mark canvas items
        self.canvas.delete("mark")
        self.mark_ids.clear()

        # Redraw all marks
        for row, col in self.marked_tiles:
            self.draw_mark(row, col)

    def on_canvas_click(self, event):
        """Handle canvas click."""
        pos = self.get_tile_at(event)
        if not pos:
            return

        if self.mark_mode:
            self.is_dragging = True
            # Determine if we're adding or removing marks based on first tile
            self.mark_adding = (pos[0], pos[1]) not in self.marked_tiles
            self.toggle_mark(*pos)
        else:
            self.is_dragging = True
            self.current_stroke = []
            self.paint_tile(*pos)

    def on_canvas_drag(self, event):
        """Handle canvas drag for continuous painting/marking."""
        if not self.is_dragging:
            return
        pos = self.get_tile_at(event)
        if not pos:
            return

        if self.mark_mode:
            # Add or remove marks based on initial click action
            is_marked = (pos[0], pos[1]) in self.marked_tiles
            if self.mark_adding and not is_marked:
                self.toggle_mark(*pos)
            elif not self.mark_adding and is_marked:
                self.toggle_mark(*pos)
        else:
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

            # Redraw grid (includes headers)
            self.draw_grid()

            # Update scroll region
            canvas_size = self.grid_size * self.tile_size
            self.canvas.config(scrollregion=(0, 0, canvas_size, canvas_size))
            self.col_header_canvas.config(scrollregion=(0, 0, canvas_size, self.header_size))
            self.row_header_canvas.config(scrollregion=(0, 0, self.header_size, canvas_size))

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

    # Selection methods
    def on_selection_start(self, event):
        """Start selection with right-click."""
        self.clear_selection()
        pos = self.get_tile_at(event)
        if pos:
            self.selection_start = pos
            self.is_selecting = True

    def on_selection_drag(self, event):
        """Update selection rectangle while dragging."""
        if not self.is_selecting or not self.selection_start:
            return

        pos = self.get_tile_at(event)
        if pos:
            self.selection_end = pos
            self._draw_selection_rect()

    def on_selection_end(self, event):
        """Finalize selection on mouse release."""
        if not self.is_selecting:
            return

        self.is_selecting = False
        pos = self.get_tile_at(event)
        if pos:
            self.selection_end = pos
            self._draw_selection_rect()

    def _draw_selection_rect(self):
        """Draw or update the selection rectangle."""
        if self.selection_rect_id:
            for rect_id in self.selection_rect_id:
                self.canvas.delete(rect_id)
            self.selection_rect_id = None

        if not self.selection_start or not self.selection_end:
            return

        # Get normalized bounds
        r1, c1 = self.selection_start
        r2, c2 = self.selection_end
        min_row, max_row = min(r1, r2), max(r1, r2)
        min_col, max_col = min(c1, c2), max(c1, c2)

        # Calculate pixel coordinates
        x1 = min_col * self.tile_size
        y1 = min_row * self.tile_size
        x2 = (max_col + 1) * self.tile_size
        y2 = (max_row + 1) * self.tile_size

        # Draw selection rectangle with thick, visible border
        # Create multiple rectangles for a "marching ants" style effect
        self.selection_rect_id = []

        # Outer glow/shadow (dark)
        outer = self.canvas.create_rectangle(
            x1 - 1, y1 - 1, x2 + 1, y2 + 1,
            outline="#000000",
            width=3
        )
        self.selection_rect_id.append(outer)

        # Main selection rectangle (bright cyan, thick)
        main = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#00ffff",
            width=4,
            dash=(8, 4)
        )
        self.selection_rect_id.append(main)

        # Inner highlight (white dashed, offset)
        inner = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#ffffff",
            width=2,
            dash=(4, 8),
            dashoffset=6
        )
        self.selection_rect_id.append(inner)

    def clear_selection(self, _event=None):
        """Clear the current selection."""
        if self.selection_rect_id:
            for rect_id in self.selection_rect_id:
                self.canvas.delete(rect_id)
            self.selection_rect_id = None
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False

    def _get_selection_bounds(self):
        """Get normalized selection bounds (min_row, min_col, max_row, max_col)."""
        if not self.selection_start or not self.selection_end:
            return None

        r1, c1 = self.selection_start
        r2, c2 = self.selection_end
        return min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2)

    def copy_selection(self, _event=None):
        """Copy the selected region to clipboard."""
        bounds = self._get_selection_bounds()
        if not bounds:
            return

        min_row, min_col, max_row, max_col = bounds

        # Copy colors from selection to clipboard
        self.clipboard = []
        for row in range(min_row, max_row + 1):
            row_data = []
            for col in range(min_col, max_col + 1):
                row_data.append(self.grid_data[row][col])
            self.clipboard.append(row_data)

    def cut_selection(self, _event=None):
        """Cut the selected region (copy + clear)."""
        bounds = self._get_selection_bounds()
        if not bounds:
            return

        # First copy
        self.copy_selection()

        min_row, min_col, max_row, max_col = bounds

        # Record for undo
        undo_data = []
        default_color = "#f5f5f5"

        # Clear the selection area
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                old_color = self.grid_data[row][col]
                if old_color != default_color:
                    undo_data.append((row, col, old_color))
                    self.grid_data[row][col] = default_color
                    self.canvas.itemconfig(self.tile_ids[row][col], fill=default_color)

        if undo_data:
            self.undo_history.append(undo_data)
            if len(self.undo_history) > self.max_undo:
                self.undo_history.pop(0)

    def paste_selection(self, _event=None):
        """Paste clipboard content at current selection start."""
        if not self.clipboard:
            return

        # Paste at selection start, or at (0,0) if no selection
        if self.selection_start:
            start_row, start_col = self.selection_start
        else:
            start_row, start_col = 0, 0

        # Record for undo
        undo_data = []

        # Paste the clipboard data
        for row_offset, row_data in enumerate(self.clipboard):
            for col_offset, color in enumerate(row_data):
                target_row = start_row + row_offset
                target_col = start_col + col_offset

                # Check bounds
                if 0 <= target_row < self.grid_size and 0 <= target_col < self.grid_size:
                    old_color = self.grid_data[target_row][target_col]
                    if old_color != color:
                        undo_data.append((target_row, target_col, old_color))
                        self.grid_data[target_row][target_col] = color
                        self.canvas.itemconfig(self.tile_ids[target_row][target_col], fill=color)

        if undo_data:
            self.undo_history.append(undo_data)
            if len(self.undo_history) > self.max_undo:
                self.undo_history.pop(0)

        # Update selection to show pasted area
        if self.selection_start:
            paste_height = len(self.clipboard)
            paste_width = len(self.clipboard[0]) if self.clipboard else 0
            self.selection_end = (
                min(start_row + paste_height - 1, self.grid_size - 1),
                min(start_col + paste_width - 1, self.grid_size - 1)
            )
            self._draw_selection_rect()

    def save_settings(self):
        """Save color presets to file."""
        settings = {
            "colors": self.colors,
            "recent_colors": self.recent_colors
        }
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
                if "recent_colors" in settings:
                    self.recent_colors = settings["recent_colors"][:self.max_recent_colors]
        except Exception:
            pass

    def save_project(self, _event=None):
        """Save the current project (grid data and marks) to file."""
        project = {
            "grid_size": self.grid_size,
            "grid_data": self.grid_data,
            "marked_tiles": list(self.marked_tiles)  # Convert set to list for JSON
        }
        project_path = os.path.join(os.path.dirname(__file__), "knitting_project.json")
        try:
            with open(project_path, "w") as f:
                json.dump(project, f)
        except Exception:
            pass

    def load_project(self):
        """Load the project (grid data and marks) from file."""
        project_path = os.path.join(os.path.dirname(__file__), "knitting_project.json")
        try:
            with open(project_path, "r") as f:
                project = json.load(f)
                if "grid_data" in project:
                    loaded_grid = project["grid_data"]
                    # Copy data, respecting current grid size
                    for row in range(min(len(loaded_grid), self.grid_size)):
                        for col in range(min(len(loaded_grid[row]), self.grid_size)):
                            self.grid_data[row][col] = loaded_grid[row][col]
                if "marked_tiles" in project:
                    # Convert list back to set of tuples
                    self.marked_tiles = set(tuple(tile) for tile in project["marked_tiles"])
                # Redraw grid with loaded data
                self.draw_grid()
        except Exception:
            pass


def main():
    root = tk.Tk()
    root.minsize(800, 700)
    # Maximize window on startup
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    app = KnittingDesigner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
