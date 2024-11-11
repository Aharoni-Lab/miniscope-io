"""
File-based data sources
"""

from miniscope_io.models.pipeline import Source


class FileSource(Source):
    """
    Generic parent class for file sources
    """


class BinaryLayout:
    """Layout for binary files"""

    pass


class BinaryFileSource(FileSource):
    """
    Structured binary file that has

    * a global header with config values
    * a series of buffers, each containing a

        * buffer header - with metadata for that buffer and
        * buffer data - the data for that buffer

    The source thus has two configurations

    * the ``config`` - getter and setter for the actual configuration values of the source
    * the ``layout`` - how the configuration and data are laid out within the file.
    """
