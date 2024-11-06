"""
CLI for updating device over IR or UART.
"""

import click
import yaml

from miniscope_io.device_update import device_update
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
    "-k",
    "--key",
    required=False,
    type=click.Choice(["LED", "GAIN", "ROI_X", "ROI_Y"]),
    help="key to update. Cannot be used with --restart.",
)
@click.option(
    "-v",
    "--value",
    required=False,
    type=int,
    help="Value to set. Must be used with --key and cannot be used with --restart.",
)
@click.option(
    "-c",
    "--config",
    required=False,
    type=click.Path(exists=True, dir_okay=False),
    help="YAML file with configuration to update. Specify key and value pairs in the file.",
)
def update(port: str, key: str, value: int, device_id: int, config: str) -> None:
    """
    Update device configuration.
    """

    # Check mutual exclusivity
    if (key and not value) or (value and not key):
        raise click.UsageError("Both --key and --value are required if one is specified.")

    if config and (key or value):
        raise click.UsageError(
            "Options --key/--value and --restart" " and --config are mutually exclusive."
        )
    if key and value:
        device_update(port=port, key=key, value=value, device_id=device_id)
    elif config:
        with open(config) as f:
            config_file = yaml.safe_load(f)
        for key, value in config_file:
            device_update(port=port, key=key, value=value, device_id=device_id)
    else:
        raise click.UsageError("Either --key with --value or --restart must be specified.")


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
    "--reboot",
    is_flag=True,
    type=bool,
    help="Restart the device. Cannot be used with --key or --value.",
)
def device(port: str, device_id: int, reboot: bool) -> None:
    """
    Send device commands (e.g., reboot)
    """

    # Check mutual exclusivity
    if reboot:
        device_update(
            port=port, key="DEVICE", value=DeviceCommand.REBOOT.value, device_id=device_id
        )
    else:
        raise click.UsageError("Only --reboot is currently implemented.")
