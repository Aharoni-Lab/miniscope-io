"""
CLI for updating device over IR or UART.
"""

import click

from miniscope_io.device_update import DevUpdate
from miniscope_io.models.devupdate import DeviceCommand


@click.command()
@click.option(
    "-p",
    "--port",
    required=False,
    help="Serial port to connect to. Needed if multiple FTDI devices are connected.",
)
@click.option(
    "-i",
    "--device_id",
    required=False,
    default=0,
    type=int,
    help="ID of the device to update. 0 will update all devices.",
)
@click.option(
    "-t",
    "--target",
    required=False,
    type=click.Choice(["LED", "GAIN", "ROI_X", "ROI_Y"]),
    help="Target to update. Cannot be used with --restart.",
)
@click.option(
    "-v",
    "--value",
    required=False,
    type=int,
    help="Value to set. Must be used with --target and cannot be used with --restart.",
)
@click.option(
    "--restart",
    is_flag=True,
    type=bool,
    help="Restart the device. Cannot be used with --target or --value.",
)
def update(port: str, target: str, value: int, device_id: int, restart: bool) -> None:
    """
    Update device configuration or restart it.
    """

    # Check mutual exclusivity
    if (target and not value) or (value and not target):
        raise click.UsageError("Both --target and --value are required if one is specified.")

    if (target or value) and restart:
        raise click.UsageError("Options --target/--value and --restart cannot be used together.")

    if target and value:
        DevUpdate(port=port, target=target, value=value, device_id=device_id)
    elif restart:
        DevUpdate(
            port=port, target="DEVICE", value=DeviceCommand.RESTART.value, device_id=device_id
        )
    else:
        raise click.UsageError("Either --target with --value or --restart must be specified.")
