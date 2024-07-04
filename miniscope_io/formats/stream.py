"""
Formats for use with :mod:`miniscope_io.stream_daq`
We plan to re-define this soon so documentation will come after that.
"""

from miniscope_io.models.stream import StreamBufferHeaderFormat

StreamBufferHeader = StreamBufferHeaderFormat(
    linked_list=0,
    frame_num=1,
    buffer_count=2,
    frame_buffer_count=3,
    write_buffer_count=4,
    dropped_buffer_count=5,
    timestamp=6,
    pixel_count=7,
    write_timestamp=8,
    battery_voltage=9,
    ewl_pos=10,
)
