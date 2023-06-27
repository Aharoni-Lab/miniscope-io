import pytest
import json
import importlib

from miniscope_io.formats import WireFreeSDLayout


# More formats can be added here as needed.
@pytest.mark.parametrize('format', [WireFreeSDLayout])
def test_to_from_json(format):
    """
    A format can be exported and re-imported from JSON and remain equivalent
    """
    fmt_json = format.json()

    # convert the json to a dict
    fmt_dict = json.loads(fmt_json)

    # Get the parent class
    parent_class = type(format)
    #parent_class_name = parent_module_str.split('.')[-1]
    #parent_class = getattr(importlib.import_module(parent_module_str), parent_class_name)

    new_format = parent_class(**fmt_dict)

    assert format == new_format


@pytest.mark.parametrize(
    ['format', 'format_json'],
    [
        (WireFreeSDLayout, '{"sectors": {"header": 1023, "config": 1024, "data": 1025, "size": 512}, "write_key0": 226277911, "write_key1": 226277911, "write_key2": 226277911, "write_key3": 226277911, "header": {"gain": 4, "led": 5, "ewl": 6, "record_length": 7, "fs": 8}, "config": {"width": 0, "height": 1, "fs": 2, "buffer_size": 3, "n_buffers_recorded": 4, "n_buffers_dropped": 5}, "buffer": {"length": 0, "linked_list": 1, "frame_num": 2, "buffer_count": 3, "frame_buffer_count": 4, "write_buffer_count": 5, "dropped_buffer_count": 6, "timestamp": 7, "data_length": 8}}')
    ]
)
def test_format_unchanged(format, format_json):
    """
    A format is a constant and shouldn't change!

    This protects against changes in the parent classes breaking the formats,
    and also breaking the formats themselves
    """
    parent_class = type(format)

    format_dict = json.loads(format_json)
    new_format = parent_class(**format_dict)

    assert new_format == format
