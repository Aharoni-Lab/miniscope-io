import pytest
import serial
from pydantic import ValidationError
from unittest.mock import MagicMock, patch, call
from miniscope_io.models.devupdate import UpdateCommandDefinitions, UpdateTarget
from miniscope_io.device_update import DevUpdate, find_ftdi_device


@patch("miniscope_io.device_update.serial.tools.list_ports.comports")
@patch("miniscope_io.device_update.serial.Serial")
def test_devupdate_with_device_connected(mock_serial, mock_comports):
    """
    Test DevUpdate function with a device connected.
    """
    mock_serial_instance = mock_serial.return_value
    mock_comports.return_value = [
        MagicMock(vid=0x0403, pid=0x6001, device="COM3"),
        MagicMock(vid=0x1234, pid=0x5678, device="COM4"),
    ]
    target = "LED"
    value = 2
    device_id = 1
    port = "COM3"

    DevUpdate(target, value, device_id, port)

    mock_serial.assert_called_once_with(port=port, baudrate=2400, timeout=5, stopbits=2)

    id_command = (device_id + UpdateCommandDefinitions.id_header) & 0xFF
    target_command = (UpdateTarget.LED.value + UpdateCommandDefinitions.target_header) & 0xFF
    value_LSB_command = (
        (value & UpdateCommandDefinitions.LSB_value_mask) + UpdateCommandDefinitions.LSB_header
    ) & 0xFF
    value_MSB_command = (
        ((value & UpdateCommandDefinitions.MSB_value_mask) >> 6) + UpdateCommandDefinitions.MSB_header
    ) & 0xFF
    reset_command = UpdateCommandDefinitions.reset_byte

    expected_calls = [
        call(id_command.to_bytes(1, 'big')),
        call(target_command.to_bytes(1, 'big')),
        call(value_LSB_command.to_bytes(1, 'big')),
        call(value_MSB_command.to_bytes(1, 'big')),
        call(reset_command.to_bytes(1, 'big')),
    ]

    assert mock_serial_instance.write.call_count == len(expected_calls)
    mock_serial_instance.write.assert_has_calls(expected_calls, any_order=False)

@patch("miniscope_io.device_update.serial.tools.list_ports.comports")
def test_devupdate_without_device_connected(mock_comports):
    """
    Test DevUpdate function without a device connected.
    """
    mock_comports.return_value = [
    ]
    target = "GAIN"
    value = 2
    device_id = 0

    with pytest.raises(ValueError, match="No FTDI devices found."):
        DevUpdate(target, value, device_id)

@patch("miniscope_io.device_update.serial.tools.list_ports.comports")
def test_find_ftdi_device(mock_comports):
    """
    Test find_ftdi_device function.
    """
    mock_comports.return_value = [
        MagicMock(vid=0x0403, pid=0x6001, device="COM3"),
        MagicMock(vid=0x1234, pid=0x5678, device="COM4"),
    ]

    result = find_ftdi_device()

    assert result == ["COM3"]

@patch("miniscope_io.models.devupdate.serial.tools.list_ports.comports")
def test_invalid_target_raises_error(mock_comports):
    """
    Test that an invalid target raises an error.
    """
    mock_comports.return_value = [
        MagicMock(vid=0x0403, pid=0x6001, device="COM3"),
        MagicMock(vid=0x1234, pid=0x5678, device="COM4"),
    ]

    target = "RANDOM_STRING"
    value = 50
    device_id = 1
    port = "COM3"

    with pytest.raises(ValidationError, match="Target RANDOM_STRING not found"):
        DevUpdate(target, value, device_id, port)

@patch("miniscope_io.models.devupdate.serial.tools.list_ports.comports")
def test_invalid_led_value_raises_error(mock_comports):
    """
    Test that an invalid LED value raises an error.
    """
    mock_comports.return_value = [
        MagicMock(vid=0x0403, pid=0x6001, device="COM3"),
        MagicMock(vid=0x1234, pid=0x5678, device="COM4"),
    ]
    target = "LED"
    value = 150  # LED value should be between 0 and 100
    device_id = 1
    port = "COM3"

    with pytest.raises(ValidationError, match="For LED, value must be between 0 and 100"):
        DevUpdate(target, value, device_id, port)


@patch("miniscope_io.device_update.serial.tools.list_ports.comports")
def test_devupdate_with_multiple_ftdi_devices(mock_comports):
    """
    Test that multiple FTDI devices raise an error.
    """
    mock_comports.return_value = [
        MagicMock(vid=0x0403, pid=0x6001, device="COM1"),
        MagicMock(vid=0x0403, pid=0x6001, device="COM2"),
    ]

    target = "GAIN"
    value = 5
    device_id = 1

    with pytest.raises(ValueError, match="Multiple FTDI devices found. Please specify the port."):
        DevUpdate(target, value, device_id)

@patch("miniscope_io.device_update.serial.Serial")
def test_devupdate_serial_exception_handling(mock_serial):
    """
    Test exception handling when serial port cannot be opened.
    """
    mock_serial.side_effect = serial.SerialException("Serial port error")

    target = "LED"
    value = 50
    device_id = 1
    port = "COM3"

    with pytest.raises(ValidationError):
        DevUpdate(target, value, device_id, port)

@patch("miniscope_io.device_update.serial.tools.list_ports.comports")
def test_specified_port_not_ftdi_device(mock_comports):
    """
    Test with a specified port not corresponding to an FTDI device.
    """
    mock_comports.return_value = [
        MagicMock(vid=None, pid=None, device="COM3")
    ]

    target = "GAIN"
    value = 10
    device_id = 1

    with pytest.raises(ValueError, match="No FTDI devices found."):
        DevUpdate(target, value, device_id)
