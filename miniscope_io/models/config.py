"""
Module-global configuration models
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from miniscope_io.models import MiniscopeIOModel

_default_basedir = Path().home() / ".config" / "miniscope_io"
LOG_LEVELS = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class LogConfig(MiniscopeIOModel):
    """
    Configuration for logging
    """

    level: LOG_LEVELS = "INFO"
    """
    Severity of log messages to process.
    """
    level_file: Optional[LOG_LEVELS] = None
    """
    Severity for file-based logging. If unset, use ``level``
    """
    level_stdout: Optional[LOG_LEVELS] = None
    """
    Severity for stream-based logging. If unset, use ``level``
    """
    file_n: int = 5
    """
    Number of log files to rotate through
    """
    file_size: int = 2**22  # roughly 4MB
    """
    Maximum size of log files (bytes)
    """

    @field_validator("level", "level_file", "level_stdout", mode="before")
    @classmethod
    def uppercase_levels(cls, value: Optional[str] = None) -> Optional[str]:
        """
        Ensure log level strings are uppercased
        """
        if value is not None:
            value = value.upper()
        return value

    @model_validator(mode="after")
    def inherit_base_level(self) -> "LogConfig":
        """
        If loglevels for specific output streams are unset, set from base :attr:`.level`
        """
        levels = ("level_file", "level_stdout")
        for level_name in levels:
            if getattr(self, level_name) is None:
                setattr(self, level_name, self.level)
        return self


class Config(BaseSettings):
    """
    Runtime configuration for miniscope-io.

    See https://docs.pydantic.dev/latest/concepts/pydantic_settings/

    Set values either in an ``.env`` file or using environment variables
    prefixed with ``MINISCOPE_IO_*``. Values in nested models are separated with ``__`` ,
    eg. ``MINISCOPE_IO_LOGS__LEVEL``

    See ``.env.example`` in repository root

    Paths are set relative to ``base_dir`` by default, unless explicitly specified.


    """

    base_dir: Path = Field(
        _default_basedir,
        description="Base directory to store configuration and other temporary files, "
        "other paths are relative to this by default",
    )
    log_dir: Path = Field(Path("logs"), description="Location to store logs")
    logs: LogConfig = Field(LogConfig(), description="Additional settings for logs")
    csvwriter_buffer: int = Field(
        100,
        description="Buffer length for CSV writer",
        json_schema_extra={"env": "MINISCOPE_IO_CSVWRITER_BUFFER"},
    )
    serial_buffer_queue_size: int = Field(
        10,
        description="Buffer length for serial data reception in streamDaq",
        json_schema_extra={"env": "MINISCOPE_IO_SERIAL_BUFFER"},
    )
    frame_buffer_queue_size: int = Field(
        5,
        description="Buffer length for storing frames in streamDaq",
        json_schema_extra={"env": "MINISCOPE_IO_FRAME_BUFFER"},
    )
    image_buffer_queue_size: int = Field(
        5,
        description="Buffer length for storing images in streamDaq",
        json_schema_extra={"env": "MINISCOPE_IO_IMAGE_BUFFER"},
    )
    stream_header_plot_update_ms: int = Field(
        1000,
        description="Update rate for stream header plots in milliseconds",
        json_schema_extra={"env": "MINISCOPE_IO_STREAM_HEADER_PLOT_UPDATE_MS"},
    )
    stream_header_plot_history: int = Field(
        500,
        description="Number of stream headers to plot",
        json_schema_extra={"env": "MINISCOPE_IO_STREAM_HEADER_PLOT_HISTORY"},
    )
    stream_header_plot_key: str = Field(
        "timestamp,buffer_count,frame_buffer_count",
        description="Keys for plotting stream headers",
        json_schema_extra={"env": "MINISCOPE_IO_STREAM_HEADER_PLOT_KEY"},
    )


    @field_validator("base_dir", mode="before")
    @classmethod
    def folder_exists(cls, v: Path) -> Path:
        """Ensure base_dir exists, make it otherwise"""
        v = Path(v)
        v.mkdir(exist_ok=True, parents=True)

        assert v.exists(), f"{v} does not exist!"
        return v

    @model_validator(mode="after")
    def paths_relative_to_basedir(self) -> "Config":
        """If relative paths are given, make them absolute relative to ``base_dir``"""
        paths = ("log_dir",)
        for path_name in paths:
            path = getattr(self, path_name)  # type: Path
            if not path.is_absolute():
                path = self.base_dir / path
                setattr(self, path_name, path)
            path.mkdir(exist_ok=True)
            assert path.exists()
        return self

    model_config = SettingsConfigDict(
        env_prefix="miniscope_io_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )
