"""
Base and meta model classes.

All the models here should be empty - these are abstract parent classes
to group child classes in a semantic inheritance hierarchy.

More specific models should either be defined in their own
module within the `miniscope_io.models` package or in their own
package.
"""

from pydantic import BaseModel


class MiniscopeIOModel(BaseModel):
    """
    Root model for all miniscope_io models
    """


class MiniscopeConfig(MiniscopeIOModel):
    """
    Root model for all configuration models,
    eg. those that are effectively static at runtime.

    .. note::
        Not named ``Config`` or ``BaseConfig`` because those are both
        in use already.

    See also: :class:`.Container`
    """


class Container(MiniscopeIOModel):
    """
    Root model for models intended to be used as runtime data containers,
    eg. those that actually carry data from a buffer, rather than
    those that configure positions within a header.

    See also: :class:`.MiniscopeConfig`
    """


class PipelineModel(MiniscopeIOModel):
    """A model used in a processing pipeline"""
