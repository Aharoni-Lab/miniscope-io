# stream_daq
This module is a data acquisition module that captures video streams from Miniscopes based on the `Miniscope-SAMD-Framework` firmware. The firmware repository will be published in future updates but is currently under development and private.

## Command
After [installation](../guide/installation.md) and customizing [configurations](stream-daq-config) if necessary, run the following command in this Git repository to start the data acquisition process:
```bash
>>> mio sdaq -c path/to/config.yml -o output_filename
[24-06-25T04:19:46] INFO     [miniscope_io.okDev] Connected to           opalkelly.py:34
                             XEM7310-A75
Connected to XEM7310-A75
Successfully uploaded /miniscope-io/miniscope_io/devices/selected_bitfile.bit
FrontPanel is supported
[24-06-11T01:40:45] INFO     [miniscope_io.streamDaq.frame] frame: 1570, bits lost: 0                                    stream_daq.py:524
[24-06-11T01:40:46] INFO     [miniscope_io.streamDaq.frame] frame: 1571, bits lost: 0                                    stream_daq.py:524
```
A window displaying the image transferred from the Miniscope should pop up. Additionally, the indexes of captured frames and their statuses will be logged in the terminal.

## Prerequisites
- **Data capture hardware:** Opal Kelly XEM7310-A75 FPGA board (connected via USB)
- **Supported Operating Systems:** MacOS or Ubuntu PC (To do: specify version)
- **Imaging hardware:** Miniscope based on the `Miniscope-SAMD-Framework` firmware. Hardware modules for feeding in data into the data capture hardware are also needed but these will be specified in future updates.

(stream-daq-config)=
## Configuration
A YAML file is used to configure this module. The configuration needs to match the imaging and data capture hardware for proper operation. This file is used to set up hardware, define data formats, and set data preambles. The contents of this YAML file will be parsed into a model [miniscope_io.models.stream](../api/models/stream.md), which then configures the Stream DAQ.

### Example Configuration
Below is an example configuration YAML file. More examples can be found in `miniscope_io.data.config`.

```yaml
# capture device. "OK" (Opal Kelly) or "UART"
device: "OK"

# The configuration bitstream file to upload to the Opal Kelly board. This uploads a Manchester decoder HDL and different bitstream files are required to configure different data rates and bit polarity. This is a binary file synthesized using Vivado, and details for generating this file will be provided in later updates.
bitstream: "USBInterface-6mhz-3v3-INVERSE.bit"

# COM port and baud rate is only required for UART mode
port: null
baudrate: null

# Preamble for each data buffer. This is actually converted to bytes in the StreamDaq but has to be imported as a string because .yaml doesn't support hexadecimal formats.
preamble: 0x12345678

# Image format. StreamDaq will calculate buffer size, etc. based on these parameters
frame_width: 304
frame_height: 304
pix_depth: 8

# Buffer data format. These have to match the firmware value
header_len: 12
buffer_block_length: 40
block_size: 512
num_buffers: 8

# Temporary parameter to handle bit polarity. This is not actual LSB, so it needs to be fixed later.
LSB: True
```

```{eval-rst}
.. automodule:: miniscope_io.stream_daq
    :members:
    :undoc-members:
```