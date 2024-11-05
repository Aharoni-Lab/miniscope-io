"""
Type and type annotations
"""

from typing import NamedTuple, Tuple, Union

Range = Union[Tuple[int, int], Tuple[float, float]]


class BBox(NamedTuple):
    """
    Bounding Box

    (for specificying a rectangular ROI within an image frame)
    """

    x: int
    """Leftmost x coordinate"""
    y: int
    """Topmost y coordinate"""
    width: int
    height: int


class Resolution(NamedTuple):
    """
    Pixel resolution of a frame or camera.

    (i.e. the number of pixels a frame is wide and tall,
    not e.g. the spatial extent of an individual pixel)
    """

    width: int
    height: int
