import os
from pathlib import Path
from typing import Union, Callable
from datetime import datetime

import pytest
import yaml

from mio.models.mixins import ConfigYAMLMixin

from .fixtures import *

DATA_DIR = Path(__file__).parent / "data"
CONFIG_DIR = DATA_DIR / "config"
MOCK_DIR = Path(__file__).parent / "mock"


def pytest_sessionstart(session):
    """
    Allow coverage to handle multiprocessing.

    References:
        https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html
    """
    from pytest_cov.embed import cleanup_on_sigterm

    cleanup_on_sigterm()


@pytest.fixture(autouse=True)
def mock_okdev(monkeypatch):
    from mio.devices.mocks import okDevMock
    from mio.devices import opalkelly
    from mio import stream_daq

    monkeypatch.setattr(opalkelly, "okDev", okDevMock)
    monkeypatch.setattr(stream_daq, "okDev", okDevMock)


@pytest.fixture(scope="session", autouse=True)
def mock_config_source(monkeypatch_session):
    """
    Add the `tests/data/config` directory to the config sources for the entire testing session
    """
    current_sources = ConfigYAMLMixin.config_sources

    @classmethod
    @property
    def _config_sources(cls: type[ConfigYAMLMixin]) -> list[Path]:
        return [CONFIG_DIR, *current_sources]

    monkeypatch_session.setattr(ConfigYAMLMixin, "config_sources", _config_sources)


@pytest.fixture()
def set_okdev_input(monkeypatch):
    """
    closure fixture to set the environment variable used by StreamDaq to set the
    okDev data source
    """

    def _set_okdev_input(file: Union[str, Path]):
        from mio.devices.mocks import okDevMock

        monkeypatch.setattr(okDevMock, "DATA_FILE", file)
        os.environ["PYTEST_OKDEV_DATA_FILE"] = str(file)

    return _set_okdev_input


@pytest.fixture()
def config_override(tmp_path) -> Callable[[Path, dict], Path]:
    """
    Create a config file with some of its properties overridden
    """

    def _config_override(path: Path, config: dict) -> Path:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        data.update(config)
        out_path = tmp_path / f"config_override_{datetime.now().strftime('%H_%M_%S_%f')}.yml"
        with open(out_path, "w") as f:
            yaml.safe_dump(data, f)
        return out_path

    yield _config_override
