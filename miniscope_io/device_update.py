"""
Update miniscope device configuration, such as LED, GAIN, etc.
"""

import time
from typing import Optional

import serial
import serial.tools.list_ports

from miniscope_io.logging import init_logger
from miniscope_io.models.devupdate import DevUpdateCommand

logger = init_logger(name="device_update", level="INFO")


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
