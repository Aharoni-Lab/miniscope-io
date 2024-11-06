"""
CLI entry point
"""

import click

from miniscope_io.cli.stream import stream
from miniscope_io.cli.update import device, update


@click.group()
@click.version_option(package_name="miniscope_io")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Miniscope IO CLI Interface
    """
    ctx.ensure_object(dict)


cli.add_command(stream)
cli.add_command(update)
cli.add_command(device)
