# Object Model

## Devices

A "{class}`.Device`" is the top-level class that one is expected to interact with when recording 
data.

It encapsulates a {class}`.Pipeline` object that parameterizes one of several
{class}`.Source` nodes (like the {class}`.okDev`, {class]`.SDCard`, etc.),
zero-to-several {class}`.ProcessingNode`s that transform the source ouput,
and then one or several {class}`.Sink` nodes for saving data, plotting, and so on.
 
```{autoclasstree} miniscope_io.devices.Device miniscope_io.devices.Camera miniscope_io.devices.Miniscope 
:namespace: miniscope_io
```  

## Pipeline

A {class}`.Pipeline` is the basic unit of data processing in miniscope-io.

A {class}`.Pipeline` contains a set of {class}`.Node`s, which have three root types:

- {class}`.Source` nodes have outputs but no inputs
- {class}`.Sink` nodes have inputs but no outputs
- {class}`.ProcessingNode`s have both inputs and outputs

Nodes can be connected to any number of `input` or `output` nodes,
and it is the responsibility of the {class}`.Pipeline` class to orchestrate
their run: launching them in a threadqueue, passing data between them, etc.

{class}`.Node`s should not directly call each other, and instead implement
their {meth}`.Node.process` method as a "pure"-ish[^pureish] function that takes
data as input and returns data as output without knowledge of the nodes
that are connected to it.

```{autoclasstree} miniscope_io.models.PipelineModel miniscope_io.models.Node miniscope_io.models.Source miniscope_io.models.Sink miniscope_io.models.ProcessingNode miniscope_io.models.Pipeline
:namespace: miniscope_io
```  

## Config

```{todo}
Complete configuration documentation:
- Sources of config - user dir, prepackaged, etc.
- Types of config - device, session, etc.
```

[^pureish]: As in nodes can be stateful and use their instance attributes,
  but should not rely on side-effects, implement their own queues, etc.