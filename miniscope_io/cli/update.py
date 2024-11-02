"""
CLI for updating device over IR or UART.
"""

import click
import yaml

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
    "-c",
    "--config",
    required=False,
    type=click.Path(exists=True, dir_okay=False),
    help="YAML file with configuration to update. Specify target and value pairs in the file.",
)
@click.option(
    "--reboot",
    is_flag=True,
    type=bool,
    help="Restart the device. Cannot be used with --target or --value.",
)
def update(port: str, target: str, value: int, device_id: int, reboot: bool, config: str) -> None:
    """
    Update device configuration or restart it.
    """

    # Check mutual exclusivity
    if (target and not value) or (value and not target):
        raise click.UsageError("Both --target and --value are required if one is specified.")

    if ((target or value) and reboot) or (config and reboot) or (config and (target or value)):
        raise click.UsageError(
            "Options --target/--value and --restart" " and --config are mutually exclusive."
        )
    if target and value:
        DevUpdate(port=port, target=target, value=value, device_id=device_id)
    elif config:
        with open(config) as f:
            config_file = yaml.safe_load(f)
        for key, value in config_file:
            DevUpdate(port=port, target=key, value=value, device_id=device_id)
    elif reboot:
        DevUpdate(port=port, target="DEVICE", value=DeviceCommand.REBOOT.value, device_id=device_id)
    else:
        raise click.UsageError("Either --target with --value or --restart must be specified.")
