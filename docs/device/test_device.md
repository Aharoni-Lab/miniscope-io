# Example stream device

**Under Construction:** This section will be populated when devices are released.

## Buffer Structure
- **Constituents**: The buffer consists of a concatenation of 32-bit header data and 8-bit pixel data.
- **Storage**: A single image is split and stored in a circulating buffer within the device. The [`num_buffers`](../api/stream_daq.md) should match the number of circulating buffers in the device.

## Header Values and Expected Transitions
See following docs for the basic structure.
- `miniscope_io.models.buffer.BufferHeaderFormat`
- `miniscope_io.models.stream.StreamBufferHeaderFormat`

Device specific notes are listed below.
- **`preamble`**: 32-bit preamble for detecting the beginning of each buffer. The [`preamble`](../api/stream_daq.md) in the device config needs to match the preamble defined in firmware.
- **`dropped_buffer_count`**: Currently not used and should always be zero.
- **`write_timestamp`**: Currently not used and should always be zero.
- **`battery_voltage`**: Currently not used and should always be zero.
- **`ewl_pos`**: Currently not used and should always be zero.