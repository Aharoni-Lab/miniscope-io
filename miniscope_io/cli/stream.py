"""
CLI commands for running streamDaq
"""

import os
from pathlib import Path
from typing import Any, Callable, Optional

import click

from miniscope_io.stream_daq import StreamDaq


@click.group()
def stream() -> None:
    """
    Command group for StreamDaq
    """
    pass


def _common_options(fn: Callable) -> Callable:
    fn = click.option(
        "-c",
        "--config",
        required=True,
        help="Path to YAML file to configure the streamDaq (see models.stream.StreamDaqConfig)",
        type=click.Path(exists=True),
    )(fn)
    return fn


def _capture_options(fn: Callable) -> Callable:
    fn = click.option("-o", "--output", help="Video output filename", type=click.Path())(fn)
    fn = click.option(
        "-ok",
        "--output-kwarg",
        "okwarg",
        help="Output kwargs (passed to StreamDaq.init_video). \n"
        "passed as (potentially multiple) calls like\n\n"
        "mio stream capture -ok key1 val1 -ok key2 val2",
        multiple=True,
        type=(str, Any),
    )(fn)
    fn = click.option("-b", "--binary", help="Path (.bin) to save raw binary output to")(fn)
    return fn


@stream.command()
@_common_options
@_capture_options
def capture(
    config: Path,
    output: Optional[Path],
    okwarg: Optional[dict],
    binary: Optional[Path],
    **kwargs: dict,
) -> None:
    """
    Capture video from a StreamDaq device, optionally saving as an encoded video or as raw binary
    """
    daq_inst = StreamDaq(config=config)
    okwargs = dict(okwarg)
    daq_inst.capture(source="fpga", video=output, video_kwargs=okwargs, binary=binary)


@stream.command()
@_common_options
@click.option(
    "-s",
    "--source",
    required=True,
    help="Path to RAW FPGA data to plug into okDevMock",
    type=click.Path(exists=True),
)
@click.option(
    "-p", "--profile", is_flag=True, default=False, help="Run with profiler (not implemented yet)"
)
@_capture_options
@click.pass_context
def test(ctx: click.Context, source: Path, profile: bool, **kwargs: dict) -> None:
    """
    Run StreamDaq in testing mode, using the okDevMock rather than the actual device
    """
    if profile:
        raise NotImplementedError("Profiling mode is not implemented")

    os.environ["STREAMDAQ_MOCKRUN"] = "just_placeholder"
    os.environ["PYTEST_OKDEV_DATA_FILE"] = str(source)

    ctx.forward(capture)
