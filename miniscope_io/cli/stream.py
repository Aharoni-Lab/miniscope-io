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
        "--device_config",
        required=True,
        help="Path to device config YAML file for streamDaq (see models.stream.StreamDevConfig)",
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
    fn = click.option("--no-display", is_flag=True, help="Don't show video in real time")(fn)
    fn = click.option("--no-metadata", is_flag=True, help="Don't save metadata to a csv file")(fn)
    fn = click.option("-b", "--binary", help="Path (.bin) to save raw binary output to")(fn)
    return fn


@stream.command()
@_common_options
@_capture_options
def capture(
    device_config: Path,
    output: Optional[Path],
    okwarg: Optional[dict],
    binary: Optional[Path],
    no_display: Optional[bool],
    no_metadata: Optional[bool],
    **kwargs: dict,
) -> None:
    """
    Capture video from a StreamDaq device, optionally saving as an encoded video or as raw binary
    """
    daq_inst = StreamDaq(device_config=device_config)
    okwargs = dict(okwarg)

    output = get_unique_filepath(Path(output)) if output else None
    binary = get_unique_filepath(Path(binary)) if binary else None

    daq_inst.capture(
        source="fpga",
        video=output,
        video_kwargs=okwargs,
        binary=binary,
        show_video=not no_display,
        save_metadata=not no_metadata,
    )


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

def get_unique_filepath(output: Path) -> Path:
    """
    Check if the path already exists, and if so, append a number to the path.
    """
    base_output = output
    index = 1

    while output.exists():
        output = base_output.with_stem(f"{base_output.stem}-{index}") if base_output.suffix else output
        index += 1

    return output