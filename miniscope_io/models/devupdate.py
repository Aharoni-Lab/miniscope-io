"""
Models for device update commands.
"""

from enum import Enum

import serial.tools.list_ports
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class DeviceCommand(Enum):
    """Commands for device."""

    REBOOT = 200


class UpdateCommandDefinitions:
    """
    Definitions of Bit masks and headers for remote update commands.
    """

    # Header to indicate target/value.
    # It probably won't be used in other places so defined here.
    id_header = 0b00000000
    target_header = 0b11000000
    LSB_header = 0b01000000
    MSB_header = 0b10000000
    LSB_value_mask = 0b000000111111  # value below 12-bit
    MSB_value_mask = 0b111111000000  # value below 12-bit
    reset_byte = 0b11111111


class UpdateTarget(Enum):
    """
    Targets to update. Needs to be under 6-bit.
    """

    LED = 0
    GAIN = 1
    ROI_X = 2
    ROI_Y = 3
    ROI_WIDTH = 4  # not implemented
    ROI_HEIGHT = 5  # not implemented
    EWL = 6  # not implemented
    DEVICE = 50  # for device commands


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
        elif target == UpdateTarget.DEVICE:
            assert value in [DeviceCommand.REBOOT.value], "For DEVICE, value must be in [200]"
        elif target in UpdateTarget:
            raise NotImplementedError()
        else:
            raise ValueError(f"{target} is not a valid update target, need an instance of UpdateTarget")
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
