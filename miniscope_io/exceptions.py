
class InvalidSDException(Exception):
    """
    Raised when :class:`.io.SDCard` is used with a drive that doesn't have the appropriate WRITE KEYS in its header
    """