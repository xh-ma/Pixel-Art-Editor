from __future__ import annotations
from typing import TextIO
from pixel import Pixel, convert_to_hex_rgb


def average_pixels(pixels: list[Pixel]) -> Pixel:
    """
    Return a Pixel containing the average RGB values of <pixels>.

    If a pixel is transparent, then it is NOT included in the average.
    For example, if exactly one of the four pixels is transparent, then the
    average would be computed using the other three.

    If all pixels are transparent, then the returned Pixel would be transparent.

    The average of a pixel involves averaging each of the red, green and
    blue values, separately.

    Note: round should be used to round the averages to integers.

    >>> average_pixels([Pixel((1, 2, 3)), Pixel((2, 3, 5))]).rgb
    (2, 2, 4)
    >>> average_pixels([Pixel(None)]).is_transparent()
    True
    """
    r_sum = 0
    g_sum = 0
    b_sum = 0
    count = 0
    for p in pixels:
        if p.rgb is not None:
            r, g, b = p.rgb
            r_sum += r
            g_sum += g
            b_sum += b
            count += 1
    if count == 0:
        return Pixel()
    avg_r = round(r_sum / count)
    avg_g = round(g_sum / count)
    avg_b = round(b_sum / count)
    return Pixel((avg_r, avg_g, avg_b))


