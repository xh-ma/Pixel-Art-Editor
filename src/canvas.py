from __future__ import annotations
from typing import TextIO
from PIL import Image

from pixel import convert_to_hex_rgb
from layer import Layer


def canvas_to_png(canvas: Canvas, path: str) -> None:
    """
    Convert this canvas to an image and save it to <path> as a PNG file.

    Preconditions:
    - path.endswith('.png')
    """
    image = Image.new('RGBA', size=canvas.size, color=(0, 0, 0, 0))
    for i in range(canvas.size[0]):
        for j in range(canvas.size[1]):
            color = _canvas_to_png_helper(canvas, i, j)
            if color is not None:
                image.putpixel((i, j), color)

    image.save(path)


def _canvas_to_png_helper(canvas: Canvas, i: int, j: int) -> tuple[int, int, int, int] | None:
    """Helper function for canvas_to_png to get the top-most
    rgba value at location (i, j) in <canvas>.
    """
    for layer in canvas.get_layers():
        if layer.visible:
            c = layer.get_pixel((i, j)).rgb
            if c is not None:
                return c[0], c[1], c[2], 255
    return None


def load_canvas(path: str = 'my_canvas.canvas') -> Canvas:
    """
    Return a new Canvas object using the information from the file at <path>.

    See the handout for the description of the .canvas file format.

    Preconditions:
    - path.endswith('.canvas')
    - the file with the given path follows the .canvas format described in the handout
    """
    with open(path) as f:
        line = f.readline()
        width, height, n_layers = line.strip().split(',')
        width, height, n_layers = int(width), int(height), int(n_layers)
        size = (width, height)
        c = Canvas(size)
        for _ in range(n_layers):
            layer = Layer(size)
            layer.read_layer(f)
            c.add_layer(layer)

    c.active_layer_index = 0
    return c


def blank_canvas(width: int, height: int, num_layers: int = 4) -> Canvas:
    """
    Return a new canvas with the given <width> by <height> size and
    <num_layers> layers. The i'th layer is named 'layer i'.

    The default number of layers is 4.

    Preconditions:
    - 0 <= num_layers < 10
    - width > 0 and height > 0
    """
    c = Canvas((width, height))
    while c.get_num_layers() < num_layers:
        c.add_layer(Layer((width, height),
                          name=f'layer {c.get_num_layers() + 1}'))
    return c


