import pdb

import pytest

from miniscope_io.stream_daq import StreamDevConfig, StreamDaq
from miniscope_io.utils import hash_video, hash_file
from .conftest import DATA_DIR, CONFIG_DIR


@pytest.mark.parametrize(
    "config,data,video_hash,show_video",
    [
        (
            "stream_daq_test_200px.yml",
            "stream_daq_test_fpga_raw_input_200px.bin",
            "f878f9c55de28a9ae6128631c09953214044f5b86504d6e5b0906084c64c644c",
            False,
        )
    ],
)
def test_video_output(config, data, video_hash, tmp_path, show_video, set_okdev_input):
    output_video = tmp_path / "output.avi"

    test_config_path = CONFIG_DIR / config
    daqConfig = StreamDevConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    set_okdev_input(data_file)

    daq_inst = StreamDaq(device_config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video, show_video=show_video)

    assert output_video.exists()

    video_hash = hash_video(output_video)

    assert video_hash == video_hash


@pytest.mark.parametrize(
    "config,data",
    [
        (
            "stream_daq_test_200px.yml",
            "stream_daq_test_fpga_raw_input_200px.bin",
        )
    ],
)
def test_binary_output(config, data, set_okdev_input, tmp_path):
    test_config_path = CONFIG_DIR / config
    daqConfig = StreamDevConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    set_okdev_input(data_file)

    output_file = tmp_path / "output.bin"

    daq_inst = StreamDaq(device_config=daqConfig)
    daq_inst.capture(source="fpga", binary=output_file, show_video=False)

    assert output_file.exists()

    assert hash_file(data_file) == hash_file(output_file)
