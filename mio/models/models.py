"""
Base and meta model classes.
"""

from pydantic import BaseModel


class MiniscopeIOModel(BaseModel):
    """
    Root model for all mio models
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
