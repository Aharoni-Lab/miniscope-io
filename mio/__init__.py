"""
I/O SDK for UCLA Miniscopes
"""

from importlib import metadata
from pathlib import Path

from mio.logging import init_logger
from mio.models.config import Config

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = DATA_DIR / "config"
DEVICE_DIR = BASE_DIR / "devices"

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "CONFIG_DIR",
    "Config",
    "init_logger",
]

try:
    __version__ = metadata.version("mio")
except metadata.PackageNotFoundError:  # pragma: nocover
    __version__ = None
