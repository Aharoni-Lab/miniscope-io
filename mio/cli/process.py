"""
Command line interface for 
"""

import click

from miniscope_io.processing.video import VideoProcessor


@click.command()
@click.option(
    "-i",
    "--input",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the video file to process.",
)
def denoise(
    input: str,
) -> None:
    """
    Denoise a video file.
    """
    VideoProcessor.denoise(input)
