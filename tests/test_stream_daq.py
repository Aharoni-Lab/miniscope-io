import pytest

from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io.utils import hash_video
from .conftest import DATA_DIR, CONFIG_DIR

from miniscope_io.devices.mocks import okDevMock

@pytest.mark.parametrize(
    'config,data,video_hash',
    [
        (
            'stream_daq_test_200px.yml',
            'stream_daq_test_fpga_raw_input_200px.bin',
            '40047689185bdbeb81829aea7c6e3070bcd4673976e5836a138c3e1b54d75099'
        )
    ]
)
@pytest.mark.timeout(30)
def test_video_output(config, data, video_hash, tmp_path, monkeypatch):
    output_video = tmp_path / 'output.avi'

    test_config_path = CONFIG_DIR / config
    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    monkeypatch.setattr(okDevMock, 'DATA_FILE', data_file)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)

    assert output_video.exists()

    video_hash = hash_video(output_video)

    assert video_hash == video_hash