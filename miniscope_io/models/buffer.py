"""
Models for a data stream from a miniscope device: header formats,
containers, etc.
"""

from miniscope_io.models import Container, MiniscopeConfig


class BufferHeaderFormat(MiniscopeConfig):
    """
    Format model used to parse header at the beginning of every buffer.
    """

    linked_list: int
    frame_num: int
    buffer_count: int
    frame_buffer_count: int
    timestamp: int
    pixel_count: int


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
