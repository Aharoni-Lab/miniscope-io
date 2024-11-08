"""
ABCs for Camera and Miniscope source classes
"""

from abc import abstractmethod
from typing import Optional, Union

from miniscope_io.devices.device import Device, DeviceConfig
from miniscope_io.types import BBox, Resolution


class CameraConfig(DeviceConfig):
    """
    Configuration for a :class:`.Camera`
    """

    fps: int
    exposure: float
    resolution: Resolution
    focus: Optional[float] = None
    analog_gain: Optional[float] = None
    digital_gain: Optional[float] = None
    binning: Optional[Union[int, tuple[int, int]]] = None
    roi: Optional[BBox] = None


class Camera(Device):
    """
    A data source that captures images, often in a sequence known as a "video"

    For each of the abstract properties:
    * Subclasses **should** check the value given to a setter for correctness, e.g.
        if an FPS is disallowed for a given capture mode.
        The value should *not* be coerced except for trivial value-neutral
        type conversion like ``int(1.0)``, and instead a
        :class:`.ConfigurationError` should be raised in the case of an invalid value.
    * Subclasses **may** disallow setting values during capture,
        or implement it by dynamically stopping and starting capture,
        but they should warn the user if they do.
    * Subclasses **may** emit a `NotImplementedError` in case setting some value
        is impossible for that device.

    """

    config: CameraConfig

    @property
    @abstractmethod
    def fps(self) -> Union[int, float]:
        """
        The current capture framerate as frames per second of the camera.

        Returns:
            Union[int, float]: The FPS!
        """

    @fps.setter
    @abstractmethod
    def fps(self, value: Union[int, float]) -> None:
        """
        Set the capturing framerate.

        Args:
            value (Union[int, float]): Value to set

        Raises:
            :class:`.ConfigurationError` when an incorrect value is given
        """

    @property
    @abstractmethod
    def exposure(self) -> int:
        """
        Returns:
            int:
        """

    @exposure.setter
    @abstractmethod
    def exposure(self, value: int) -> None:
        """
        Args:
            value (int): Value to set
        """

    @property
    @abstractmethod
    def resolution(self) -> Resolution:
        """
        Returns:
            Resolution:
        """

    @resolution.setter
    @abstractmethod
    def resolution(self, value: Resolution) -> None:
        """
        Args:
            value (Resolution): Value to set
        """

    @property
    def focus(self) -> float:
        """
        Returns:
            float:

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("focus getter is not implemented")

    @focus.setter
    def focus(self, value: float) -> None:
        """
        Args:
            value (float): Value to set

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("focus setter is not implemented")

    @property
    def analog_gain(self) -> float:
        """
        Returns:
            float:

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("analog_gain getter is not implemented")

    @analog_gain.setter
    def analog_gain(self, value: float) -> None:
        """
        Args:
            value (float): Value to set

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("analog_gain setter is not implemented")

    @property
    def digital_gain(self) -> float:
        """
        Returns:
            float:

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("digital_gain getter is not implemented")

    @digital_gain.setter
    def digital_gain(self, value: float) -> None:
        """
        Args:
            value (float): Value to set

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("digital_gain setter is not implemented")

    @property
    def binning(self) -> Union[int, tuple[int, int]]:
        """
        Returns:
            Union[int, tuple[int,int]]:

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("binning getter is not implemented")

    @binning.setter
    def binning(self, value: Union[int, tuple[int, int]]) -> None:
        """
        Args:
            value (Union[int, tuple[int,int]]): Value to set

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("binning setter is not implemented")

    @property
    def roi(self) -> BBox:
        """
        Returns:
            BBox:

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("roi getter is not implemented")

    @roi.setter
    def roi(self, value: BBox) -> None:
        """
        Args:
            value (BBox): Value to set

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("roi setter is not implemented")


class MiniscopeConfig(CameraConfig):
    """Configuration of a miniscope"""

    excitation: float


class Miniscope(Camera):
    """
    Abstract base class for a miniature microscope!
    """

    config: MiniscopeConfig

    @property
    @abstractmethod
    def excitation(self) -> float:
        """
        Returns:
            float:
        """

    @excitation.setter
    @abstractmethod
    def excitation(self, value: float) -> None:
        """
        Args:
            value (float): Value to set
        """
