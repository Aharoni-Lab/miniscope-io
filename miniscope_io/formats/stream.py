"""
Formats for use with :mod:`miniscope_io.stream_daq`
We plan to re-define this soon so documentation will come after that.
"""

from miniscope_io.models.stream import StreamBufferHeaderFormat
""" 
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
    battery_voltage_raw=9,
    input_voltage_raw=10,
)
"""

StreamBufferHeader = StreamBufferHeaderFormat(
    linked_list=2,
    frame_num=3,
    buffer_count=5,
    frame_buffer_count=4,
    write_buffer_count=6,
    dropped_buffer_count=7,
    timestamp=8,
    pixel_count=3,
    write_timestamp=8,
    battery_voltage_raw=10,
    input_voltage_raw=11,
)
