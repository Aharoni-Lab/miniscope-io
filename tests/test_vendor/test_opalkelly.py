"""
Need input on these tests...
"""
import pytest
import sys

def test_import_ok():
    """
    We should be able to import the opalkelly module -
    that just means that it has all the c extension
    modules it imports.
    """
    if sys.platform.startswith('win'):
        with pytest.raises(NotImplementedError):
            from miniscope_io.vendor import opalkelly as ok
    else:
        from miniscope_io.vendor import opalkelly as ok
