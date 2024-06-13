"""
Models for a data stream from a miniscope device: header formats,
containers, etc.
"""

from typing import Union

from miniscope_io.models import MiniscopeConfig, Container
from miniscope_io.types import Range

class BufferHeaderFormat(MiniscopeConfig):
    """
    Format model used to parse header at the beginning of every buffer.
    """
    linked_list: Union[int, Range]
    frame_num: Union[int, Range]
    buffer_count: Union[int, Range]
    frame_buffer_count: Union[int, Range]
    timestamp: Union[int, Range]
    pixel_count: Union[int, Range]


class BufferHeader(Container):
    """
    Container for the data stream's header, structured by :class:`.MetadataHeaderFormat`
    """

    linked_list: int
    frame_num: int
    buffer_count: int
    frame_buffer_count: int
    timestamp: int
    pixel_count: int