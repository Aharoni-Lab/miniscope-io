"""
Formats for use with :mod:`miniscope_io.stream_daq`
"""

from miniscope_io.models.stream import StreamBufferHeaderFormat

StreamBufferHeader = StreamBufferHeaderFormat(
    linked_list = (0, 32),
    frame_num = (32, 64),
    buffer_count = (64, 96),
    frame_buffer_count = (96, 128),
    timestamp = (192, 224),
    pixel_count = (224, 256)
)
