"""
CLI commands for running streamDaq
"""

import os
from pathlib import Path
from typing import Any, Callable, Optional

import click

from mio.cli.common import ConfigIDOrPath
from mio.stream_daq import StreamDaq


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
        help=(
            "Either a config `id` or a path to device config YAML file for streamDaq "
            "(see models.stream.StreamDevConfig). If path is relative, treated as "
            "relative to the current directory, and then if no matching file is found, "
            "relative to the user `config_dir` (see `mio config --help`)."
        ),
        type=ConfigIDOrPath(),
    )(fn)
    return fn


def _capture_options(fn: Callable) -> Callable:
    fn = click.option(
        "-o",
        "--output",
        help="Output file basename for video, metadata, and binary exports",
        type=click.Path(),
    )(fn)
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
    fn = click.option("-b", "--binary_export", is_flag=True, help="Save binary to a .bin file")(fn)
    fn = click.option(
        "-m",
        "--metadata_display",
        is_flag=True,
        help="Display metadata in real time. \n"
        "**WARNING:** This is still an **EXPERIMENTAL** feature and is **UNSTABLE**.",
    )(fn)

    return fn


@stream.command()
@_common_options
@_capture_options
def capture(
    device_config: Path,
    output: Optional[Path],
    okwarg: Optional[dict],
    no_display: Optional[bool],
    binary_export: Optional[bool],
    metadata_display: Optional[bool],
    **kwargs: dict,
) -> None:
    """
    Capture video from a StreamDaq device, optionally saving as an encoded video or as raw binary
    """
    daq_inst = StreamDaq(device_config=device_config)
    okwargs = dict(okwarg)

    if output:
        unique_stem_path = get_unique_stempath(Path(output))
        video_output = unique_stem_path.with_suffix(".avi")
        metadata_output = unique_stem_path.with_suffix(".csv")

        binary_output = unique_stem_path.with_suffix(".bin") if binary_export else None
    else:
        video_output = None
        metadata_output = None
        binary_output = None

    daq_inst.capture(
        source="fpga",
        video=video_output,
        video_kwargs=okwargs,
        metadata=metadata_output,
        binary=binary_output,
        show_video=not no_display,
        show_metadata=metadata_display,
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


def get_unique_stempath(base_output: Path) -> Path:
    """
    Check the target directory if there are any files with the same basename (ignoring extensions)
    If so, append a number to the basename to make it unique.
    """
    directory = base_output.parent
    stem = base_output.stem

    # Ensure the directory exists
    directory.mkdir(parents=True, exist_ok=True)

    index = 1
    candidate_stem = stem

    def _any_stem_exists(candidate_stem_str: str) -> bool:
        # List all files and check if any have the same stem as the candidate
        return any(candidate_stem_str == p.stem for p in directory.iterdir() if p.is_file())

    # Iterate to find a unique stem
    while _any_stem_exists(candidate_stem):
        candidate_stem = f"{stem}-{index}"
        index += 1

    return directory / candidate_stem
