"""
CLI entry point
"""

import click

from mio.cli.config import config
from mio.cli.stream import stream
from mio.cli.update import device, update


@click.group()
@click.version_option(package_name="mio")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Miniscope IO CLI Interface
    """
    ctx.ensure_object(dict)


cli.add_command(stream)
cli.add_command(update)
cli.add_command(device)
cli.add_command(config)
