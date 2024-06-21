import os

import pytest
from typing import Union

from pathlib import Path


DATA_DIR = Path(__file__).parent / 'data'
CONFIG_DIR = DATA_DIR / 'config'
MOCK_DIR = Path(__file__).parent / 'mock'


@pytest.fixture(autouse=True)
def mock_okdev(monkeypatch):
    from miniscope_io.devices.mocks import okDevMock
    from miniscope_io.devices import opalkelly
    from miniscope_io import stream_daq

    monkeypatch.setattr(opalkelly, 'okDev', okDevMock)
    monkeypatch.setattr(stream_daq, 'okDev', okDevMock)

@pytest.fixture()
def set_okdev_input(monkeypatch):
    """
    closure fixture to set the environment variable used by StreamDaq to set the
    okDev data source
    """
    def _set_okdev_input(file:Union[str, Path]):
        from miniscope_io.devices.mocks import okDevMock
        monkeypatch.setattr(okDevMock, 'DATA_FILE', file)
        os.environ['PYTEST_OKDEV_DATA_FILE'] = str(file)

    return _set_okdev_input