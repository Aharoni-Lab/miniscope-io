"""
Models for a data stream from a miniscope device: header formats,
containers, etc.
"""

from collections.abc import Sequence
from typing import Type, TypeVar

from miniscope_io.models import Container, MiniscopeConfig


class BufferHeaderFormat(MiniscopeConfig):
    """
    Format model used to parse header at the beginning of every buffer.
    """

    linked_list: int
    frame_num: int
    buffer_count: int
    frame_buffer_count: int
    write_buffer_count: int
    dropped_buffer_count: int
    timestamp: int
    write_timestamp: int


_T = TypeVar("_T", bound="BufferHeader")


class BufferHeader(Container):
    """
    Container for the data stream's header, structured by :class:`.MetadataHeaderFormat`
    """

    linked_list: int
    frame_num: int
    buffer_count: int
    frame_buffer_count: int
    write_buffer_count: int
    dropped_buffer_count: int
    timestamp: int
    write_timestamp: int

    @classmethod
    def from_format(
        cls: Type[_T], vals: Sequence, format: BufferHeaderFormat, construct: bool = False
    ) -> _T:
        """
        Instantiate a buffer header from linearized values (eg. in an ndarray or list)
        and an associated format that tells us what index the model values are found
        in that data.

        Args:
            vals (list, :class:`numpy.ndarray` ): Indexable values to cast to the header model
            format (:class:`.BufferHeaderFormat` ): Format used to index values
            construct (bool): If ``True`` , use :meth:`~pydantic.BaseModel.model_construct`
                to create the model instance (ie. without validation, but faster).
                Default: ``False``

        Returns:
            :class:`.BufferHeader`
        """

        header_data = dict()
        for hd, header_index in format.model_dump().items():
            if header_index is not None:
                header_data[hd] = vals[header_index]

        if construct:
            return cls.model_construct(**header_data)
        else:
            return cls(**header_data)
