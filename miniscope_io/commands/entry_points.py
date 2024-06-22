"""
Entry points for scripts
"""

import click

from miniscope_io.commands.capture import main_sdaq, sdaq


@click.group()
def cli() -> None:
    """
    CLI entry point
    """
    pass


# Register commands
cli.add_command(sdaq)

# Map main functions for CLI commands to ensure they work with the multiprocessing guard
main_functions = {
    "sdaqprof": main_sdaq,
}


def main() -> None:
    """
    Just an entry point. Nested for multiprocessing guard which is probably not necessary now.
    """
    cli()
