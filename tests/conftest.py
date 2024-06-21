import pytest

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