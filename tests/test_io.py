import pytest
import csv

from mio.io import BufferedCSVWriter


@pytest.fixture
def tmp_csvfile(tmp_path):
    """
    Creates a temporary file for testing.
    """
    return tmp_path / "test.csv"


def test_csvwriter_initialization(tmp_csvfile):
    """
    Test that the BufferedCSVWriter initializes correctly.
    """
    writer = BufferedCSVWriter(tmp_csvfile, buffer_size=10)
    assert writer.file_path == tmp_csvfile
    assert writer.buffer_size == 10
    assert writer.buffer == []


def test_csvwriter_append_and_flush(tmp_csvfile):
    """
    Test that the BufferedCSVWriter appends to the buffer and flushes it when full.
    """
    writer = BufferedCSVWriter(tmp_csvfile, buffer_size=2)
    writer.append([1, 2, 3])
    assert len(writer.buffer) == 1

    writer.append([4, 5, 6])
    assert len(writer.buffer) == 0
    assert tmp_csvfile.exists()

    with tmp_csvfile.open("r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows == [["1", "2", "3"], ["4", "5", "6"]]


def test_csvwriter_flush_buffer(tmp_csvfile):
    """
    Test that the BufferedCSVWriter flushes the buffer when explicitly told to.
    """
    writer = BufferedCSVWriter(tmp_csvfile, buffer_size=2)
    writer.append([1, 2, 3])
    writer.flush_buffer()

    assert len(writer.buffer) == 0
    assert tmp_csvfile.exists()

    with tmp_csvfile.open("r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows == [["1", "2", "3"]]


def test_csvwriter_close(tmp_csvfile):
    """
    Test that the BufferedCSVWriter flushes the buffer and closes the file when closed.
    """
    writer = BufferedCSVWriter(tmp_csvfile, buffer_size=2)
    writer.append([1, 2, 3])
    writer.close()

    assert len(writer.buffer) == 0
    assert tmp_csvfile.exists()

    with tmp_csvfile.open("r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows == [["1", "2", "3"]]
