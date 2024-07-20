# Example stream device

**Under Construction:** This section will be populated when devices are released.

## Buffer Structure
- **Constituents**: The buffer consists of a concatenation of 32-bit header data and 8-bit pixel data.
- **Storage**: A single image is split and stored in a circulating buffer within the device. The [`num_buffers`](../api/stream_daq.md) should match the number of circulating buffers in the device.

## Header Values and Expected Transitions

- **`preamble`**: 32-bit preamble for detecting the beginning of each buffer. The [`preamble`](../api/stream_daq.md) in the device config needs to match the preamble defined in firmware.
- **`linked_list`**: Index of data buffers within the circulating structure. This increments with each buffer until it reaches [`num_buffers`](../api/stream_daq.md), then resets to zero.
- **`frame_num`**: The index of the image frame, which increments with each image frame (comprising multiple data buffers).
- **`buffer_count`**: Index of data buffers, which increments with each buffer.
- **`frame_buffer_count`**: Index of the data buffer within the image frame. It is set to `frame_buffer_count = 0` at the first buffer in each frame.
- **`write_buffer_count`**: Number of data buffers transmitted out of the MCU.
- **`dropped_buffer_count`**: Number of dropped data buffers. Currently not used and should always be zero.
- **`timestamp`**: Timestamp in milliseconds. This should increase approximately by `1 / framerate * 1000` every frame.
- **`pixel_count`**: Number of pixels contained in the buffer.
- **`write_timestamp`**: Currently not used and should always be zero.
- **`battery_voltage`**: Currently not used and should always be zero.
- **`ewl_pos`**: Currently not used and should always be zero.