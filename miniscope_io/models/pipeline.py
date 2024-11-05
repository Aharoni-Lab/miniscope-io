"""
Base ABCs for pipeline classes
"""

from abc import abstractmethod
from typing import ClassVar, Generic, TypeVar, Union

from pydantic import Field

from miniscope_io.models.models import PipelineModel

T = TypeVar("T")
"""
Input Type typevar
"""
U = TypeVar("U")
"""
Output Type typevar
"""


class Node(PipelineModel):
    """A node within a processing pipeline"""


class Source(Node, Generic[U]):
    """A source of data in a processing pipeline"""

    output_type: ClassVar[type[U]]
    outputs: list[Union["Sink", "ProcessingNode"]] = Field(default_factory=list)

    @abstractmethod
    def process(self) -> U:
        """
        Process some data, returning an output.


        .. note::

            The `process` method should not directly call or pass
            data to subscribed output nodes, but instead return the output
            and allow a containing pipeline class to handle dispatching data.

        """


class Sink(Node, Generic[T]):
    """A sink of data in a processing pipeline"""

    input_type: ClassVar[type[T]]
    inputs: list[Union["Source", "ProcessingNode"]] = Field(default_factory=list)

    @abstractmethod
    def process(self, data: T) -> None:
        """
        Process some incoming data, returning None

        .. note::

            The `process` method should not directly be called or passed data,
            but instead should be called by a containing pipeline class.

        """


class ProcessingNode(Node, Generic[T, U]):
    """
    An intermediate processing node that transforms some input to output
    """

    input_type: ClassVar[type[T]]
    inputs: list[Union["Source", "ProcessingNode"]] = Field(default_factory=list)
    output_type: ClassVar[type[U]]
    outputs: list[Union["Sink", "ProcessingNode"]] = Field(default_factory=list)

    @abstractmethod
    def process(self, data: T) -> U:
        """
        Process some incoming data, yielding a transformed output

        .. note::

            The `process` method should not directly call or be called by
            output or input nodes, but instead return the output
            and allow a containing pipeline class to handle dispatching data.

        """


class Pipeline(PipelineModel):
    """
    A graph of nodes transforming some input source(s) to some output sink(s)
    """

    sources: list["Source"] = Field(default_factory=list)
    processing_nodes: list["ProcessingNode"] = Field(default_factory=list)
    sinks: list["Sink"] = Field(default_factory=list)

    @abstractmethod
    def process(self) -> None:
        """
        Process one step of data from each of the sources,
        passing intermediate data to any subscribed nodes in a chain.

        The `process` method should not return anything except a to-be-implemented
        result/status object, as any data intended to be received/processed by
        downstream objects should be accessed via a :class:`.Sink` .
        """
