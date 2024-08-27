"""
Models for sink classes
"""

from pydantic import Field

from miniscope_io.models import MiniscopeConfig


class StreamPlotterConfig(MiniscopeConfig):
    """
    Configuration for :class:`miniscope_io.plots.headers.StreamPlotter`
    """

    keys: list[str] = Field(
        description="Keys to specify what fields of the given model to plot",
    )
    update_ms: int = Field(
        1000,
        description="Update rate for stream header plots in milliseconds",
    )
    history: int = Field(
        500,
        description="Number of stream headers to plot",
    )


class CSVWriterConfig(MiniscopeConfig):
    """
    Configuration for :class:`miniscope_io.io.BufferedCSVWriter`
    """

    buffer: int = Field(
        100,
        description="Buffer length for CSV writer",
    )
