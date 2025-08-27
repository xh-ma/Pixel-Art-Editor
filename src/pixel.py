def is_valid_rgb_colour(rgb: tuple[int, int, int]) -> bool:
    """Return whether <rgb> represents a valid RGB colour as explained in the handout.

    >>> is_valid_rgb_colour((1, 0, 150))
    True
    >>> is_valid_rgb_colour((-1, 255, 255))
    False
    >>> is_valid_rgb_colour((260, 0, 0))
    False
    """
    if not isinstance(rgb, tuple) or len(rgb) != 3:
        return False
    for c in rgb:
        if not isinstance(c, int) or c < 0 or c > 255:
            return False
    return True


def convert_to_hex_rgb(rgb: tuple[int, int, int]) -> str:
    """
    Convert <rgb> to the hex representation of this colour.

    As mentioned on the handout, we represent a colour by specifying the
    intensity of the red, green and blue components.
    The intensities are specified as values in the range [0, 255].
    These intensities can be represented using hexadecimal (base 16) numbers,
    instead of the decimal (base 10) system.

    The hexadecimal representation of a colour starts with the
    "#" symbol, followed by the value for the red, green and blue channels as
    two hexadecimal values each, between 00 (0 in decimal) and
    ff (255 in decimal).

    For instance, the colour (0, 0, 255) would have the hexadecimal
    representation #0000ff.

    We use the hex function in Python to determine the hexadecimal
    representation of a base-ten number.

    Preconditions:
    - is_valid_rgb_colour(rgb)

    >>> convert_to_hex_rgb((255, 255, 255))
    '#ffffff'
    >>> convert_to_hex_rgb((0, 15, 16))
    '#000f10'
    """
    r, g, b = rgb
    return f"#{hex(r)[2:]:0>2}{hex(g)[2:]:0>2}{hex(b)[2:]:0>2}"


class Pixel:
    """
    A representation of a single pixel in a drawing application.

    Attributes:
    - rgb: the red, green, blue components of this Pixel.
           A value of None represents a transparent pixel.

    Representation Invariants:
    - self.rgb is None or is_valid_rgb_colour(self.rgb)
    """
    rgb: None | tuple[int, int, int]

    def __init__(self, rgb: tuple[int, int, int] | None = None) -> None:
        """
        Initialize this pixel with the <rgb> values provided. If <rgb> is not
        provided or is None, then the colour will be treated as 'transparent'.

        Preconditions:
        - rgb is None or is_valid_rgb_colour(rgb)

        >>> rose_quartz = Pixel((174, 140, 163))
        >>> rose_quartz.rgb
        (174, 140, 163)
        >>> teal = Pixel((0, 125, 125))
        >>> teal.rgb
        (0, 125, 125)
        """
        self.rgb = rgb

    def set(self, colour_hex_str: str | None) -> None:
        """
        Set this Pixel's attributes to represent the colour indicated
        by <colour_hex_str>.

        If <colour_hex_str> is None, this sets the pixel to be transparent.

        Note: You can call the built-in int function with an additional argument
              representing its base.
              int(s, 16) will convert string <s> to an integer assuming
              the string represents a hexadecimal number.

        Preconditions:
        - colour_hex_str is None or len(colour_hex_str) == 7
        - colour_hex_str is None or colour_hex_str[0] == '#'
        - colour_hex_str is None or colour_hex_str is a valid hexadecimal
          representation of a colour.

        >>> lavender = Pixel(None)
        >>> lavender.set("#D4AFCD")
        >>> lavender.rgb == (212, 175, 205)
        True
        """
        if colour_hex_str is None:
            self.rgb = None
        else:
            r = int(colour_hex_str[1:3], 16)
            g = int(colour_hex_str[3:5], 16)
            b = int(colour_hex_str[5:7], 16)
            self.rgb = (r, g, b)

    def is_transparent(self) -> bool:
        """
        Return True iff this Pixel is transparent.

        >>> p = Pixel(None)
        >>> p.is_transparent()
        True
        >>> p = Pixel((174, 140, 163))
        >>> p.is_transparent()
        False
        """
        if self.rgb is None:
            return True
        return False


if __name__ == "__main__":
    import doctest

    doctest.testmod()
