
class InvalidSDException(Exception):
    """
    Raised when :class:`.io.SDCard` is used with a drive that doesn't have the appropriate WRITE KEYS in its header
    """

class EndOfRecordingException(StopIteration):
    """
    Raised when :class:`.io.SDCard` is at the end of the available recording!
    """