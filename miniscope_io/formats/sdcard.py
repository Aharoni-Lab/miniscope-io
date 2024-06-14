"""
SD Card data layout formats for different miniscopes!
"""

from miniscope_io.models.sdcard import (
    BufferHeaderPositions,
    ConfigPositions,
    SDHeaderPositions,
    SDLayout,
    SectorConfig,
)

WireFreeSDLayout = SDLayout(
    version="0.1.1",
    sectors=SectorConfig(header=1022, config=1023, data=1024, size=512),
    write_key0=0x0D7CBA17,
    write_key1=0x0D7CBA17,
    write_key2=0x0D7CBA17,
    write_key3=0x0D7CBA17,
    header=SDHeaderPositions(
        gain=4, led=5, ewl=6, record_length=7, fs=8, delay_start=9, battery_cutoff=10
    ),
    config=ConfigPositions(
        width=0,
        height=1,
        fs=2,
        buffer_size=3,
        n_buffers_recorded=4,
        n_buffers_dropped=5,
    ),
    buffer=BufferHeaderPositions(
        length=0,
        linked_list=1,
        frame_num=2,
        buffer_count=3,
        frame_buffer_count=4,
        write_buffer_count=5,
        dropped_buffer_count=6,
        timestamp=7,
        data_length=8,
    ),
)

WireFreeSDLayout_Battery = SDLayout(**WireFreeSDLayout.model_dump())
"""
Making another format for now, but added version field so that we could
replace making more top-level classes with a FormatCollection that can store 
sets of formats for the same device with multiple versions.
"""
WireFreeSDLayout_Battery.buffer.write_timestamp = 9
WireFreeSDLayout_Battery.buffer.battery_voltage = 10


WireFreeSDLayout_Old = SDLayout(
    sectors=SectorConfig(header=1023, config=1024, data=1025, size=512),
    write_key0=0x0D7CBA17,
    write_key1=0x0D7CBA17,
    write_key2=0x0D7CBA17,
    write_key3=0x0D7CBA17,
    header=SDHeaderPositions(gain=4, led=5, ewl=6, record_length=7, fs=8),
    config=ConfigPositions(
        width=0,
        height=1,
        fs=2,
        buffer_size=3,
        n_buffers_recorded=4,
        n_buffers_dropped=5,
    ),
    buffer=BufferHeaderPositions(
        length=0,
        linked_list=1,
        frame_num=2,
        buffer_count=3,
        frame_buffer_count=4,
        write_buffer_count=5,
        dropped_buffer_count=6,
        timestamp=7,
        data_length=8,
    ),
)
