from pathlib import Path

import pytest

from miniscope_io import SDCard
from miniscope_io.formats import WireFreeSDLayout, WireFreeSDLayout_Battery
from miniscope_io.models.data import Frames


@pytest.fixture
def wirefree() -> SDCard:
    """
    SDCard with wirefree layout pointing to the sample data file

    """
    sd_path = Path(__file__).parent.parent / "data" / "wirefree_example.img"
    sdcard = SDCard(drive=sd_path, layout=WireFreeSDLayout)
    return sdcard


@pytest.fixture
def wirefree_battery() -> SDCard:
    sd_path = Path(__file__).parent.parent / "data" / "wirefree_battery_sample.img"
    sdcard = SDCard(drive=sd_path, layout=WireFreeSDLayout_Battery)
    return sdcard


@pytest.fixture()
def wirefree_frames(wirefree) -> Frames:
    frames = []
    with wirefree:
        while True:
            try:
                frame_object = wirefree.read(return_header=True)
                frames.append(frame_object)
            except StopIteration:
                break
    return Frames(frames=frames)
