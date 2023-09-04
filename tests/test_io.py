import pytest
import tempfile
from pathlib import Path

from miniscope_io.sdcard import DataHeader
from miniscope_io.exceptions import EndOfRecordingException
from miniscope_io.data import Frame
from miniscope_io.utils import hash_file

from .fixtures import wirefree


def test_read(wirefree):
    """
    Test that we can read a frame!

    For now since we're just using the example, don't try and validate the output,
    we'll do that later.
    """
    n_frames = 20

    # before we enter the context manager, we shouldn't be able to read
    with pytest.raises(RuntimeError):
        frame = wirefree.read()

    # failing to read should not increment the frame and it should still be None
    assert wirefree.frame is None

    with wirefree:
        for i in range(n_frames):
            # Frame indicates what frame we are just about to read
            assert wirefree.frame == i

            frame = wirefree.read()

            # the frame is the right shape
            assert len(frame.shape) == 2
            assert frame.shape[0] == wirefree.config.height
            assert frame.shape[1] == wirefree.config.width

            # assert they're not all zeros - ie. we read some data
            assert frame.any()

            # we should have stashed frame start positions
            # if we just read the 0th frame, we should have 2 positions
            # for the 0th and 1st frame
            assert len(wirefree.positions) == i + 2

    # after we exit the context manager, we should lose our current frame
    assert wirefree.frame is None
    # we should also not be able to read anymore
    with pytest.raises(RuntimeError):
        frame = wirefree.read()
    # and the file descriptor should also be gone
    assert wirefree._f is None
    # but we should keep our positions
    assert len(wirefree.positions) == n_frames + 1

def test_return_headers(wirefree):
    """
    We can return the headers for the individual buffers in a frame
    """
    with wirefree:
        frame_object = wirefree.read(return_header=True)
        assert isinstance(frame_object, Frame)

        assert len(frame_object.headers) == 5
        assert all([isinstance(b, DataHeader) for b in frame_object.headers])

def test_frame_count(wirefree):
    """
    We can infer the total number of frames in a recording from the data header
    """
    # known max frames given the data header in the example data
    assert wirefree.frame_count == 388

    # if we try and read past the end, we get an exception
    with wirefree:
        wirefree.frame = 389
        with pytest.raises(EndOfRecordingException):
            frame = wirefree.read()


@pytest.mark.parametrize(
    ['file', 'fourcc', 'hash'],
    [
        ('video.avi', 'GREY', '70b6898113a6d9f05c02bd52131ee56dc68b1c65fed518ea2265440fab801cc6'),
        ('video.mp4', 'X264', 'aecbe09ebabce67acd509b4819da76ea4ddee945c2cf078fbe4ae7b157965637')
    ]
)
def test_write_video(wirefree, file, fourcc, hash):
    """
    Test that we can write videos from an SD card!!
    """
    with tempfile.TemporaryDirectory() as tempdir:
        path = Path(tempdir) / file
        wirefree.to_video(path, fourcc=fourcc, progress=False)
        file_hash = hash_file(path)
        assert file_hash == hash




#
# @pytest.mark.parametrize(
#     ['data', 'header', 'sector', 'word'],
#     list(itertools.product(
#         (63964, 49844),
#         (9, 10),
#         (512,),
#         (4,)
#     ))
# )
# def test_n_blocks(data, header, sector, word):
#     """
#     Original:
#
#     numBlocks = int((dataHeader[BUFFER_HEADER_DATA_LENGTH_POS] + \
#       (dataHeader[BUFFER_HEADER_HEADER_LENGTH_POS] * 4) + (512 - 1)) / 512)
#     data = np.fromstring(
#       f.read(
#         numBlocks*512 - dataHeader[BUFFER_HEADER_HEADER_LENGTH_POS] * 4
#       ),
#       dtype=np.uint8
#     )
#
#     """
#     n_blocks = int(
#         (data + (header * word) + (sector - 1)) / sector
#     )
#     read_bytes = n_blocks * sector - header * word
#
#     assert read_bytes == data