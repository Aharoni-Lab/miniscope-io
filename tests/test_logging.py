import pdb

import pytest
import os
import tempfile
from pathlib import Path

from miniscope_io.logging import init_logger

def test_init_logger(capsys):
    """
    We should be able to
    - log to file and stdout
    - with separable levels
    """
    with tempfile.TemporaryDirectory() as tmpfilename:
        # os.environ['MINISCOPE_IO_BASE_DIR'] = tmpfilename
        #
        log_dir = Path(tmpfilename) / 'logs'
        log_dir.mkdir()
        log_file = log_dir / 'miniscope_io.test_logger.log'
        logger = init_logger(
            name='test_logger',
            log_dir=log_dir,
            level='INFO',
            file_level='WARNING'
        )
        warn_msg = 'Both loggers should show'
        logger.warning(warn_msg)

        # can't test for presence of string because logger can split lines depending on size of console
        # but there should be one WARNING in stdout
        captured = capsys.readouterr()
        assert 'WARNING' in captured.out

        with open(log_file, 'r') as lfile:
            log_str = lfile.read()
        assert 'WARNING' in log_str

        info_msg = "Now only stdout should show"
        logger.info(info_msg)
        captured = capsys.readouterr()
        assert 'INFO' in captured.out
        with open(log_file, 'r') as lfile:
            log_str = lfile.read()
        assert 'INFO' not in log_str


