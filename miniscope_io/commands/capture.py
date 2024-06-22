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

    output_video = Path("output") / (output + ".avi")

    if source:
        # environment variable to allow import okDevMock
        os.environ['STREAMDAQ_PROFILERUN'] = 'just_placeholder'
        os.environ['PYTEST_OKDEV_DATA_FILE'] = source

    daqConfig = StreamDaqConfig.from_yaml(config)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)