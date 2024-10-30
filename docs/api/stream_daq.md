# stream_daq
This module is a data acquisition module that captures video streams from Miniscopes based on the `Miniscope-SAMD-Framework` firmware. The firmware repository will be published in future updates but is currently under development and private.

## Command
After [installation](../guide/installation.md) and customizing [device configurations](stream-dev-config) and [runtime configuration](models/config.md) if necessary, run the command described in [CLI Usage](../cli/main.rst).

One example of this command is the following:
```bash
$ mio stream capture -c .path/to/device/config.yml -o output_filename.avi -m
```
A window displaying the image transferred from the Miniscope and a graph plotting metadata (`-m` option) should pop up. Additionally, the indexes of captured frames and their statuses will be logged in the terminal. The `MINISCOPE_IO_STREAM_HEADER_PLOT_KEY` defines plotted header fields (see `.env.sample`).

## Prerequisites
- **Data capture hardware:** Opal Kelly XEM7310-A75 FPGA board (connected via USB)
- **Supported Operating Systems:** MacOS or Ubuntu PC (To do: specify version)
- **Imaging hardware:** Miniscope based on the `Miniscope-SAMD-Framework` firmware. Hardware modules for feeding in data into the data capture hardware are also needed but these will be specified in future updates.

(stream-dev-config)=
## Device configuration
A YAML file is used to configure Stream DAQ based on the device configuration. The device configuration needs to match the imaging and data capture hardware for proper operation. This file is used to set up hardware, define data formats, and set data preambles. The contents of this YAML file will be parsed into a model [miniscope_io.models.stream](../api/models/stream.md), which then configures the Stream DAQ.

### Example device configuration
Below is an example configuration YAML file. More examples can be found in `miniscope_io.data.config`.

```yaml
# capture device. "OK" (Opal Kelly) or "UART"
device: "OK"

# The configuration bitstream file to upload to the Opal Kelly board. This uploads a Manchester decoder HDL and different bitstream files are required to configure different data rates and bit polarity. This is a binary file synthesized using Vivado, and details for generating this file will be provided in later updates.
bitstream: "USBInterface-6mhz-3v3-INVERSE.bit"
nomenclature: Frequency of SPI clock (Fpga can only create bit files with speed: 100 / i MHz where i is an integer), J2_2 indicates signal goes into second pin of J2 pin headers in breakout board, 3v3 V inoput from digitization board, following the IEEE convention of Manchester encoding

# COM port and baud rate is only required for UART mode
port: null
baudrate: null

# Preamble for each data buffer.
preamble: 0x12345678

# Image format. StreamDaq will calculate buffer size, etc. based on these parameters
frame_width: 200
frame_height: 200
pix_depth: 8

# Buffer data format. These have to match the firmware value
header_len: 384 # 12 * 32 (in bits)
buffer_block_length: 10
block_size: 512
num_buffers: 32

# Flags to flip bit/byte order when recovering headers and data. See model document for details.
reverse_header_bits: True
reverse_header_bytes: True
reverse_payload_bits: True
reverse_payload_bytes: True

```

```{eval-rst}
.. automodule:: miniscope_io.stream_daq
    :members:
    :undoc-members:
```