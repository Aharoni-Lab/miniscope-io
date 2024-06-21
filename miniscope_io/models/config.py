from typing import Optional, Literal
from pathlib import Path

from pydantic import field_validator, model_validator, Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from miniscope_io.models import MiniscopeIOModel

_default_basedir = Path().home() / '.config' / 'miniscope_io'
LOG_LEVELS = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']


class LogConfig(MiniscopeIOModel):
    """
    Configuration for logging
    """
    level: LOG_LEVELS = 'INFO'
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
    file_size: int = 2**22 # roughly 4MB
    """
    Maximum size of log files (bytes)
    """

    @field_validator('level', 'level_file', 'level_stdout', mode="before")
    @classmethod
    def uppercase_levels(cls, value: Optional[str] = None):
        if value is not None:
            value = value.upper()
        return value

    @model_validator(mode='after')
    def inherit_base_level(self) -> 'LogConfig':
        """
        If loglevels for specific output streams are unset, set from base :attr:`.level`
        """
        levels = ('level_file', 'level_stdout')
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
        description="Base directory to store configuration and other temporary files, other paths are relative to this by default"
    )
    log_dir: Path = Field(
        Path('logs'),
        description="Location to store logs"
    )
    logs: LogConfig = Field(
        LogConfig(),
        description="Additional settings for logs"
    )


    @field_validator('base_dir', mode='before')
    @classmethod
    def folder_exists(cls, v: Path) -> Path:
        v = Path(v)
        v.mkdir(exist_ok=True, parents=True)

        assert v.exists(), f'{v} does not exist!'
        return v

    @model_validator(mode='after')
    def paths_relative_to_basedir(self) -> 'Config':
        paths = ('log_dir',)
        for path_name in paths:
            path = getattr(self, path_name) # type: Path
            if not path.is_absolute():
                path = self.base_dir / path
                setattr(self, path_name, path)
            path.mkdir(exist_ok=True)
            assert path.exists()
        return self


    model_config = SettingsConfigDict(
        env_prefix='miniscope_io_',
        env_file='.env',
        env_nested_delimiter='__',
        extra='ignore'
    )