class Canvas:
    """
    A representation of a drawing canvas for a pixel art program.
    A canvas consists of layers and operations that manipulate those layers.

    Attributes:
    - size: the size (width * height) of this canvas
    - active_layer_index: the index of the currently active layer or -1 if no layers exist
    - _layers: a list of layers in this canvas

    Representation Invariants:
    - (self.size[0] >= 1) and (self.size[1] >= 1)
    - (0 <= self.active_layer_index < len(self._layers)) or \
      (self.active_layer_index == -1 and len(self._layers) == 0)
    - The _layers are stored with the top-most layer at the front of the list
      (index 0) and the bottom-most layer at the end of the list, with
      intermediate layers consistently ordered.
    - each layer has size equal to self.size
    - no layer appears more than once in this canvas
    """
    size: tuple[int, int]
    active_layer_index: int
    _layers: list[Layer]

    def __init__(self, size: tuple[int, int] = (16, 16)) -> None:
        """
        Initialize this Canvas with the given <size>.
        <size> is of the form (number of columns, number of rows).

        The default size is (16, 16).

        A Canvas initially has no layers (and no active layer as a result.)

        Preconditions:
        - size[0] >= 1  and  size[1] >= 1

        >>> new_canvas = Canvas((4, 4))
        >>> new_canvas.size
        (4, 4)
        >>> new_canvas.active_layer_index
        -1
        """
        self.size = size
        self.active_layer_index = -1
        self._layers = []

    def add_layer(self, layer: Layer) -> None:
        """
        Add <layer> to the canvas such that it is the bottom-most layer.

        If there are no layers in the canvas, then the added layer should
        become the active layer.

        Preconditions:
        - layer.size == self.size
        - layer not in self._layers

        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> new_canvas = Canvas((4, 4))
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.active_layer_index
        0
        """
        self._layers.append(layer)
        if self.active_layer_index == -1:
            self.active_layer_index = 0

    def get_num_layers(self) -> int:
        """
        Return the number of layers in this Canvas.

        >>> new_canvas = Canvas((4, 4))
        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.get_num_layers()
        2
        """
        return len(self._layers)

    def get_layers(self) -> list[Layer]:
        """
        Return a shallow copy of the list of layers on this canvas, with
        the layers ordered from topmost to bottommost.

        By shallow copy, we mean that the returned list is NOT an alias for
        the original list, but each layer in the list IS an alias for its
        correpsonding layer.

        Note: the doctest example below requires add_layer to be implemented.

        >>> new_canvas = Canvas((4, 4))
        >>> layer_abc = Layer((4, 4), None, 'Layer ABC')
        >>> new_canvas.add_layer(layer_abc)
        >>> new_canvas.add_layer(Layer((4, 4), None, 'Layer BCD'))
        >>> new_canvas.add_layer(Layer((4, 4), None, 'Layer DEF'))
        >>> canvas_layers =  new_canvas.get_layers()
        >>> len(canvas_layers)
        3
        >>> canvas_layers[0] is layer_abc
        True
        >>> canvas_layers.remove(layer_abc)
        >>> len(canvas_layers)
        2
        >>> len(new_canvas.get_layers())  # confirm that the original list is unchanged
        3
        """
        return self._layers[:]

    def get_layer(self, k: int) -> Layer:
        """
        Return the <k>th topmost layer in this Canvas.

        Preconditions:
        - 0 <= k < self.get_num_layers()

        >>> new_canvas = Canvas((4, 4))
        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.get_layer(1) is layer_b
        True
        """
        return self._layers[k]

    def get_active_layer(self) -> Layer:
        """
        Return the active layer of this canvas.

        Preconditions:
        - len(self._layers) > 0

        >>> new_canvas = Canvas((4, 4))
        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.active_layer_index = 1
        >>> new_canvas.get_active_layer() is layer_b
        True
        """
        return self._layers[self.active_layer_index]

    def set_active_layer_index(self, k: int) -> None:
        """
        Set the active layer index to <k>.

        Preconditions:
        - 0 <= k < self.get_num_layers()
        - self.get_num_layers() > 0

        >>> new_canvas = Canvas((4, 4))
        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.set_active_layer_index(0)
        >>> new_canvas.get_active_layer() is layer_a
        True
        """
        self.active_layer_index = k

    def change_active_layer(self, new_active_layer: Layer) -> None:
        """
        Change the active layer index such that it corresponds to <new_active_layer>.

        Preconditions:
        - new_active_layer in self._layers

        >>> new_canvas = Canvas((4, 4))
        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.active_layer_index = 1
        >>> new_canvas.change_active_layer(layer_a)
        >>> new_canvas.active_layer_index
        0
        """
        self.active_layer_index = self._layers.index(new_active_layer)

    def get_hex_rgb(self, loc: tuple[int, int]) -> None | str:
        """
        Return the hex representation of the pixel at location <loc>
        of the topmost visible layer.

        If all layers are not visible or all pixels at <loc> are
        transparent, then return None.

        Preconditions:
        - 0 <= loc[0] < self.size[0] and 0 <= loc[1] < self.size[1]

        >>> new_canvas = Canvas((4, 4))
        >>> layer_a = Layer((4, 4), (129, 23, 27), 'Layer A')  # red
        >>> layer_a.visible = False
        >>> layer_b = Layer((4, 4), (4, 67, 137), 'Layer B')  # blue
        >>> layer_b.get_pixel((2, 2)).rgb = None
        >>> layer_b.get_pixel((3, 3)).rgb = None
        >>> layer_c = Layer((4, 4), (0, 196, 125), 'Layer C')  # emerald
        >>> layer_c.get_pixel((2, 2)).rgb = None
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.add_layer(layer_c)
        >>> new_canvas.get_hex_rgb((2, 2)) is None
        True
        >>> new_canvas.get_hex_rgb((1, 3))
        '#044389'
        >>> new_canvas.get_hex_rgb((3, 3))
        '#00c47d'
        """
        for layer in self._layers:
            if layer.visible:
                rgb = layer.get_pixel(loc).rgb
                if rgb is not None:
                    return convert_to_hex_rgb(rgb)
        return None

    def remove_layer(self, layer: Layer) -> None:
        """
        Remove <layer> from this canvas.
        The current active layer should still refer to the same layer after this method returns,
        unless <layer> *was* the current active layer.

        If <layer> was the current active layer, then this Canvas'
        active_layer_index should stay the same *unless* this index would be out
        of bounds. In this case: active_layer_index should refer to the highest
        possible index within bounds.

        Preconditions:
        - layer in self._layers
        - len(self._layers) >= 2

        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> layer_c = Layer((4, 4), None, 'Layer C')
        >>> new_canvas = Canvas((4, 4))
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.add_layer(layer_c)
        >>> new_canvas.set_active_layer_index(1)
        >>> new_canvas.remove_layer(layer_a)
        >>> new_canvas.get_active_layer() is layer_b
        True
        """
        index = self._layers.index(layer)
        self._layers.remove(layer)
        if self.active_layer_index == index:
            if self.active_layer_index >= len(self._layers):
                self.active_layer_index = len(self._layers) - 1
        elif self.active_layer_index > index:
            self.active_layer_index -= 1

    def move_layer(self, layer: Layer, i: int) -> None:
        """
        Move layer such that <layer> is moved <i> positions towards the top.
        i.e. if <layer> is at the bottom and <i> is 3, we move it up 3 places.

        If <i> is such that the new position is less than 0, move <layer> to
        position 0. Likewise, if <i> is such that the new position is greater
        than or equal to the number of layers, move <layer> to the bottom-most
        position.

        Note: the active_layer_index should be appropriately updated such that it
        still corresponds to the index of the previously active layer.

        Preconditions:
        - layer in self._layers
        - i != 0

        >>> layer_a = Layer((4, 4), None, 'Layer A')
        >>> layer_b = Layer((4, 4), None, 'Layer B')
        >>> layer_c = Layer((4, 4), None, 'Layer C')
        >>> layer_d = Layer((4, 4), None, 'Layer D')
        >>> layer_e = Layer((4, 4), None, 'Layer E')
        >>> new_canvas = Canvas((4, 4))
        >>> new_canvas.add_layer(layer_a)
        >>> new_canvas.add_layer(layer_b)
        >>> new_canvas.add_layer(layer_c)
        >>> new_canvas.add_layer(layer_d)
        >>> new_canvas.add_layer(layer_e)
        >>> new_canvas.active_layer_index = 1
        >>> new_canvas.move_layer(layer_d, 2)
        >>> new_canvas.move_layer(layer_b, -2)
        >>> new_canvas.get_layers() == [
        ...     layer_a, layer_d, layer_c, layer_e, layer_b]
        True
        >>> new_canvas.active_layer_index
        4
        """
        org_index = self._layers.index(layer)
        new_index = max(0, min(org_index - i, len(self._layers) - 1))
        self._layers.pop(org_index)
        self._layers.insert(new_index, layer)
        if self.active_layer_index == org_index:
            self.active_layer_index = new_index
        elif org_index < self.active_layer_index <= new_index:
            self.active_layer_index -= 1
        elif new_index <= self.active_layer_index < org_index:
            self.active_layer_index += 1

    def upscale(self) -> None:
        """
        Upscale all layers associated with this canvas.

        See the Layer.upscale method for more details.

        Hint: this is a mutating method in that it should create new layers
              and update self's relevant attribute. When implemented correctly,
              this method should be quite short.

        >>> new_canvas = Canvas((4, 4))
        >>> new_canvas.add_layer(Layer((4, 4), None, 'Layer A'))
        >>> new_canvas.add_layer(Layer((4, 4), None, 'Layer B'))
        >>> new_canvas.upscale()
        >>> new_canvas.size
        (8, 8)
        >>> len(new_canvas.get_layers())
        2
        >>> new_canvas.get_layer(1).size
        (8, 8)
        """
        upscale_l = []
        for layer in self._layers:
            upscale_l.append(layer.upscale())
        self.size = (self.size[0] * 2, self.size[1] * 2)
        self._layers = upscale_l

    def downscale(self) -> None:
        """
        Downscale all layers associated with this canvas.

        See the Layer.downscale method for more details.

        Hint: this is a mutating method in that it should create new layers
              and update self's relevant attribute. When implemented correctly,
              this method should be quite short.

        Preconditions:
        - self.size[0] % 2 == 0
        - self.size[1] % 2 == 0
        - self.size[0] > 1 and self.size[1] > 1

        >>> new_canvas = Canvas((4, 4))
        >>> new_canvas.add_layer(Layer((4, 4), None, 'Layer A'))
        >>> new_canvas.add_layer(Layer((4, 4), None, 'Layer B'))
        >>> new_canvas.downscale()
        >>> new_canvas.size
        (2, 2)
        >>> len(new_canvas.get_layers())
        2
        >>> new_canvas.get_layer(1).size
        (2, 2)
        """
        downscale_l = []
        for layer in self._layers:
            downscale_l.append(layer.downscale())
        self.size = (self.size[0] // 2, self.size[1] // 2)
        self._layers = downscale_l

    def save(self, file_name: str) -> None:
        """
        Save this canvas to a file called <file_name>.

        If the file name ends in '.png', the file will be saved in PNG format.
        The canvas_to_png helper must be used for this!

        If the file name ends in '.canvas', the canvas will be saved in the
        .canvas format described in the assignment handout.

        Briefly, the format for a .canvas file is:
            size, number_of_layers
            string_representation_of_top_most_layer
            ...
            string_representation_of_bottom_most_layer

        Preconditions:
        - file_name.endswith('.canvas') or file_name.endswith('.png')
        """
        if file_name.endswith('.png'):
            canvas_to_png(self, file_name)
        elif file_name.endswith('.canvas'):
            with open(file_name, 'w') as f:
                f.write(f'{self.size[0]}, {self.size[1]}, {len(self._layers)}\n')
                for layer in self._layers:
                    self._write_layer(f, layer)

    def _write_layer(self, f: TextIO, layer: Layer) -> None:
        """
        Helper method to write a single layer to f, the file object to write to.
        """
        f.write(f'{layer.visible}\n')
        for y in range(self.size[1]):
            data = []
            for x in range(self.size[0]):
                pixel = layer.get_pixel((x, y))
                if pixel.rgb is None:
                    data.append('None')
                else:
                    data.append(f'({pixel.rgb[0]}, {pixel.rgb[1]}, {pixel.rgb[2]})')
            f.write('|'.join(data) + '\n')


if __name__ == "__main__":
    import doctest

    doctest.testmod()