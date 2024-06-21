import pytest
import os

from pathlib import Path


DATA_DIR = Path(__file__).parent / 'data'
CONFIG_DIR = DATA_DIR / 'config'
MOCK_DIR = Path(__file__).parent / 'mock'


@pytest.fixture(autouse=True)
def mock_okdev(monkeypatch):
    from .mock.opalkelly import okDevMock
    from miniscope_io.devices import opalkelly
    from miniscope_io import stream_daq

    monkeypatch.setattr(opalkelly, 'okDev', okDevMock)
    monkeypatch.setattr(stream_daq, 'okDev', okDevMock)

@pytest.fixture(autouse=True)
def opencv_ffmpeg():
    """
    Set opencv to use ffmpeg if available for more reproducible crossplatform video
    encoding
    """
    import cv2
    os.environ['OPENCV_VIDEOIO_PRIORITY_LIST'] = f'{cv2.CAP_FFMPEG}'