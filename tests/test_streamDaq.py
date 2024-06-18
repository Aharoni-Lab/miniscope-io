import os
import filecmp
from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io import TESTDATA_DIR

def test_video_output():
    reference_video_path = TESTDATA_DIR / 'stream_daq_test_output_200px.avi'
    output_video_path = 'output.avi'

    test_config_path = TESTDATA_DIR / 'config' / 'stream_daq_test_200px.yml'
    daqConfig = StreamDaqConfig.from_yaml(test_config_path)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", config = daqConfig)

    assert os.path.exists(reference_video_path)
    assert os.path.exists(output_video_path)

    assert filecmp.cmp(reference_video_path, output_video_path, shallow=False)
    os.remove(output_video_path)

test_video_output()