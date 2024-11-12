import logging
import pytest
from pathlib import Path
import re

from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

from miniscope_io.logging import init_logger


@pytest.fixture(autouse=True)
def reset_root_logger():
    """
    Before each test, reset the root logger
    """
    root_logger = logging.getLogger("miniscope_io")
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)


def test_init_logger(capsys, tmp_path):
    """
    We should be able to
    - log to file and stdout
    - with separable levels
    """

    log_dir = Path(tmp_path) / "logs"
    log_dir.mkdir()
    log_file = log_dir / "miniscope_io.test_logger.log"
    logger = init_logger(name="test_logger", log_dir=log_dir, level="INFO", file_level="WARNING")
    warn_msg = "Both loggers should show"
    logger.warning(warn_msg)

    # can't test for presence of string because logger can split lines depending on size of console
    # but there should be one WARNING in stdout
    captured = capsys.readouterr()
    assert "WARNING" in captured.out

    with open(log_file, "r") as lfile:
        log_str = lfile.read()
    assert "WARNING" in log_str

    info_msg = "Now only stdout should show"
    logger.info(info_msg)
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    with open(log_file, "r") as lfile:
        log_str = lfile.read()
    assert "INFO" not in log_str


def test_nested_loggers(capsys, tmp_path):
    """
    Nested loggers should not double-log
    """
    log_dir = Path(tmp_path) / "logs"
    log_dir.mkdir()

    parent = init_logger("parent", log_dir=log_dir, level="DEBUG", file_level="DEBUG")
    child = init_logger("parent.child", log_dir=log_dir, level="DEBUG", file_level="DEBUG")

    child.debug("hey")
    parent.debug("sup")

    with open(log_dir / "miniscope_io.log") as lfile:
        file_logs = lfile.read()

    root_logger = logging.getLogger("miniscope_io")
    assert len(root_logger.handlers) == 2
    assert len(parent.handlers) == 0
    assert len(child.handlers) == 0

    # only one message of each!
    stdout = capsys.readouterr()
    assert len(re.findall("hey", stdout.out)) == 1
    assert len(re.findall("sup", stdout.out)) == 1
    assert len(re.findall("hey", file_logs)) == 1
    assert len(re.findall("sup", file_logs)) == 1


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR"])
@pytest.mark.parametrize("dotenv_direct_setting", [True, False])
@pytest.mark.parametrize("test_target", ["logger", "RotatingFileHandler", "RichHandler"])
def test_init_logger_from_dotenv(tmp_path, monkeypatch, level, dotenv_direct_setting, test_target):
    """
    Set log levels from dotenv MINISCOPE_IO_LOGS__LEVEL key
    """
    # Feels kind of fragile to hardcode this but I couldn't think of a better way so for now
    level_name_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    tmp_path.mkdir(exist_ok=True, parents=True)
    dotenv = tmp_path / ".env"
    with open(dotenv, "w") as denvfile:
        if dotenv_direct_setting:
            denvfile.write(
                f'MINISCOPE_IO_LOGS__LEVEL="{level}"\n'
                f"MINISCOPE_IO_LOGS__LEVEL_FILE={level}\n"
                f"MINISCOPE_IO_LOGS__LEVEL_STDOUT={level}"
            )
        else:
            denvfile.write(f'MINISCOPE_IO_LOGS__LEVEL="{level}"')

    monkeypatch.chdir(tmp_path)

    dotenv_logger = init_logger(name="test_logger", log_dir=tmp_path)
    root_logger = logging.getLogger("miniscope_io")

    # Separating them for readable summary info
    if test_target == "logger":
        assert dotenv_logger.level == level_name_map.get(level)

    assert len(dotenv_logger.handlers) == 0
    assert len(root_logger.handlers) == 2
    file_handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]
    stream_handlers = [h for h in root_logger.handlers if isinstance(h, RichHandler)]
    assert len(file_handlers) == 1
    assert len(stream_handlers) == 1
    file_handler = file_handlers[0]
    stream_handler = stream_handlers[0]

    if test_target == "RotatingFileHandler":
        assert file_handler.level == level_name_map.get(level)

    elif test_target == "RichHandler":
        # Might be better to explicitly set the level in the handler
        assert stream_handler.level == level_name_map.get(level)
