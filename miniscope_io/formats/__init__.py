"""
Instantiations of :class:`~.miniscope_io.models.MiniscopeConfig` models
that describe fixed per-device configurations for the generic config
models in :mod:`~.miniscope_io.models.stream` et al.
"""

from miniscope_io.formats.sdcard import WireFreeSDLayout, WireFreeSDLayout_Battery

__all__ = ["WireFreeSDLayout", "WireFreeSDLayout_Battery"]
