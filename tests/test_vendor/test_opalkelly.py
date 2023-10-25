"""
Need input on these tests...
"""

def test_import_ok():
    """
    We should be able to import the opalkelly module -
    that just means that it has all the c extension
    modules it imports.
    """
    from miniscope_io.vendor.opalkelly.lib import ok
