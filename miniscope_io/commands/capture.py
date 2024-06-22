"""
CLI commands for running streamDaq
"""

import os
from pathlib import Path

import click

from miniscope_io.stream_daq import StreamDaq, StreamDaqConfig


@click.command()
@click.option("-c", "--config", required=True, help="YAML file to configure the streamDaq (str)")
@click.option("-s", "--source", required=False, help="RAW FPGA data to plug into okDevMock (str)")
@click.option("-o", "--output", default="output", help="Video output filename (str)")
def sdaqprof(config: str, source: str, output: str) -> None:
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

    output_video = Path(output + ".avi")

    if source:
        # environment variable to allow import okDevMock
        os.environ["STREAMDAQ_PROFILERUN"] = "just_placeholder"
        os.environ["PYTEST_OKDEV_DATA_FILE"] = source

    daqConfig = StreamDaqConfig.from_yaml(config)

    daq_inst = StreamDaq(config=daqConfig)
    daq_inst.capture(source="fpga", video=output_video)
