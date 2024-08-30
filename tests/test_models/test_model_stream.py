import pytest

from miniscope_io import DEVICE_DIR
from miniscope_io.models.stream import StreamDevConfig, StreamBufferHeader

from ..conftest import CONFIG_DIR

@pytest.mark.parametrize(
    'config',
    [
        'preamble_hex.yml',
    ]
)
def test_preamble_hex_parsing(config):
    """
    Test that a hexadecimal string is correctly parsed to a byte string
    from a string or a hex integer
    """
    config_file = CONFIG_DIR / config

    instance = StreamDevConfig.from_yaml(config_file)
    assert instance.preamble == b'\x124Vx'

def test_absolute_bitstream():
    """
    Relative paths should be resolved relative to the devices dir
    """
    example = CONFIG_DIR / 'wireless_example.yml'

    instance = StreamDevConfig.from_yaml(example)
    assert instance.bitstream.is_absolute()
    assert str(instance.bitstream).startswith(str(DEVICE_DIR))

def test_adc_scaling():
    """
    Test that the ADC scaling factors are correctly parsed
    """
    example = CONFIG_DIR / 'stream_daq_test_200px.yml'
    instance_config = StreamDevConfig.from_yaml(example)

    battery_voltage_adc = 200
    input_voltage_adc = 250

    instance_header = StreamBufferHeader(
        linked_list=0,
        frame_num=0,
        buffer_count=0,
        frame_buffer_count=0,
        write_buffer_count=0,
        dropped_buffer_count=0,
        timestamp=0,
        pixel_count=0,
        write_timestamp=0,
        battery_voltage_adc=battery_voltage_adc,
        input_voltage_adc=input_voltage_adc,
    )
    instance_header.set_adc_scaling(instance_config.adc_scale)

    battery_voltage = battery_voltage_adc / 2 ** instance_config.adc_scale.bitdepth * instance_config.adc_scale.ref_voltage * instance_config.adc_scale.battery_div_factor

    input_voltage = input_voltage_adc / 2 ** instance_config.adc_scale.bitdepth * instance_config.adc_scale.ref_voltage * instance_config.adc_scale.vin_div_factor

    assert instance_header.battery_voltage == battery_voltage
    assert instance_header.input_voltage == input_voltage