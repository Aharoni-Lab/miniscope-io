import pdb

import pytest

from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io.utils import hash_video, hash_file
from .conftest import DATA_DIR, CONFIG_DIR


@pytest.mark.parametrize(
    "config,data,video_hash",
    [
        (
            "stream_daq_test_200px.yml",
            "stream_daq_test_fpga_raw_input_200px.bin",
            "40047689185bdbeb81829aea7c6e3070bcd4673976e5836a138c3e1b54d75099",
        )
    ],
)
def test_video_output(config, data, video_hash, tmp_path, set_okdev_input):
    output_video = tmp_path / "output.avi"

    test_config_path = CONFIG_DIR / config
    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    set_okdev_input(data_file)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)

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
    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    set_okdev_input(data_file)

    output_file = tmp_path / "output.bin"

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", binary=output_file)

    assert output_file.exists()

    assert hash_file(data_file) == hash_file(output_file)
