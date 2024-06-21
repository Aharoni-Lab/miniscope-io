import pytest

from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io.utils import hash_file
from .conftest import DATA_DIR, CONFIG_DIR

from .mock.opalkelly import okDevMock

@pytest.mark.parametrize(
    'config,data,test_video',
    [
        (
            'stream_daq_test_200px.yml',
            'stream_daq_test_fpga_raw_input_200px.bin',
            'stream_daq_test_output_200px.avi'
        )
    ]
)
@pytest.mark.timeout(30)
def test_video_output(config, data, test_video, tmpdir, monkeypatch):
    output_video = tmpdir / 'output.avi'

    test_config_path = CONFIG_DIR / config
    test_video_path = DATA_DIR / test_video

    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    monkeypatch.setattr(okDevMock, 'DATA_FILE', data_file)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)

    assert output_video.exists()


    video_hash = hash_file(output_video)
    test_video_hash = hash_file(test_video_path)

    assert video_hash == test_video_hash
    #assert video_hash in hash