import pytest
import json

from miniscope_io.models.sdcard import SDLayout


# More formats can be added here as needed.
@pytest.mark.parametrize("format", [SDLayout.from_id("wirefree-sd-layout")])
def test_to_from_json(format):
    """
    A format can be exported and re-imported from JSON and remain equivalent
    """
    fmt_json = format.model_dump_json()

    # convert the json to a dict
    fmt_dict = json.loads(fmt_json)

    # Get the parent class
    parent_class = type(format)
    # parent_class_name = parent_module_str.split('.')[-1]
    # parent_class = getattr(importlib.import_module(parent_module_str), parent_class_name)

    new_format = parent_class(**fmt_dict)

    assert format == new_format
