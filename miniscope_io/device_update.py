"""
Update miniscope device configuration.

.. todo::

    What kind of devices does this apply to?

"""

import time
from enum import Enum
from typing import Optional

import serial
import serial.tools.list_ports
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from miniscope_io.logging import init_logger

logger = init_logger(name="device_update", level="DEBUG")

class DeviceCommand(Enum):
    """Commands for device."""
    RESTART = 200

class UpdateTarget(Enum):
    """Targets to update."""

    LED = 0
    GAIN = 1
    ROI_X = 2
    ROI_Y = 3
    ROI_WIDTH = 4  # not implemented
    ROI_HEIGHT = 5  # not implemented
    EWL = 6  # not implemented
    DEVICE = 99 # for device commands

class DevUpdateCommand(BaseModel):
    """
    Command to update device configuration.
    """

    device_id: int
    port: str
    target: UpdateTarget
    value: int

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_values(cls, values: dict) -> dict:
        """
        Validate values based on target.
        """
        target = values.target
        value = values.value

        if target == UpdateTarget.LED:
            assert 0 <= value <= 100, "For LED, value must be between 0 and 100"
        elif target == UpdateTarget.GAIN:
            assert value in [1, 2, 4], "For GAIN, value must be 1, 2, or 4"
        return values

    @field_validator("port")
    def validate_port(cls, value: str) -> str:
        """
        Validate port.

        Args:
            value: Port to validate.

        Returns:
            Validated port.

        Raises:
            ValueError: If no serial ports found or port not found.
        """
        portlist = list(serial.tools.list_ports.comports())

        if len(portlist) == 0:
            raise ValueError("No serial ports found")
        if value not in [port.device for port in portlist]:
            raise ValueError(f"Port {value} not found")
        return value

    @field_validator("target", mode="before")
    def validate_target(cls, value: str) -> UpdateTarget:
        """
        Validate and convert target string to UpdateTarget Enum type.

        Args:
            value (str): Target to validate.

        Returns:
            UpdateTarget: Validated target as UpdateTarget.

        Raises:
            ValueError: If target not found.
        """
        try:
            return UpdateTarget[value]
        except KeyError as e:
            raise ValueError(f"Target {value} not found.") from e


def DevUpdate(
    target: str,
    value: int,
    device_id: int,
    port: Optional[str] = None,
) -> None:
    """
    IR-based update of device configuration.

    .. note::

        Not tested after separating from stream_daq.py.

    Args:
        device_id: ID of the device. 0 will update all devices.
        port: Serial port to which the device is connected.
        target: What to update on the device (e.g., LED or GAIN).
        value: Value to which the target should be updated.

    Returns:
        None
    """

    if port:
        logger.info(f"Using port {port}")
    else:
        ftdi_port_list = find_ftdi_device()
        if len(ftdi_port_list) == 0:
            raise ValueError("No FTDI devices found.")
        if len(ftdi_port_list) > 1:
            raise ValueError("Multiple FTDI devices found. Please specify the port.")
        if len(ftdi_port_list) == 1:
            port = ftdi_port_list[0]
            logger.info(f"Using port {port}")

    command = DevUpdateCommand(device_id=device_id, port=port, target=target, value=value)
    logger.info(f"Updating {target} to {value} on port {port}")

    # Header to indicate target/value.
    # This should be a bit pattern that is unlikely to be the value.
    id_header = 0b00000000
    target_header = 0b11000000
    LSB_header = 0b01000000
    MSB_header = 0b10000000
    LSB_value_mask = 0b000000111111  # value below 12-bit
    MSB_value_mask = 0b111111000000  # value below 12-bit
    reset_byte = 0b11111111

    try:
        serial_port = serial.Serial(port=command.port, baudrate=2400, timeout=5, stopbits=2)
    except Exception as e:
        logger.exception(e)
        raise e
    logger.info("Open serial port")

    try:
        id_command = (command.device_id + id_header) & 0xFF
        serial_port.write(id_command.to_bytes(1, "big"))
        logger.debug(f"Command: {format(id_command, '08b')}; Device ID: {command.device_id}")
        time.sleep(0.1)

        target_command = (command.target.value + target_header) & 0xFF
        serial_port.write(target_command.to_bytes(1, "big"))
        logger.debug(f"Command: {format(target_command, '08b')}; Target: {command.target.name}")
        time.sleep(0.1)

        value_LSB_command = ((command.value & LSB_value_mask) + LSB_header) & 0xFF
        serial_port.write(value_LSB_command.to_bytes(1, "big"))
        logger.debug(f"Command: {format(value_LSB_command, '08b')}; Value: {command.value} (LSB)")
        time.sleep(0.1)

        value_MSB_command = (((command.value & MSB_value_mask) >> 6) + MSB_header) & 0xFF
        serial_port.write(value_MSB_command.to_bytes(1, "big"))
        logger.debug(f"Command: {format(value_MSB_command, '08b')}; Value: {command.value} (MSB)")
        time.sleep(0.1)

        serial_port.write(reset_byte.to_bytes(1, "big"))

    finally:
        serial_port.close()
        logger.info("Closed serial port")


def find_ftdi_device() -> list:
    """
    Find FTDI devices connected to the computer.
    """
    FTDI_VENDOR_ID = 0x0403
    FTDI_PRODUCT_ID = 0x6001
    ports = serial.tools.list_ports.comports()
    ftdi_ports = []

    for port in ports:
        if port.vid == FTDI_VENDOR_ID and port.pid == FTDI_PRODUCT_ID:
            ftdi_ports.append(port.device)

    return ftdi_ports
