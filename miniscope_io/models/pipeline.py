"""
Base ABCs for pipeline classes
"""

from abc import abstractmethod
from typing import ClassVar, Final, Generic, Self, TypeVar, Union, final

from pydantic import Field

from miniscope_io.exceptions import ConfigurationMismatchError
from miniscope_io.models.models import MiniscopeConfig, PipelineModel

T = TypeVar("T")
"""
Input Type typevar
"""
U = TypeVar("U")
"""
Output Type typevar
"""


class NodeConfig(MiniscopeConfig):
    """Configuration for a single processing node"""

    type_: str = Field(..., alias="type")
    """
    Shortname of the type of node this configuration is for.
    
    Subclasses should override this with a default.
    """

    id: str
    """The unique identifier of the node"""
    inputs: list[str] = Field(default_factory=list)
    """List of Node IDs to be used as input"""
    outputs: list[str] = Field(default_factory=list)
    """List of Node IDs to be used as output"""


class PipelineConfig(MiniscopeConfig):
    """
    Configuration for the nodes within a pipeline
    """

    nodes: dict[str, NodeConfig] = Field(default_factory=dict)
    """The nodes that this pipeline configures"""


class Node(PipelineModel, Generic[T, U]):
    """A node within a processing pipeline"""

    type_: ClassVar[str]
    """
    Shortname for this type of node to match configs to node types
    """

    id: str
    """Unique identifier of the node"""
    config: NodeConfig

    input_type: ClassVar[type[T]]
    inputs: dict[str, Union["Source", "ProcessingNode"]] = Field(default_factory=dict)
    output_type: ClassVar[type[U]]
    outputs: dict[str, Union["Sink", "ProcessingNode"]] = Field(default_factory=dict)

    @abstractmethod
    def start(self) -> None:
        """
        Start producing, processing, or receiving data
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stop producing, processing, or receiving data
        """

    @classmethod
    def from_config(cls, config: NodeConfig) -> Self:
        """
        Create a node from its config
        """
        return cls(id=config.id, config=config)

    @classmethod
    @final
    def node_types(cls) -> dict[str, type["Node"]]:
        """
        Map of all imported :attr:`.Node.type_` names to node classes
        """
        node_types = {}
        to_check = cls.__subclasses__()
        while to_check:
            node = to_check.pop()
            if node.type_ in node_types:
                raise ValueError(
                    f"Repeated node type_ identifier: {node.type_}, found in:\n"
                    f"- {node_types[node.type_]}\n- {node}"
                )
            node_types[node.type_] = node
            to_check.extend(node.__subclasses__())
        return node_types


class Source(Node, Generic[T, U]):
    """A source of data in a processing pipeline"""

    inputs: Final[None] = None
    input_type: ClassVar[None] = None

    @abstractmethod
    def process(self) -> U:
        """
        Process some data, returning an output.


        .. note::

            The `process` method should not directly call or pass
            data to subscribed output nodes, but instead return the output
            and allow a containing pipeline class to handle dispatching data.

        """


class Sink(Node, Generic[T, U]):
    """A sink of data in a processing pipeline"""

    output_type: ClassVar[None] = None
    outputs: Final[None] = None

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

    nodes: dict[str, Node] = Field(default_factory=dict)
    """
    Dictionary mapping all nodes from their ID to the instantiated node.
    """

    @property
    def sources(self) -> dict[str, "Source"]:
        """All :class:`.Source` nodes in the processing graph"""
        return {k: v for k, v in self.nodes.items() if isinstance(v, Source)}

    @property
    def processing_nodes(self) -> dict[str, "ProcessingNode"]:
        """All :class:`.ProcessingNode` s in the processing graph"""
        return {k: v for k, v in self.nodes.items() if isinstance(v, ProcessingNode)}

    @property
    def sinks(self) -> dict[str, "Sink"]:
        """All :class:`.Sink` nodes in the processing graph"""
        return {k: v for k, v in self.nodes.items() if isinstance(v, Sink)}

    @abstractmethod
    def process(self) -> None:
        """
        Process one step of data from each of the sources,
        passing intermediate data to any subscribed nodes in a chain.

        The `process` method should not return anything except a to-be-implemented
        result/status object, as any data intended to be received/processed by
        downstream objects should be accessed via a :class:`.Sink` .
        """

    @abstractmethod
    def start(self) -> None:
        """
        Start processing data with the pipeline graph
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stop processing data with the pipeline graph
        """

    @classmethod
    def from_config(cls, config: PipelineConfig) -> Self:
        """
        Instantiate a pipeline model from its configuration
        """
        types = Node.node_types()

        nodes = {k: types[v.type_].from_config(v) for k, v in config.nodes.items()}
        nodes = connect_nodes(nodes)
        return cls(nodes=nodes)


def connect_nodes(nodes: dict[str, Node]) -> dict[str, Node]:
    """
    Provide references to instantiated nodes
    """

    for node in nodes.values():
        if node.config.inputs and node.inputs is None:
            raise ConfigurationMismatchError(
                "inputs found in node configuration, but node type allows no inputs!\n"
                f"node: {node.model_dump()}"
            )
        if node.config.outputs and not hasattr(node, "outputs"):
            raise ConfigurationMismatchError(
                "outputs found in node configuration, but node type allows no outputs!\n"
                f"node: {node.model_dump()}"
            )

        node.inputs.update({id: nodes[id] for id in node.config.inputs})
        node.outputs.update({id: nodes[id] for id in node.config.outputs})
    return nodes
