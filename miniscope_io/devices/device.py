"""
ABC for 
"""

from abc import abstractmethod

from miniscope_io.models import MiniscopeConfig, MiniscopeIOModel, Pipeline


class DeviceConfig(MiniscopeConfig):
    """
    Abstract base class for device configuration
    """


class Device(MiniscopeIOModel):
    """
    Abstract base class for devices.

    Currently a placeholder to allow room for expansion/renaming in the future
    """

    pipeline: Pipeline
    config: DeviceConfig

    @abstractmethod
    def start(self) -> None:
        """
        Start processing data with the :attr:`.pipeline`
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Start processing data with the :attr:`.pipeline`
        """

    @abstractmethod
    def join(self) -> None:
        """
        Await the completion of data processing after :meth:`.stop` is called.
        """
