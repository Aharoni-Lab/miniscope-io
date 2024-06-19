import pytest

from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io.utils import hash_file
from .conftest import DATA_DIR, CONFIG_DIR

from .mock.opalkelly import okDevMock

@pytest.mark.parametrize(
    'config,data,hash',
    [
        (
            'stream_daq_test_200px.yml',
            'stream_daq_test_fpga_raw_input_200px.bin',
            ('3c0b7caedc5f6506fdfdc4f1277ba76a3a911dd79e5240801455a74292f793f5',
             'e55462cc06cf6082952b2ce0fdd956cf1408fb492cddb6fb797119235b559a93',
             '290fd85bb3d00f896e695564eedc072e5e1f2837c4a0f19282e80624bae56401')
        )
    ]
)
@pytest.mark.timeout(10)
def test_video_output(config, data, hash, tmpdir, monkeypatch):
    output_video = tmpdir / 'output.avi'

    test_config_path = CONFIG_DIR / config
    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    data_file = DATA_DIR / data
    monkeypatch.setattr(okDevMock, 'DATA_FILE', data_file)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)

    assert output_video.exists()

    video_hash = hash_file(output_video)
    assert video_hash in hash