class Layer:
    """
    A representation of a single layer in a drawing application.

    Attributes:
    - name: the name of this Layer
    - visible: whether this layer is visible
    - _pixels: a list of lists representing the grid of pixels
    - size: the dimensions of this Layer

    Representation Invariants:
    - self.size[0] == len(self._pixels)
    - self.size[0] > 0 and self.size[1] > 0
    - len(self.name) > 0
    - each sublist in self._pixels represents a column of length self.size[1]
    """
    name: str
    visible: bool
    _pixels: list[list[Pixel]]
    size: tuple[int, int]

    def __init__(self, size: tuple[int, int],
                 bg: tuple[int, int, int] | None = None,
                 name: str = 'Layer') -> None:
        """
        Initialize this Layer with a <size[0]> * <size[1]> grid of pixels,
        where <size[0]> is the number of columns in the grid and <size[1]> is
        the number of rows in the grid.

        The layer will be named <name> and <bg> will be used as the background
        colour. If <bg> is not provided, the background should be transparent
        by default.

        The layer should initially be visible.

        Note: A layer could still be visible despite containing only transparent
            pixels.

        Preconditions:
        - bg is None or is_valid_rgb_colour(bg)
        - len(name) > 0

        >>> new_layer = Layer((3, 4), (51, 12, 47), 'New Layer')
        >>> new_layer.name == "New Layer"
        True
        >>> new_layer.visible
        True
        >>> new_layer.size
        (3, 4)
        >>> print(new_layer)  # Note: requires get_pixel to be implemented for this to work
        True
        (51, 12, 47)|(51, 12, 47)|(51, 12, 47)
        (51, 12, 47)|(51, 12, 47)|(51, 12, 47)
        (51, 12, 47)|(51, 12, 47)|(51, 12, 47)
        (51, 12, 47)|(51, 12, 47)|(51, 12, 47)
        """
        self.name = name
        self.visible = True
        self.size = size
        self._pixels = []
        for _ in range(size[0]):
            column = []
            for _ in range(size[1]):
                column.append(Pixel(bg))
            self._pixels.append(column)

    def get_rgb_row(self, row: int) -> list[None | tuple[int, int, int]]:
        """
        Return a list containing the RGB tuples of all pixels in the <row>'th
        row of this layer.

        Precondtions:
        - 0 <= row < self.size[1]

        >>> l = Layer((2, 2))
        >>> l.get_pixel((0, 0)).rgb = (255, 0, 0)
        >>> l.get_rgb_row(0)
        [(255, 0, 0), None]
        """
        rgb_row = []
        for col in range(self.size[0]):
            rgb_row.append(self._pixels[col][row].rgb)
        return rgb_row

    def get_pixel(self, loc: tuple[int, int]) -> Pixel:
        """
        Return the pixel located at <loc> in this Layer,
        where <loc> is in the form (col index, row index).

        Precondtions:
        - (0 <= loc[0] < self.size[0]) and (0 <= loc[1] < self.size[1])

        >>> l = Layer((2, 2))
        >>> pixel = l.get_pixel((0, 0))
        >>> pixel.is_transparent()
        True
        """
        col, row = loc
        return self._pixels[col][row]

    def get_hex_rgb(self, loc: tuple[int, int]) -> None | str:
        """
        Return the hex representation of the pixel at location <loc> or None
        if the pixel is transparent.

        <loc> is in the format (col index, row index).

        Hint: you should make use of the provided convert_to_hex_rgb function.

        Preconditions:
        - (0 <= loc[0] < self.size[0]) and (0 <= loc[1] < self.size[1])

        >>> new_layer = Layer((2, 4), None, name="New Layer")
        >>> new_layer.get_pixel((0, 0)).rgb = (4, 67, 137)
        >>> new_layer.get_pixel((1, 2)).rgb = (129, 23, 27)
        >>> new_layer.get_hex_rgb((0, 0)) == "#044389"
        True
        >>> new_layer.get_hex_rgb((1, 2)) == "#81171b"
        True
        >>> new_layer.get_hex_rgb((1, 3)) is None
        True
        """
        pixel = self.get_pixel(loc)
        if pixel.is_transparent():
            return None
        return convert_to_hex_rgb(pixel.rgb)

    def upscale(self) -> Layer:
        """
        Return a new layer whose width and height are twice that of this layer.

        Each new pixel is obtained by making copies of the rgb value of
        the pixel that will be expanded to cover a 2-by-2 area.

        The returned layer should have the same values for the name and visible
        attributes as self.

        Note: Make sure to create new Pixel objects to avoid aliasing.

        >>> l = Layer((1, 1), bg=(255, 0, 255))
        >>> large = l.upscale()  # Note: all pixels same colour
        >>> large.get_pixel((0, 0)).rgb == l.get_pixel((0, 0)).rgb
        True
        >>> large.get_pixel((1, 1)).rgb == l.get_pixel((0, 0)).rgb
        True
        """
        new_size = (self.size[0] * 2, self.size[1] * 2)
        new_layer = Layer(new_size, None, self.name)
        new_layer.visible = self.visible
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                pixel = self.get_pixel((x, y))
                rgb_value = pixel.rgb
                new_layer.get_pixel((x * 2, y * 2)).rgb = rgb_value
                new_layer.get_pixel((x * 2 + 1, y * 2)).rgb = rgb_value
                new_layer.get_pixel((x * 2, y * 2 + 1)).rgb = rgb_value
                new_layer.get_pixel((x * 2 + 1, y * 2 + 1)).rgb = rgb_value
        return new_layer

    def downscale(self) -> Layer:
        """
        Return a new Layer whose width and height are half of this layer.
        The returned Layer should have the same values for the name and visible
        attributes as self.

        Each new pixel is obtained by taking the average RGB value of
        the 2-by-2 area of pixels that it is replacing. You MUST use the
        average_pixels helper function provided in order to calculate the
        average: this will take transparent Pixels into consideration for you.

        Preconditions:
        - self.size[0] % 2 == 0
        - self.size[1] % 2 == 0
        - self.size[0] > 1 and self.size[1] > 1

        >>> l = Layer((2, 2))
        >>> smaller = l.downscale()  # Note: all pixels same colour
        >>> smaller.get_pixel((0, 0)).rgb == l.get_pixel((0, 0)).rgb
        True
        >>> l = Layer((4, 4), (212, 153, 185))
        >>> l.visible = True
        >>> l.get_pixel((3, 0)).rgb = None
        >>> l.get_pixel((0, 2)).rgb = None
        >>> l.get_pixel((2, 2)).rgb = (88, 129, 87)
        >>> smaller = l.downscale()
        >>> smaller.size
        (2, 2)
        >>> smaller.visible
        True
        >>> smaller.get_pixel((0, 0)).rgb
        (212, 153, 185)
        >>> smaller.get_pixel((1, 0)).rgb
        (212, 153, 185)
        >>> smaller.get_pixel((0, 1)).rgb
        (212, 153, 185)
        >>> smaller.get_pixel((1, 1)).rgb
        (181, 147, 160)
        """
        new_size = (self.size[0] // 2, self.size[1] // 2)
        new_layer = Layer(new_size, None, self.name)
        new_layer.visible = self.visible
        for x in range(new_size[0]):
            for y in range(new_size[1]):
                pixels_to_avg = [self.get_pixel((2 * x, 2 * y)),
                                 self.get_pixel((2 * x + 1, 2 * y)),
                                 self.get_pixel((2 * x, 2 * y + 1)),
                                 self.get_pixel((2 * x + 1, 2 * y + 1)),]
                avg_pixel = average_pixels(pixels_to_avg)
                new_layer.get_pixel((x, y)).rgb = avg_pixel.rgb
        return new_layer
    # The methods below have been provided to you: you should not modify
    # them in any way!

    def __str__(self) -> str:
        """
        Return the string representation of this Layer.
        Note: this method requires get_pixel to be implemented!

        >>> new_layer = Layer((2, 4), None, name="New Layer")
        >>> print(new_layer)
        True
        None|None
        None|None
        None|None
        None|None
        >>> new_layer = Layer((2, 4), (46, 196, 182), name='New Layer')
        >>> print(new_layer)
        True
        (46, 196, 182)|(46, 196, 182)
        (46, 196, 182)|(46, 196, 182)
        (46, 196, 182)|(46, 196, 182)
        (46, 196, 182)|(46, 196, 182)
        """
        rslt = f"{self.visible}\n"
        for row in range(self.size[1]):
            for col in range(self.size[0]):
                rslt += f"{self.get_pixel((col, row)).rgb}|"
            rslt = rslt.strip("|")
            rslt += "\n"
        return rslt.strip()

    # Note: "# pragma: no cover" is a feature used by the code coverage module,
    #       which indicates that the line of code containing the comment should
    #       be excluded from the code coverage report. Here, we have used it to
    #       restrict the code coverage to not include this provided method
    def read_layer(self, f: TextIO) -> None:  # pragma: no cover
        """
        Read the layer data stored in file <f> and set the pixels to
        their appropriate values.

        Preconditions:
        - <f> follows the format specified in the handout, and the next
          line to read in <f> is the start of the information for this layer
          i.e., the visibility status of this layer.
        - The size of this layer has been set correctly.
        """
        visible = f.readline().strip()
        if visible == 'True':
            self.visible = True
        else:
            self.visible = False
        for row in range(self.size[1]):
            line = f.readline().strip()
            col = 0
            for pixel in line.split("|"):
                if pixel == 'None':
                    rgb = None
                else:
                    parts = pixel.lstrip('(').rstrip(')').split(",")
                    rgb = int(parts[0]), int(parts[1]), int(parts[2])
                self._pixels[col][row].rgb = rgb
                col += 1


# Note: "# pragma: no cover" is a feature used by the code coverage module,
#       which indicates that the line of code containing the comment should
#       be excluded from the code coverage report. Here, we have used it to
#       restrict the code coverage to not include the main block
if __name__ == "__main__":  # pragma: no cover
    import doctest

    doctest.testmod()