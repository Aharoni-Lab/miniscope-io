import click

from miniscope_io.commands.capture import main_sdaqprof, sdaqprof


@click.group()
def cli() -> None:
    """
    CLI entry point
    """
    pass

# Register commands
cli.add_command(sdaqprof)

# Map main functions for CLI commands to ensure they work with the multiprocessing guard
main_functions = {
    "sdaqprof": main_sdaqprof,
}

def main():
    cli()