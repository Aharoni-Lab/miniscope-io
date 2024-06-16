import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Union
from pathlib import Path

from rich.logging import RichHandler

from miniscope_io.models.config import Config, LOG_LEVELS

def init_logger(
        name: str,
        log_dir: Union[Optional[Path], bool] = None,
        level: Optional[LOG_LEVELS] = None,
        file_level: Optional[LOG_LEVELS] = None,
        log_file_n: Optional[int] = None,
        log_file_size: Optional[int] = None
    ):
    """
    Make a logger.

    Log to a set of rotating files in the ``log_dir`` according to ``name`` ,
    as well as using the :class:`~rich.RichHandler` for pretty-formatted stdout logs.

    Args:
        name (str): Name of this logger. Ideally names are hierarchical
            and indicate what they are logging for, eg. ``miniscope_io.sdcard``
            and don't contain metadata like timestamps, etc. (which are in the logs)
        log_dir (:class:`pathlib.Path`): Directory to store file-based logs in. If ``None``,
            get from :class:`.Config`. If ``False`` , disable file logging.
        level (:class:`.LOG_LEVELS`): Level to use for stdout logging. If ``None`` ,
            get from :class:`.Config`
        file_level (:class:`.LOG_LEVELS`): Level to use for file-based logging.
             If ``None`` , get from :class:`.Config`
        log_file_n (int): Number of rotating file logs to use.
            If ``None`` , get from :class:`.Config`
        log_file_size (int): Maximum size of logfiles before rotation.
            If ``None`` , get from :class:`.Config`

    Returns:
        :class:`logging.Logger`
    """
    config = Config()
    if log_dir is None:
        log_dir = config.log_dir
    if level is None:
        level = config.logs.level_stdout
    if file_level is None:
        file_level = config.logs.level_file
    if log_file_n is None:
        log_file_n = config.logs.file_n
    if log_file_size is None:
        log_file_size = config.logs.file_size

    if not name.startswith('miniscope_io'):
        name = 'miniscope_io.' + name

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add handlers for stdout and file
    if log_dir is not False:
        logger.addHandler(_file_handler(
            name, file_level, log_dir, log_file_n, log_file_size
        ))

    logger.addHandler(_rich_handler())

    return logger

def _file_handler(
        name: str,
        file_level: LOG_LEVELS,
        log_dir: Path,
        log_file_n: int = 5,
        log_file_size: int = 2**22
    ) -> RotatingFileHandler:
    # See init_logger for arg docs

    filename = Path(log_dir) / '.'.join([name, 'log'])
    file_handler = RotatingFileHandler(
        str(filename),
        mode='a',
        maxBytes=log_file_size,
        backupCount=log_file_n
    )
    file_formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    return file_handler

def _rich_handler() -> RichHandler:
    rich_handler = RichHandler(rich_tracebacks=True, markup=True)
    rich_formatter = logging.Formatter(
        "[bold green]\[%(name)s][/bold green] %(message)s",
        datefmt='[%y-%m-%dT%H:%M:%S]'
    )
    rich_handler.setFormatter(rich_formatter)
    return rich_handler

