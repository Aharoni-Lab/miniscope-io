"""
CLI for updating device over IR or UART.
"""

import click

from miniscope_io.device_update import DevUpdate


@click.command()
@click.option(
    "-p",
    "--port",
    required=False,
    help="Serial port to connect to. Needed if multiple FTDI devices are connected.",
)
@click.option(
    "-t", "--target", required=True, type=click.Choice(["LED", "GAIN"]), help="Target to update"
)
@click.option("-v", "--value", required=True, type=int, help="Value to set")
def update(port: str, target: str, value: int) -> None:
    """
    Update device configuration.
    """
    DevUpdate(port=port, target=target, value=value)
