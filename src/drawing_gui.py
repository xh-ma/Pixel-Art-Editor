from __future__ import annotations
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, colorchooser
from datetime import datetime
from PIL import Image
import math
import copy

from canvas import Canvas, load_canvas, blank_canvas
from layer import Layer


DEFAULT_CANVAS_SIZE = 512
DEFAULT_BLANK_CANVAS_SIZE = 16
DEFAULT_NUM_LAYERS = 4
DEFAULT_LOAD_CANVAS_SIZE = 64

FONT_NAME = "Press Start 2P"
FONT = (FONT_NAME, 10, "bold")

BTN_STYLE = {
    "font": FONT,
    "bg": "white",
    "fg": "black",
    "activebackground": "#ddd",
    "activeforeground": "black",
    "borderwidth": 4,
    "relief": "solid",
    "padx": 5,
    "pady": 2
}

SMALL_BTN_STYLE = BTN_STYLE.copy()
SMALL_BTN_STYLE.update({
    "font": (FONT_NAME, 8),   # smaller font
    "width": 2,               # small fixed width
    "height": 1,              # small fixed height
    "padx": 0,                # tighter padding
    "pady": 0,
    "borderwidth": 1,         # thin border
    "relief": "flat",         # flat look (no heavy outline)
    "highlightthickness": 0   # remove focus highlight border
})


class WindowTracker:
    """A class for tracking the number of windows created.

    Attributes:
        - num_windows: the number of windows created
        - active_windows: a list of all active DrawingGUIs.
    """
    num_windows: int
    active_windows: list[tuple[DrawingGUI, tk.Tk]]

    def __init__(self) -> None:
        """Initialize this WindowTracker with 0 windows.
        """
        self.num_windows = 0
        self.active_windows = []

    def add(self, to_add: DrawingGUI, root: tk.Tk) -> None:
        """Add to_add to this WindowTracker.
        """
        self.num_windows += 1
        self.active_windows.append((to_add, root))

    def remove(self, to_remove: DrawingGUI) -> None:
        """Remove to_remove from the GUI. If there are no windows left,
        exits the program.
        """
        i = 0
        while i < len(self.active_windows) and self.active_windows[i][0] != to_remove:
            i += 1
        gui, root = self.active_windows.pop(i)

        self.num_windows -= 1
        if self.num_windows == 0:
            root.destroy()
            exit()


WINDOWS = WindowTracker()


def interpolate(start: tuple[int, int],
                end: tuple[int, int]) -> list[tuple[int, int]]:
    """
    Return a list of coordinates between the point <start> and point <end>.
    """
    # Use Bresenham's line algorithm for better performance
    x1, y1 = start
    x2, y2 = end
    
    # If points are the same, return just the endpoints
    if x1 == x2 and y1 == y2:
        return [start, end]
    
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
    
    return points


def canvas_from_png(path: str) -> Canvas:
    """
    Return a Canvas instance from the given <path>.

    The name of the resulting canvas will be the <path> but with the '.png'
    extension replaced with '_pixel_art'. This is to prevent the user from
    accidentally overwriting the original <path>.

    Preconditions:
    - path.endswith('.png')
    """
    image = Image.open(path)
    size = DEFAULT_LOAD_CANVAS_SIZE
    if image.width == image.height and \
            int(math.log2(image.width)) == math.log2(image.width):
        scaled = image
        size = image.width
    else:
        scaled = image.resize((size, size), 5).convert('RGBA')

    c = Canvas((size, size))

    layer = Layer((size, size))
    for x in range(size):
        for y in range(size):
            color = scaled.getpixel((x, y))
            if color == 255:
                color = (0, 0, 0, 0)
            layer.get_pixel((x, y)).rgb = color[:-1]
            if color[-1] == 0:
                layer.get_pixel((x, y)).rgb = None
    c.add_layer(layer)
    return c


def _load_image() -> None:
    """Prompt users for a filename and open the given image.
    """
    name = filedialog.askopenfilename()
    # Open the new image in another window
    DrawingGUI(name)


def _new_image() -> None:
    """Create a GUI for a new image.
    """
    DrawingGUI(num_layers=DEFAULT_NUM_LAYERS)


