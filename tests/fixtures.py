from pathlib import Path
from typing import Callable, Optional

import pytest
import yaml

from miniscope_io.io import SDCard
from miniscope_io.models.data import Frames
from miniscope_io.models.mixins import ConfigYAMLMixin


@pytest.fixture
def wirefree() -> SDCard:
    """
    SDCard with wirefree layout pointing to the sample data file

    """
    sd_path = Path(__file__).parent.parent / "data" / "wirefree_example.img"
    sdcard = SDCard(drive=sd_path, layout="wirefree-sd-layout")
    return sdcard


@pytest.fixture
def wirefree_battery() -> SDCard:
    sd_path = Path(__file__).parent.parent / "data" / "wirefree_battery_sample.img"
    sdcard = SDCard(drive=sd_path, layout="wirefree-sd-layout-battery")
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


@pytest.fixture()
def tmp_config_source(tmp_path, monkeypatch) -> Path:
    """
    Monkeypatch the config sources to include a temporary path
    """

    path = tmp_path / "configs"
    path.mkdir(exist_ok=True)
    current_sources = ConfigYAMLMixin.config_sources

    @classmethod
    @property
    def _config_sources(cls: type[ConfigYAMLMixin]) -> list[Path]:
        return [path, *current_sources]

    monkeypatch.setattr(ConfigYAMLMixin, "config_sources", _config_sources)
    return path


@pytest.fixture()
def yaml_config(
    tmp_config_source, tmp_path, monkeypatch
) -> Callable[[str, dict, Optional[Path]], Path]:
    out_file = tmp_config_source / "test_config.yaml"

    def _yaml_config(id: str, data: dict, path: Optional[Path] = None) -> Path:
        if path is None:
            path = out_file
        else:
            path = Path(path)
            if not path.is_absolute():
                # put under tmp_path (rather than tmp_config_source)
                # in case putting a file outside the config dir is intentional.
                path = tmp_path / path

            if path.is_dir():
                path.mkdir(exist_ok=True, parents=True)
                path = path / "test_config.yaml"
            else:
                path.parent.mkdir(exist_ok=True, parents=True)

        data = {"id": id, **data}
        with open(path, "w") as yfile:
            yaml.dump(data, yfile)
        return path

    return _yaml_config
