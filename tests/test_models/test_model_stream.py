import pytest

from miniscope_io import DEVICE_DIR
from miniscope_io.models.stream import StreamDaqConfig

@pytest.mark.parametrize(
    'config',
    [
        'preamble_hex.yml',
        'preamble_string.yml'
    ]
)
def test_preamble_hex_parsing(config, config_dir):
    """
    Test that a hexadecimal string is correctly parsed to a byte string
    from a string or a hex integer
    """
    config_file = config_dir / config

    instance = StreamDaqConfig.from_yaml(config_file)
    assert instance.preamble == b'\x124Vx'

def test_absolute_bitstream(config_dir):
    """
    Relative paths should be resolved relative to the devices dir
    """
    example = config_dir / 'wireless_example.yml'

    instance = StreamDaqConfig.from_yaml(example)
    assert instance.bitstream.is_absolute()
    assert str(instance.bitstream).startswith(str(DEVICE_DIR))





