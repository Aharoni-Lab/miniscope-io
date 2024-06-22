import click
import os

from pathlib import Path


from miniscope_io.stream_daq import StreamDaqConfig, StreamDaq
from miniscope_io.utils import hash_video, hash_file

@click.command()
@click.option('-c', '--config', required=True, help='YAML file to configure the streamDaq')
@click.option('-s', '--source', required=False, help='RAW FPGA data to plug into okDevMock')
@click.option('-o', '--output', default='output', help='Video output filename')
def sdaqprof(config, source, output):
    """
    Command to profile stream data acquisition.

    This command profiles stream data acquisition based on the provided configuration and
    optional source file.

    Usage: 
        mio sdaqprof -c path/to/config.yml -s path/to/rawdata.bin -o output_filename

    Parameters:
    -c, --config (str): Path to the main YAML configuration file.
    -s, --source (str or None): Optional path to a source configuration file for stream data mock.
    -o, --output (str): Name of the output video file (without extension).

    Returns:
    None
    """
 
    output_video = Path("output") / (output + ".avi")

    if source:
        # environment variable to allow import okDevMock
        os.environ['STREAMDAQ_PROFILERUN'] = 'just_placeholder'
        os.environ['PYTEST_OKDEV_DATA_FILE'] = source

    daqConfig = StreamDaqConfig.from_yaml(config)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)