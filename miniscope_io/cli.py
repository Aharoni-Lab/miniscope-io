"""
CLI entry points
"""
import click

from miniscope_io.commands.capture import sdaqprof


@click.group()
def cli()->None:
    """
    CLI entry point
    """
    pass

cli.add_command(sdaqprof)

if __name__ == '__main__':
    cli()