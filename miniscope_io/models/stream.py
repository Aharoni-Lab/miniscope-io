"""
Models for :mod:`miniscope_io.stream_daq`
"""

from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import field_validator

from miniscope_io import DEVICE_DIR
from miniscope_io.models import MiniscopeConfig
from miniscope_io.models.buffer import BufferHeader, BufferHeaderFormat
from miniscope_io.models.mixins import YAMLMixin


class StreamBufferHeaderFormat(BufferHeaderFormat):
    """
    Refinements of :class:`.BufferHeaderFormat` for
    :class:`~miniscope_io.stream_daq.StreamDaq`
    """

    pixel_count: int


class StreamBufferHeader(BufferHeader):
    """
    Refinements of :class:`.BufferHeader` for
    :class:`~miniscope_io.stream_daq.StreamDaq`
    """

    pixel_count: int


class StreamDevConfig(MiniscopeConfig, YAMLMixin):
    """
    Format model used to parse DAQ configuration yaml file (examples are in ./config)
    The model attributes are key-value pairs needed for reconstructing frames from data streams.

    Parameters
    ----------
    device: str
        Interface hardware used for receiving data.
        Current options are "OK" (Opal Kelly XEM 7310) and "UART" (generic UART-USB converters).
        Only "OK" is supported at the moment.
    bitstream: str, optional
        Required when device is "OK".
        The configuration bitstream file to upload to the Opal Kelly board.
        This uploads a Manchester decoder HDL and different bitstream files are required
        to configure different data rates and bit polarity.
        This is a binary file synthesized using Vivado,
        and details for generating this file will be provided in later updates.
    port: str, optional
        Required when device is "UART".
        COM port connected to the UART-USB converter.
    baudrate: Optional[int]
        Required when device is "UART".
        Baudrate of the connection to the UART-USB converter.
    frame_width: int
        Frame width of transferred image. This is used to reconstruct image.
    frame_height: int
        Frame height of transferred image. This is used to reconstruct image.
    fs: int
        Framerate of acquired stream
    preamble: str
        32-bit preamble used to locate the start of each buffer.
        The header and image data follows this preamble.
        This is used as a hex but imported as a string because yaml doesn't support hex format.
    header_len : int, optional
        Length of header in bits. (For 32-bit words, 32 * number of words)
        This is useful when not all the variable/words in the header are defined in
        :class:`.MetadataHeaderFormat`.
        The user is responsible to ensure that `header_len` is larger than the largest bit
        position defined in :class:`.MetadataHeaderFormat`
        otherwise unexpected behavior might occur.
    pix_depth : int, optional
        Bit-depth of each pixel, by default 8.
    buffer_block_length: int
        Defines the data buffer structure. This value needs to match the Miniscope firmware.
        Number of blocks per each data buffer.
        This is required to calculate the number of pixels contained in one data buffer.
    block_size: int
        Defines the data buffer structure. This value needs to match the Miniscope firmware.
        Number of 32-bit words per data block.
        This is required to calculate the number of pixels contained in one data buffer.
    num_buffers: int
        Defines the data buffer structure. This value needs to match the Miniscope firmware.
        This is the number of buffers that the source microcontroller cycles around.
        This isn't strictly required for data reconstruction but useful for debugging.
    reverse_header_bits : bool, optional
        If True, reverse the bits within each byte of the header.
        Default is False.
    reverse_header_bytes : bool, optional
        If True, reverse the byte order within each 32-bit word of the header.
        This is used for handling endianness in systems where the byte order needs to be swapped.
        Default is False.
    reverse_payload_bits : bool, optional
        If True, reverse the bits within each byte of the payload.
        Default is False.
    reverse_payload_bytes : bool, optional
        If True, reverse the byte order within each 32-bit word of the payload.
        This is used for handling endianness in systems where the byte order needs to be swapped.
        Default is False.

    ..todo::
        Move port (for USART) to a user config area. This should make this pure device config.
    """

    device: Literal["OK", "UART"]
    bitstream: Optional[Path] = None
    port: Optional[str] = None
    baudrate: Optional[int] = None
    frame_width: int
    frame_height: int
    fs: int = 20
    preamble: bytes
    header_len: int
    pix_depth: int = 8
    buffer_block_length: int
    block_size: int
    num_buffers: int
    reverse_header_bits: bool = False
    reverse_header_bytes: bool = False
    reverse_payload_bits: bool = False
    reverse_payload_bytes: bool = False

    @field_validator("preamble", mode="before")
    def preamble_to_bytes(cls, value: Union[str, bytes, int]) -> bytes:
        """
        Cast ``preamble`` to bytes.

        Args:
            value (str, bytes, int): Recast from `str` (in yaml like ``preamble: "0x12345"`` )
                or `int` (in yaml like `preamble: 0x12345`

        Returns:
            bytes
        """
        if isinstance(value, str):
            return bytes.fromhex(value)
        elif isinstance(value, int):
            return bytes.fromhex(hex(value)[2:])
        else:
            return value

    @field_validator("bitstream", mode="after")
    def resolve_relative(cls, value: Path) -> Path:
        """
        If we are given a relative path to a bitstream, resolve it relative to
        the device path
        """
        if not value.is_absolute():
            value = DEVICE_DIR / value
        return value