class DrawingGUI:
    """
    A GUI for drawing pixel art.

    Attributes:
        - last_updated_position: The last position that was drawn.
        - file_name: The name of the canvas/image being drawn on.
        - canvas_size: The dimensions of the image (i.e. the number of pixels)
        - viewport_size: The size of the drawing area in the gui.
        - colour: The hex code of the currently active colour or None if
                  transparent.
        - recent_colours: A list of the most recently used colours.
        - _canvas: The Canvas for that this DrawingGUI uses,
        - _total_layers: The total number of layers that have been created
                         in this canvas.
        - _current_tool: The name of the current tool being used.
        - _undo_stack: A stack of actions that can be undone.
        - _redo_stack: A stack of actions that can be redone.
    """
    last_updated_position: None | tuple[int, int]
    file_name: str
    canvas_size: int
    viewport_size: int
    colour: str | None
    recent_colours: list[str]
    _canvas: Canvas
    _total_layers: int
    _current_tool: str
    _undo_stack: list[tuple[str, dict]]
    _redo_stack: list[tuple[str, dict]]

    def __init__(self, file_name: str = None,
                 canvas_size: int = DEFAULT_CANVAS_SIZE,
                 num_layers: int = DEFAULT_NUM_LAYERS) -> None:
        """Initialize a DrawingGUI using the image at <file_name> if provided,
        with size <canvas_size> and <num_layers> layers.

        Preconditions:
        - canvas_size[0] > 0 and canvas_size[1] > 0
        - num_layers > 0
        """
        original_root = tk.Tk()
        self._root = tk.Toplevel()  
        original_root.withdraw()
        WINDOWS.add(self, original_root)
        self.last_updated_position = None

        self._root.protocol("WM_DELETE_WINDOW", self._close)
        self._root.config(bg='white')
        self._root.wm_title('Pixel Art!')

        if not file_name:
            file_name = "untitled"
            self._canvas = blank_canvas(DEFAULT_BLANK_CANVAS_SIZE,
                                        DEFAULT_BLANK_CANVAS_SIZE,
                                        num_layers)
        elif file_name.endswith(".png"):
            self._canvas = canvas_from_png(file_name)
            file_name = file_name[:-4]
        elif file_name.endswith(".canvas"):
            self._canvas = load_canvas(file_name)
            file_name = file_name[:-7]

        self._canvas.set_active_layer_index(0)
        self._total_layers = self._canvas.get_num_layers()
        self.file_name = file_name
        self.canvas_size = self._canvas.size[0]
        self.viewport_size = max(canvas_size, self.canvas_size)
        self.colour = "#000000"
        self.recent_colours = []
        self.max_recent_colours = 10
        self._initialize_gui_components(canvas_size)

        self._current_tool = "Brush"
        self._set_current_tool(self._current_tool)

        self._undo_stack = []
        self._redo_stack = []

        # Update all views and controls
        self._update_view_canvas()
        self._update_edit_canvas()
        self.reset_layer_controllers()

        self._root.mainloop()

    def _initialize_gui_components(self, canvas_size) -> None:
        """Initialize the GUI components for this DrawingGUI.  
        """
         # LEFT PANEL (Toolbar + Current tool display)
        self._toolbar_frame = tk.Frame(self._root, bg="white", padx=5, pady=5)
        self._toolbar_frame.grid(row=0, column=0, rowspan=2, sticky="ns")  # spans both rows

        self._color_tk_canvas = tk.Canvas(self._toolbar_frame, width=20, height=20, bg="white", highlightthickness=1, highlightbackground="black")
        self._color_tk_canvas.pack(pady=(0, 10))
        self._color_tk_canvas.create_rectangle(0, 0, 20, 20, fill=self.colour, outline='black')

        # Current tool display
        self._current_tool_label = tk.Label(self._toolbar_frame, text="Current Tool: Brush",
                                            font=FONT, bg="white")
        self._current_tool_label.pack(pady=(0,10))
    
        # Toolbar buttons
        tk.Button(self._toolbar_frame, text="Colour", command=lambda: self._select_tool("Brush"), **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Eraser", command=lambda: self._select_tool("Eraser"), **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Save as .png", command=self._save_png, **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Save as .canvas", command=self._save_canvas, **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Load", command=_load_image, **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="New Canvas", command=_new_image, **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Upscale", command=self._refine, **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Downscale", command=self._coarsen, **BTN_STYLE).pack(pady=5, fill="x")
        tk.Button(self._toolbar_frame, text="Add Layer", command=self.add_layer, **BTN_STYLE).pack(pady=5, fill="x")

        #3self._layers_frame = tk.Frame(self._root, bg="white")
        # self._layers_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        self._layers_panel_container = tk.Frame(
            self._root,
            bg="white",
            bd=BTN_STYLE["borderwidth"],
            relief=BTN_STYLE["relief"],
            highlightbackground="black",
            highlightthickness=2,
            padx=BTN_STYLE["padx"],
            pady=BTN_STYLE["pady"]
        )

        self._layers_panel_container.grid(row=2, column=0, sticky="ns", pady=10)

        self._layers_canvas = tk.Canvas(self._layers_panel_container, bg="#ffffff", height=120, highlightthickness=0)
        self._layers_scrollbar = tk.Scrollbar(self._layers_panel_container, orient="vertical", command=self._layers_canvas.yview)
        self._layers_frame = tk.Frame(self._layers_canvas, bg="#ffffff")

        self._layers_frame.bind(
            "<Configure>",
            lambda e: self._layers_canvas.configure(
                scrollregion=self._layers_canvas.bbox("all")
            )
        )

        self._layers_canvas.create_window((0, 0), window=self._layers_frame, anchor="nw")
        self._layers_canvas.configure(yscrollcommand=self._layers_scrollbar.set)

        self._layers_canvas.pack(side="left", fill="both")
        self._layers_scrollbar.pack(side="right", fill="y")

        self._recent_colours_frame = tk.Frame(self._toolbar_frame, bg="white")
        self._recent_colours_frame.pack(pady=(10, 0))
        tk.Label(self._recent_colours_frame, text="Recent Colours:", bg="white", font=FONT).pack(anchor="w")
        self._recent_colours_squares = tk.Frame(self._recent_colours_frame, bg="white")
        self._recent_colours_squares.pack()

        # Undo/Redo
        undo_redo_frame = tk.Frame(self._toolbar_frame, bg="white")
        undo_redo_frame.pack(pady=5)
        small_btn_style = BTN_STYLE.copy()
        small_btn_style.update({"width": 2, "font": (FONT_NAME, 10, "bold")})

        tk.Button(undo_redo_frame, text="↶", command=self._undo, **small_btn_style).pack(side="left", padx=2)
        tk.Button(undo_redo_frame, text="↷", command=self._redo, **small_btn_style).pack(side="left", padx=2)
        self._root.bind('<Control-z>', lambda e: self._undo())
        self._root.bind('<Control-y>', lambda e: self._redo())

        # VIEW CANVAS (smaller, top-right)
        preview_size = canvas_size // 4
        self._view_canvas = tk.Canvas(self._root, width=preview_size, height=preview_size,
                                    bg="#111111", highlightthickness=4, highlightbackground="black")
        self._preview_size = preview_size
        self._view_img = tk.PhotoImage(width=preview_size, height=preview_size)
        self._view_canvas.create_image(preview_size//2, preview_size//2, image=self._view_img)
        self._view_canvas.grid(row=0, column=1, padx=5, pady=5, sticky="ne")

        # EDIT CANVAS (main canvas, below preview)
        # Create a frame to hold the edit canvas and scrollbars
        self._edit_canvas_frame = tk.Frame(self._root)
        self._edit_canvas_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self._edit_canvas_frame.rowconfigure(0, weight=1)
        self._edit_canvas_frame.columnconfigure(0, weight=1)


        self._edit_canvas = tk.Canvas(
            self._edit_canvas_frame,
            width = self.viewport_size,
            height = self.viewport_size,
            bg="#111111", highlightthickness=4, highlightbackground="black",
            scrollregion=(0, 0, self.canvas_size, self.canvas_size)
        )
        self._edit_img = tk.PhotoImage(width=self.viewport_size, height=self.viewport_size)
        self._edit_canvas.create_image(0, 0, anchor="nw", image=self._edit_img)

        # Add scrollbars
        self._edit_xscroll = tk.Scrollbar(self._edit_canvas_frame, orient="horizontal", command=self._edit_canvas.xview)
        self._edit_yscroll = tk.Scrollbar(self._edit_canvas_frame, orient="vertical", command=self._edit_canvas.yview)
        self._edit_canvas.configure(xscrollcommand=self._edit_xscroll.set, yscrollcommand=self._edit_yscroll.set)

        # Grid everything
        self._edit_canvas.grid(row=0, column=0, sticky="nsew")
        self._edit_yscroll.grid(row=0, column=1, sticky="ns")
        self._edit_xscroll.grid(row=1, column=0, sticky="ew")

        # Bindings
        self._edit_canvas.bind("<ButtonRelease-1>", self._on_up)
        self._view_canvas.bind("<ButtonRelease-1>", self._on_up)
        self._edit_canvas.bind("<B1-Motion>", self._on_drag)
        self._view_canvas.bind("<B1-Motion>", self._on_drag)

        # Make canvas expand with window
        self._root.grid_rowconfigure(1, weight=1)
        self._root.grid_columnconfigure(1, weight=1)

    
    def _push_undo(self):
        """Push the current canvas state onto the undo stack and clear redo stack.
        """
        self._undo_stack.append(copy.deepcopy(self._canvas))
        self._redo_stack.clear()
    
    def _set_current_tool(self, tool_name) -> None:
        """Set the current tool label to the given <tool_name>."""
        if not isinstance(tool_name, str):
            raise ValueError("Tool name must be a string.")
        # Update the label to reflect the current tool
        self._current_tool_label.config(text=f"Current Tool: {tool_name}")
    
    def _select_tool(self, tool_name: str) -> None:
        """Set the current tool and update the label."""
        self._current_tool = tool_name
        self._set_current_tool(tool_name)
        if tool_name == "Brush":
            self._choose_colour()
        elif tool_name == "Eraser":
            self.set_transparent()

    def set_transparent(self) -> None:
        """Set self.colour to None and update the GUI accordingly.
        """
        if self.colour is not None:
            self.colour = None

            # Draw a box representing our 'transparent' colour
            c1 = '#aaaaaa'
            c2 = '#666666'
            self._color_tk_canvas.delete(tk.ALL)
            self._color_tk_canvas.create_rectangle(0, 0, 10, 10, fill=c1, outline='black')
            self._color_tk_canvas.create_rectangle(10, 10, 20, 20, fill=c1, outline='black')
            self._color_tk_canvas.create_rectangle(0, 10, 10, 20, fill=c2, outline='black')
            self._color_tk_canvas.create_rectangle(10, 0, 20, 10, fill=c2, outline='black')
            
    def _close(self) -> None:
        """Close this drawing GUI."""
        self._root.destroy()
        WINDOWS.remove(self)

    def _choose_colour(self) -> None:
        """Prompt users for a colour and update self.colour
        """
        colour_code = colorchooser.askcolor(title="Choose color")

        if colour_code and colour_code[0] is not None:
            self.colour = colour_code[1]
            if self.colour and self.colour not in self.recent_colours:
                self.recent_colours.insert(0, self.colour)
                if len(self.recent_colours) > self.max_recent_colours:
                    self.recent_colours.pop()
                self._update_recent_colours_palette()
    
            # Update the display
            self._color_tk_canvas.delete(tk.ALL)
            self._color_tk_canvas.create_rectangle(0, 0, 20, 20,
                                                   fill=self.colour,
                                                   outline='black')
    
    def _update_recent_colours_palette(self) -> None:
        """Update the recent colours palette in the GUI."""
        # Clear the current palette
        for widget in self._recent_colours_squares.winfo_children():
            widget.destroy()

        # Add each recent colour as a square
        for colour in self.recent_colours:
            btn = tk.Button(self._recent_colours_squares, bg=colour, width=2, height=1,
                            command=lambda c=colour: self._set_colour_from_palette(c))
            btn.pack(side="left", padx=2)

    def _set_colour_from_palette(self, colour: str) -> None:
        """Set the current colour from the recent colours palette."""
        self.colour = colour
        self._current_tool = "Brush"
        self._set_current_tool("Brush")
        self._color_tk_canvas.delete(tk.ALL)
        self._color_tk_canvas.create_rectangle(0, 0, 20, 20,
                                               fill=self.colour,
                                               outline='black')

    def _save_png(self) -> None:
        """Save this canvas to a png in a user-choosen location."""
        # add timestamp
        current_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = self.file_name + current_timestamp + '.png'
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            initialfile=filename,
            title="Save as .png"
        )
        if file_path:
            self._canvas.save(file_path)

    def _save_canvas(self) -> None:
        """Save this canvas to a .canvas"""
        current_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = self.file_name + current_timestamp + '.canvas'
        file_path = filedialog.asksaveasfilename(
            defaultextension=".canvas",
            filetypes=[("Canvas files", "*.canvas")],
            initialfile=filename,
            title="Save as .canvas"
        )
        if file_path:
            self._canvas.save(file_path)

    def _on_up(self, event) -> None:
        """Handle the mouse-click release event <event>. Changes the colour
        of the pixel clicked on to self.colour.
        Sets last_updated_position to None.
        """
        self._on_drag(event)
        self.last_updated_position = None

    def _on_drag(self, event) -> None:
        """Handle the drag event <event>, setting all pixels dragged across
         to self.colour.
        """
        # Get the canvas coordinates (accounting for scrolling)
        canvas_x = int(self._edit_canvas.canvasx(event.x))
        canvas_y = int(self._edit_canvas.canvasy(event.y))
        
        # Check bounds
        if not (0 <= canvas_x < self.viewport_size and 0 <= canvas_y < self.viewport_size):
            self.last_updated_position = None
            return
        
        # Calculate pixel coordinates
        square_size = self.viewport_size / self.canvas_size
        i = int(canvas_x // square_size)
        j = int(canvas_y // square_size)
        
        # If this is a new drag, push to undo stack
        if self.last_updated_position is None:
            self._push_undo()
        
        # Get current position
        current_position = (i, j)
        
        # If we have a previous position, interpolate
        if self.last_updated_position is not None and self.last_updated_position != current_position:
            positions_to_draw = interpolate(self.last_updated_position, current_position)
        else:
            positions_to_draw = [current_position]
        
        self.last_updated_position = current_position
        
        # Process all positions to draw
        for pos in positions_to_draw:
            i, j = pos
            
            # Set the pixel value
            if self._current_tool == "Eraser":
                self._canvas.get_active_layer().get_pixel((i, j)).set(None)
            else:
                self._canvas.get_active_layer().get_pixel((i, j)).set(self.colour)
            
            # Update the GUI for this pixel
            x1 = int(i * square_size)
            y1 = int(j * square_size)
            x2 = int((i + 1) * square_size)
            y2 = int((j + 1) * square_size)
            
            # Update edit canvas
            col = self._canvas.get_hex_rgb((i, j))
            self._draw_rectangle(True, col, x1, y1, x2, y2)
        
        # Only update the view canvas once at the end
        self._update_view_canvas()
    
    def _undo(self) -> None:
        """Undo the last action, if possible."""
        if self._undo_stack:
            self._redo_stack.append(copy.deepcopy(self._canvas))
            self._canvas = self._undo_stack.pop()
            self._update_edit_canvas()
            self._update_view_canvas()
            self.reset_layer_controllers()

    def _redo(self) -> None:
        """Redo the last undone action, if possible."""
        if self._redo_stack:
            self._undo_stack.append(copy.deepcopy(self._canvas))
            self._canvas = self._redo_stack.pop()
            self._update_edit_canvas()
            self._update_view_canvas()
            self.reset_layer_controllers()

    def _change_layer(self, index: int) -> None:
        """Change the active layer to the one at the given index.
        """
        self._canvas.set_active_layer_index(index)
        self._layer_button_var.set(index)
        self._update_edit_canvas()

    def _toggle_visible(self, index: int) -> None:
        """Toggle the visibility of the layer at the given index.
        """
        self._canvas.get_layer(index).visible = not self._canvas.get_layer(index).visible
        self._update_view_canvas()
        self._update_edit_canvas()

    def _delete_layer(self, k: int):
        """"Delete layer <k> from this canvas, updating the GUI accordingly."""
        # If there is only 1 layer, we do not delete layers.
        if self._canvas.get_num_layers() < 2:
            return
        self._canvas.remove_layer(self._canvas.get_layer(k))
        self.reset_layer_controllers()
        self._update_view_canvas()
        self._update_edit_canvas()
        

    def _lower_layer(self, k: int) -> None:
        """Move layer <k> down as needed, updating the GUI accordingly.
        """
        num_layers = self._canvas.get_num_layers()
        if k >= num_layers - 1:
            return
        
        self._canvas.move_layer(self._canvas.get_layer(k), -1)
        self.reset_layer_controllers()

        self._update_view_canvas()
        self._update_edit_canvas()

    def _raise_layer(self, k: int):
        """Move layer <k> up as needed, updating the GUI accordingly.
        """
        if k <= 0:
            return
        
        self._canvas.move_layer(self._canvas.get_layer(k), 1)
        self.reset_layer_controllers()

        self._update_view_canvas()
        self._update_edit_canvas()

    def reset_layer_controllers(self) -> None:
        """
        Reset the UI buttons for layers.
        This will re-render the move up/down, select, hide, remove buttons for
        each layer.
        """
            # Clear previous controls
        for widget in self._layers_frame.winfo_children():
            widget.destroy()

        num_layers = self._canvas.get_num_layers()
        
        # Use persistent layer selection variable
        if not hasattr(self, '_layer_button_var'):
            self._layer_button_var = tk.IntVar(value=self._canvas.active_layer_index)
        else:
            self._layer_button_var.set(self._canvas.active_layer_index)
        
        # Store the visibility variables as instance attributes so they persist
        if not hasattr(self, '_visibility_vars'):
            self._visibility_vars = []
        
        # Ensure we have enough visibility variables
        while len(self._visibility_vars) < num_layers:
            self._visibility_vars.append(tk.BooleanVar())
        
        for k in range(num_layers):
            # Set the correct visibility state
            self._visibility_vars[k].set(self._canvas.get_layer(k).visible)
            
            # Visibility checkbox
            checkbox = tk.Checkbutton(self._layers_frame, text='👁',
                                    variable=self._visibility_vars[k],
                                    command=lambda j=k: self._toggle_visible(j),
                                    bg="white")
            checkbox.grid(row=k, column=0, padx=2)

            # Layer select radio button - use persistent variable
            radiobutton = tk.Radiobutton(self._layers_frame,
                                        text=self._canvas.get_layer(k).name,
                                        variable=self._layer_button_var, 
                                        value=k,
                                        command=lambda j=k: self._change_layer(j),
                                        bg="white")
            radiobutton.grid(row=k, column=1, padx=2)
            
            # Move down button
            btn_down = tk.Button(self._layers_frame, text='↓',
                                command=lambda j=k: self._lower_layer(j), **SMALL_BTN_STYLE)
            btn_down.grid(row=k, column=2, padx=2)

            # Move up button
            btn_up = tk.Button(self._layers_frame, text='↑',
                            command=lambda j=k: self._raise_layer(j), **SMALL_BTN_STYLE)
            btn_up.grid(row=k, column=3, padx=2)

            # Delete button
            btn_delete = tk.Button(self._layers_frame, text='🗑',
                                command=lambda j=k: self._delete_layer(j), **SMALL_BTN_STYLE)
            btn_delete.grid(row=k, column=4, padx=2)

    def _refine(self) -> None:
        """
        Refine the canvas by doubling the number of pixels in each dimension.
        The maximum dimension is 64. If the dimension is already 64, do nothing.
        """
        if self.canvas_size >= 64:
            return
        self._push_undo()
        self.canvas_size *= 2
        self._canvas.upscale()
        self.viewport_size = max(self.viewport_size, self.canvas_size)
        self._edit_canvas.config(width=self.viewport_size, height=self.viewport_size,
                                 scrollregion=(0, 0, self.viewport_size, self.viewport_size))
        self._update_view_canvas()
        self._update_edit_canvas()
        self.reset_layer_controllers()

    def _coarsen(self) -> None:
        """
        Coarsen the canvas by halving the number of pixels in each dimension.
        The minimum dimension is 1. If the dimension is already 1, do nothing.
        """
        if self.canvas_size <= 1:
            return
        self._push_undo()
        self.canvas_size //= 2
        self._canvas.downscale()
        self.viewport_size = max(self.viewport_size, self.canvas_size)
        self._edit_canvas.config(width=self.viewport_size, height=self.viewport_size,
                                    scrollregion=(0, 0, self.viewport_size, self.viewport_size))
        self._update_view_canvas()
        self._update_edit_canvas()
        self.reset_layer_controllers()

    def add_layer(self) -> None:
        """
        Add a new layer to the canvas.
        Layer Controllers will be updated to reflect changed number of layers.
        """
        new_layer = Layer((self.canvas_size, self.canvas_size),
                          name=f'Layer {self._total_layers + 1}')
        self._total_layers += 1

        self._canvas.add_layer(new_layer)
        self.reset_layer_controllers()
        self._update_view_canvas()
        self._update_edit_canvas()

    def _update_edit_canvas(self) -> None:
        """
        Update the edit canvas (on the right side of the panel.)
        """
        # Calculate the size of each square in the grid
        self._edit_canvas.delete("grid_line")
        square_size = self.viewport_size / self.canvas_size
        n = self.canvas_size
        content_size = n * square_size
        self._edit_canvas.config(scrollregion=(0, 0, content_size, content_size))

        # Draw the grid
        for i in range(n):
            for j in range(n):
                self.draw_square(i, j, square_size, True)
        for i in range(n + 1):
            # horizontal lines
            y_pos = i * square_size
            self._edit_canvas.create_line(0, y_pos, content_size, y_pos, content_size,
                                          y_pos, fill="#000000", width=1, tags="grid_line")
            # vertical lines
            x_pos = i * square_size
            self._edit_canvas.create_line(x_pos, 0, x_pos, content_size, x_pos,
                                          content_size, fill="#000000", width=1, tags="grid_line")

    def _draw_rectangle(self, edit: bool, c: str | None, x1: int,
                        y1: int, x2: int, y2: int) -> None:
        """Draw a rectangle in the box from (<x1>, <y1>) to (<x2>, <y2>) with
        the colour c.

        If edit is True, we are drawing in the edit viewport rather than the
        full image view.
        """
        img = self._view_img
        if edit:
            img = self._edit_img

        if not c:  # make transparent checkerboard!
            c1 = '#aaaaaa'
            c2 = '#666666'
            dx = int(0.5 * (x2 - x1))
            dy = int(0.5 * (y2 - y1))
            img.put(c1, ['-to', x1, y1, x1 + dx, y1 + dy])
            img.put(c1, ['-to', x1 + dx, y1 + dy, x2, y2])
            img.put(c2, ['-to', x1 + dx, y1, x2, y1 + dy])
            img.put(c2, ['-to', x1, y1 + dy, x1 + dx, y2])
        else:
            # note, this warning about wrong argument type can be ignored,
            # as it is an issue with the put method not being properly
            # annotated.
            img.put(c, ['-to', x1, y1, x2, y2])

    def _update_view_canvas(self) -> None:
        """
        Update the 'view canvas' (on the left side of the panel.)
        """
        square_size = self._preview_size / self.canvas_size
        n = self.canvas_size

        self._view_img.blank()

        # Draw the grid
        for i in range(n):
            for j in range(n):
                self.draw_square(i, j, square_size, False)

    def draw_square(self, i, j, square_size, is_edit_canvas) -> None:
        """
        Draw a square on the canvas at the given position.
        """
        hex_rgb = self._canvas.get_hex_rgb((i, j))

        self._draw_rectangle(is_edit_canvas, hex_rgb, int(i * square_size),
                             int(j * square_size),
                             int((i + 1) * square_size),
                             int((j + 1) * square_size))
    


if __name__ == "__main__":
    DrawingGUI()  # Start the GUI with a blank canvas