import pdb

import pytest
import os
import tempfile
from pathlib import Path
from miniscope_io import Config

def test_config():
    """
    Config should be able to make directories and set sensible defaults
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)

        config = Config(base_dir = tmpdir)
        assert config.base_dir.exists()
        assert config.log_dir.exists()
        assert config.log_dir == config.base_dir / 'logs'


def test_config_from_environment():
    """
    Setting environmental variables should set the config, including recursive models
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.environ['MINISCOPE_IO_BASE_DIR'] = str(tmpdirname)
        # we can also override the default log dir name
        override_logdir = Path(tmpdirname) / 'fancylogdir'
        os.environ['MINISCOPE_IO_LOG_DIR'] = str(override_logdir)
        # and also recursive models
        os.environ['MINISCOPE_IO_LOGS__LEVEL'] = 'error'

        config = Config()
        assert config.base_dir == Path(tmpdirname)
        assert config.log_dir == override_logdir
        assert config.logs.level == 'error'
        del os.environ['MINISCOPE_IO_BASE_DIR']
        del os.environ['MINISCOPE_IO_LOG_DIR']
        del os.environ['MINISCOPE_IO_LOGS__LEVEL']


def test_config_from_dotenv():
    """
    dotenv files should also set config

    this test can be more relaxed since its basically a repetition of previous
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        dotenv = Path(tmpdirname) / '.env'
        with open(dotenv, 'w') as denvfile:
            denvfile.write(f'MINISCOPE_IO_BASE_DIR="{tmpdirname}"')

        config = Config(_env_file=dotenv, _env_file_encoding='utf-8')
        assert config.base_dir == Path(tmpdirname)
