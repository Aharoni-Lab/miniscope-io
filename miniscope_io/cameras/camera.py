"""
ABCs for Camera and Miniscope source classes
"""

from miniscope_io.models import Source


class Camera(Source):
    """
    A data source that captures images, often in a sequence known as a "video"
    """


class Miniscope(Camera):
    """
    A miniature microscope
    """
