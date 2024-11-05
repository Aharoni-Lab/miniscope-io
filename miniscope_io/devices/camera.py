"""
ABCs for Camera and Miniscope source classes
"""

from miniscope_io.devices.device import Device


class Camera(Device):
    """
    A data source that captures images, often in a sequence known as a "video"
    """


class Miniscope(Camera):
    """
    A miniature microscope
    """
