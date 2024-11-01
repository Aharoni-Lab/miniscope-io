"""
Models for device update commands.
"""

from enum import Enum

import serial.tools.list_ports
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


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
    DEVICE = 99  # for device commands


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
            assert value in [DeviceCommand.RESTART.value], "For DEVICE, value must be in [200]"
        elif (
            target == UpdateTarget.ROI_X
            or target == UpdateTarget.ROI_Y
            or target == UpdateTarget.ROI_WIDTH
            or target == UpdateTarget.ROI_HEIGHT
            or target == UpdateTarget.EWL
        ):
            pass  # Need to implement
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
