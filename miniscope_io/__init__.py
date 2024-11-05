"""
I/O SDK for UCLA Miniscopes
"""

from pathlib import Path

from miniscope_io.io import SDCard
from miniscope_io.logging import init_logger
from miniscope_io.models.config import Config

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = DATA_DIR / "config"
SOURCES_DIR = BASE_DIR / "sources"

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "CONFIG_DIR",
    "Config",
    "SDCard",
    "init_logger",
]
