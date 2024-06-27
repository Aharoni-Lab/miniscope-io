import os
from pathlib import Path
from miniscope_io import Config

def test_config(tmp_path):
    """
    Config should be able to make directories and set sensible defaults
    """
    config = Config(base_dir = tmp_path)
    assert config.base_dir.exists()
    assert config.log_dir.exists()
    assert config.log_dir == config.base_dir / 'logs'


def test_config_from_environment(tmp_path):
    """
    Setting environmental variables should set the config, including recursive models
    """
    os.environ['MINISCOPE_IO_BASE_DIR'] = str(tmp_path)
    # we can also override the default log dir name
    override_logdir = Path(tmp_path) / 'fancylogdir'
    os.environ['MINISCOPE_IO_LOG_DIR'] = str(override_logdir)
    # and also recursive models
    os.environ['MINISCOPE_IO_LOGS__LEVEL'] = 'error'

    config = Config()
    assert config.base_dir == Path(tmp_path)
    assert config.log_dir == override_logdir
    assert config.logs.level == 'error'.upper()
    del os.environ['MINISCOPE_IO_BASE_DIR']
    del os.environ['MINISCOPE_IO_LOG_DIR']
    del os.environ['MINISCOPE_IO_LOGS__LEVEL']


def test_config_from_dotenv(tmp_path):
    """
    dotenv files should also set config

    this test can be more relaxed since its basically a repetition of previous
    """
    tmp_path.mkdir(exist_ok=True,parents=True)
    dotenv = tmp_path / '.env'
    with open(dotenv, 'w') as denvfile:
        denvfile.write(f'MINISCOPE_IO_BASE_DIR={str(tmp_path)}')

    config = Config(_env_file=dotenv, _env_file_encoding='utf-8')
    assert config.base_dir == Path(tmp_path)
