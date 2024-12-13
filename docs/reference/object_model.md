# Object Model

## Devices

A "{class}`.Device`" is the top-level class that one is expected to interact with when recording 
data.

It encapsulates a {class}`.Pipeline` object that parameterizes one of several
{class}`.Source` nodes (like the {class}`.okDev`, {class]`.SDCard`, etc.),
zero-to-several {class}`.Transform` nodes that transform the source ouput,
and then one or several {class}`.Sink` nodes for saving data, plotting, and so on.
 
```{autoclasstree} mio.devices.Device mio.devices.Camera mio.devices.Miniscope 
:namespace: mio
```  

## Pipeline

A {class}`.Pipeline` is the basic unit of data processing in miniscope-io.

A {class}`.Pipeline` contains a set of {class}`.Node`s, which have three root types:

- {class}`.Source` nodes have outputs but no inputs
- {class}`.Sink` nodes have inputs but no outputs
- {class}`.Transform` nodes have both inputs and outputs

Nodes can be connected to any number of `input` or `output` nodes,
and it is the responsibility of the {class}`.Pipeline` class to orchestrate
their run: launching them in a threadqueue, passing data between them, etc.

{class}`.Node`s should not directly call each other, and instead implement
their {meth}`.Node.process` method as a "pure"-ish[^pureish] function that takes
data as input and returns data as output without knowledge of the nodes
that are connected to it.

```{autoclasstree} mio.models.PipelineModel mio.models.Node mio.models.Source mio.models.Sink mio.models.ProcessingNode mio.models.Pipeline
:namespace: mio
```  

## Config

```{todo}
Complete configuration documentation:
- Sources of config - user dir, prepackaged, etc.
- Types of config - device, session, etc.
```

[^pureish]: As in nodes can be stateful and use their instance attributes,
  but should not rely on side-effects, implement their own queues, etc.