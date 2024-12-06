"""
Command line interface for offline video pre-processing.
"""

import click

from miniscope_io.process.video import VideoProcessor


@click.group()
def process() -> None:
    """
    Command group for video processing.
    """
    pass


@process.command()
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
