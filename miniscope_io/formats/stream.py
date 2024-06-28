"""
Formats for use with :mod:`miniscope_io.stream_daq`
"""

from miniscope_io.models.stream import StreamBufferHeaderFormat

StreamBufferHeader = StreamBufferHeaderFormat(
    linked_list=0,
    frame_num=1,
    buffer_count=2,
    frame_buffer_count=3,
    timestamp=6,
    pixel_count=7,
)
