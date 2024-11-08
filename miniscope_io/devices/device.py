"""
ABC for 
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Union

from miniscope_io.models import MiniscopeConfig, MiniscopeIOModel, Pipeline, PipelineConfig

if TYPE_CHECKING:
    from miniscope_io.models.pipeline import Sink, Source, Transform


class DeviceConfig(MiniscopeConfig):
    """
    Abstract base class for device configuration
    """

    id: Union[str, int]
    """(Locally) unique identifier for this device"""
    pipeline: PipelineConfig = PipelineConfig()


class Device(MiniscopeIOModel):
    """
    Abstract base class for devices.

    Currently a placeholder to allow room for expansion/renaming in the future
    """

    pipeline: Pipeline
    config: DeviceConfig

    @abstractmethod
    def init(self) -> None:
        """
        Initialize the device and prepare it for use.

        Should be called as part of the :meth:`.start` routine
        """

    @abstractmethod
    def deinit(self) -> None:
        """
        Deinitialize/teardown resources when stopping.

        Should be called as part of the :meth;`.stop` routine
        """

    @abstractmethod
    def start(self) -> None:
        """
        Start processing data with the :attr:`.pipeline`

        This method should call :meth:`.Device.init` or otherwise ensure
        that the hardware devices are prepared to run, and then run them.

        This method should be nonblocking and return immediately.
        If a blocking call is required, a second call to :meth:`.Device.join`
        should be made.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Start processing data with the :attr:`.pipeline`

        This method should call the :meth:`.deinit` method to free resources,
        and provide notice to any threads waiting on
        :meth:`.Device.join` once the pipeline has finished processing and
        resources are freed.
        """

    @abstractmethod
    def join(self) -> None:
        """
        Await the completion of data processing after :meth:`.stop` is called.

        This method should be thread or process safe if the device class
        makes use of threads or processes.
        """

    @abstractmethod
    def configure(self, config: DeviceConfig) -> None:
        """
        Write a new device configuration to the device.

        Fields in the DeviceConfig may correspond to attributes used by
        the device class or attributes of any of the nodes in its
        :attr:`.Device.pipeline` . Typically it is easier to store the
        configuration for a pipeline node in the relevant `node` section of its
        :attr:`.DeviceConfig.pipeline` object, but Devices may use their
        :class:`.DeviceConfig` , :meth:`.Device.configure`, :meth:`.Device.get`,
        and :meth:`.Device.set` methods as convenience methods for accessing
        commonly used pipeline node attributes.

        This method should also update the instance :attr:`.config`
        """

    @abstractmethod
    def get(self, key: str) -> Any:
        """
        Get a configuration value from the device.

        This should **not** be used as a means of accessing data from the
        pipeline. Devices may provide other convenience methods that
        tap into a ``Queue`` sink or otherwise provide programmatic
        access to a pipeline, but should not do so with this method.

        See :meth:`.Device.configure` for further implementation details

        Args:
            key (str): The name of the value to get
        """

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value from the device.

        See :meth:`.Device.configure` for implementation details

        Args:
            key (str): The name of the value to get
        """

    @property
    def sources(self) -> dict[str, "Source"]:
        """Convenience method to access :attr:`.Pipeline.sources`"""
        return self.pipeline.sources

    @property
    def transforms(self) -> dict[str, "Transform"]:
        """Convenience method to access :attr:`.Pipeline.transforms`"""
        return self.pipeline.transforms

    @property
    def sinks(self) -> dict[str, "Sink"]:
        """Convenience method to access :attr:`.Pipeline.sinks`"""
        return self.pipeline.sinks
