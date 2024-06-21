import pytest

from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io.utils import hash_video
from .conftest import DATA_DIR, CONFIG_DIR

from .mock.opalkelly import okDevMock

@pytest.mark.parametrize(
    'config,data,video_hash',
    [
        (
            'stream_daq_test_200px.yml',
            'stream_daq_test_fpga_raw_input_200px.bin',
            '82d623032a31cf805f4971a5715ed4cb938c08c5d6a97ebbdecd8e25dae7803e'
        )
    ]
)
@pytest.mark.timeout(30)
def test_video_output(config, data, video_hash, tmpdir, monkeypatch):
    output_video = tmpdir / 'output.avi'

    test_config_path = CONFIG_DIR / config
    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    monkeypatch.setattr(okDevMock, 'DATA_FILE', data_file)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)

    assert output_video.exists()

    video_hash = hash_video(output_video)

    assert video_hash == video_hash