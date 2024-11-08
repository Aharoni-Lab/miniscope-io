from pathlib import Path

import pytest

from miniscope_io.devices import WireFreeMiniscope
from miniscope_io.formats import WireFreeSDLayout, WireFreeSDLayout_Battery
from miniscope_io.models.data import Frames


@pytest.fixture
def wirefree() -> WireFreeMiniscope:
    """
    WireFreeMiniscope with wirefree layout pointing to the sample data file

    """
    sd_path = Path(__file__).parent.parent / "data" / "wirefree_example.img"
    sdcard = WireFreeMiniscope(drive=sd_path, layout=WireFreeSDLayout)
    return sdcard


@pytest.fixture
def wirefree_battery() -> WireFreeMiniscope:
    sd_path = Path(__file__).parent.parent / "data" / "wirefree_battery_sample.img"
    sdcard = WireFreeMiniscope(drive=sd_path, layout=WireFreeSDLayout_Battery)
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
