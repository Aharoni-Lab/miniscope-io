import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml
import numpy as np
import tomli_w

from miniscope_io import Config
from miniscope_io.models.config import _global_config_path, set_user_dir
from miniscope_io.models.mixins import YamlDumper


@pytest.fixture(scope="module", autouse=True)
def dodge_existing_configs(tmp_path_factory):
    """
    Suspend any existing global config file during config tests
    """
    tmp_path = tmp_path_factory.mktemp("config_backup")
    global_config_path = _global_config_path
    backup_global_config_path = tmp_path / "mio_config.yaml.global.bak"

    user_config_path = list(Config().user_dir.glob("mio_config.*"))
    if len(user_config_path) == 0:
        user_config_path = None
    else:
        user_config_path = user_config_path[0]

    backup_user_config_path = tmp_path / "mio_config.yaml.user.bak"

    dotenv_path = Path(".env").resolve()
    dotenv_backup_path = tmp_path / "dotenv.bak"

    if global_config_path.exists():
        global_config_path.rename(backup_global_config_path)
    if user_config_path is not None and user_config_path.exists():
        user_config_path.rename(backup_user_config_path)
    if dotenv_path.exists():
        dotenv_path.rename(dotenv_backup_path)

    yield

    if backup_global_config_path.exists():
        global_config_path.unlink(missing_ok=True)
        backup_global_config_path.rename(global_config_path)
    if backup_user_config_path.exists():
        user_config_path.unlink(missing_ok=True)
        backup_user_config_path.rename(user_config_path)
    if dotenv_backup_path.exists():
        dotenv_path.unlink(missing_ok=True)
        dotenv_backup_path.rename(dotenv_path)


@pytest.fixture()
def tmp_cwd(tmp_path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture()
def set_env(monkeypatch) -> Callable[[dict[str, Any]], None]:
    """
    Function fixture to set environment variables using a nested dict
    matching a GlobalConfig.model_dump()
    """

    def _set_env(config: dict[str, Any]) -> None:
        for key, value in _flatten(config).items():
            key = "MINISCOPE_IO_" + key.upper()
            monkeypatch.setenv(key, str(value))

    return _set_env


@pytest.fixture()
def set_dotenv(tmp_cwd) -> Callable[[dict[str, Any]], Path]:
    """
    Function fixture to set config variables in a .env file
    """
    dotenv_path = tmp_cwd / ".env"

    def _set_dotenv(config: dict[str, Any]) -> Path:
        with open(dotenv_path, "w") as dfile:
            for key, value in _flatten(config).items():
                key = "MINISCOPE_IO_" + key.upper()
                dfile.write(f"{key}={value}\n")
        return dotenv_path

    return _set_dotenv


@pytest.fixture()
def set_pyproject(tmp_cwd) -> Callable[[dict[str, Any]], Path]:
    """
    Function fixture to set config variables in a pyproject.toml file
    """
    toml_path = tmp_cwd / "pyproject.toml"

    def _set_pyproject(config: dict[str, Any]) -> Path:
        config = {"tool": {"miniscope_io": {"config": config}}}

        with open(toml_path, "wb") as tfile:
            tomli_w.dump(config, tfile)

        return toml_path

    return _set_pyproject


@pytest.fixture()
def set_local_yaml(tmp_cwd) -> Callable[[dict[str, Any]], Path]:
    """
    Function fixture to set config variables in a mio_config.yaml file in the current directory
    """
    yaml_path = tmp_cwd / "mio_config.yaml"

    def _set_local_yaml(config: dict[str, Any]) -> Path:
        with open(yaml_path, "w") as yfile:
            yaml.dump(config, yfile, Dumper=YamlDumper)
        return yaml_path

    return _set_local_yaml


@pytest.fixture()
def set_user_yaml(tmp_path) -> Callable[[dict[str, Any]], Path]:
    """
    Function fixture to set config variables in a user config file
    """
    yaml_path = tmp_path / "user" / "mio_config.yaml"
    yaml_path.parent.mkdir(exist_ok=True)

    def _set_user_yaml(config: dict[str, Any]) -> Path:
        with open(yaml_path, "w") as yfile:
            yaml.dump(config, yfile, Dumper=YamlDumper)
        set_user_dir(yaml_path.parent)
        return yaml_path

    yield _set_user_yaml

    _global_config_path.unlink(missing_ok=True)


@pytest.fixture()
def set_global_yaml() -> Callable[[dict[str, Any]], Path]:
    """
    Function fixture to reversibly set config variables in a global mio_config.yaml file
    """

    def _set_global_yaml(config: dict[str, Any]) -> Path:
        with open(_global_config_path, "w") as gfile:
            yaml.dump(config, gfile, Dumper=YamlDumper)
        return _global_config_path

    yield _set_global_yaml

    _global_config_path.unlink(missing_ok=True)


@pytest.fixture(
    params=[
        "set_env",
        "set_dotenv",
        "set_pyproject",
        "set_local_yaml",
        "set_user_yaml",
        "set_global_yaml",
    ]
)
def set_config(request) -> Callable[[dict[str, Any]], Path]:
    return request.getfixturevalue(request.param)


def test_config(tmp_path):
    """
    Config should be able to make directories and set sensible defaults
    """
    config = Config(user_dir=tmp_path)
    assert config.user_dir.exists()
    assert config.log_dir.exists()
    assert config.log_dir == config.user_dir / "logs"


def test_set_config(set_config, tmp_path):
    """We should be able to set parameters from all available modalities"""
    file_n = int(np.random.default_rng().integers(0, 100))
    user_dir = tmp_path / f"fake/dir/{np.random.default_rng().integers(0, 100)}"

    set_config({"user_dir": str(user_dir), "logs": {"file_n": file_n}})

    config = Config()
    assert config.user_dir == user_dir
    assert config.logs.file_n == file_n


def test_config_from_environment(tmp_path):
    """
    Setting environmental variables should set the config, including recursive models
    """
    os.environ["MINISCOPE_IO_USER_DIR"] = str(tmp_path)
    # we can also override the default log dir name
    override_logdir = Path(tmp_path) / "fancylogdir"
    os.environ["MINISCOPE_IO_LOG_DIR"] = str(override_logdir)
    # and also recursive models
    os.environ["MINISCOPE_IO_LOGS__LEVEL"] = "error"

    config = Config()
    assert config.user_dir == Path(tmp_path)
    assert config.log_dir == override_logdir
    assert config.logs.level == "error".upper()
    del os.environ["MINISCOPE_IO_USER_DIR"]
    del os.environ["MINISCOPE_IO_LOG_DIR"]
    del os.environ["MINISCOPE_IO_LOGS__LEVEL"]


def test_config_from_dotenv(tmp_path):
    """
    dotenv files should also set config

    this test can be more relaxed since its basically a repetition of previous
    """
    tmp_path.mkdir(exist_ok=True, parents=True)
    dotenv = tmp_path / ".env"
    with open(dotenv, "w") as denvfile:
        denvfile.write(f"MINISCOPE_IO_USER_DIR={str(tmp_path)}")

    config = Config(_env_file=dotenv, _env_file_encoding="utf-8")
    assert config.user_dir == Path(tmp_path)


def test_set_user_dir(tmp_path):
    """
    We should be able to set the user dir and the global config should respect it
    """
    user_config = tmp_path / "mio_config.yml"
    file_n = int(np.random.default_rng().integers(0, 100))
    with open(user_config, "w") as yfile:
        yaml.dump({"logs": {"file_n": file_n}}, yfile)

    set_user_dir(tmp_path)

    with open(_global_config_path, "r") as gfile:
        global_config = yaml.safe_load(gfile)

    assert global_config["user_dir"] == str(tmp_path)
    assert Config().user_dir == tmp_path
    assert Config().logs.file_n == file_n

    # we do this manual cleanup here and not in a fixture because we are testing
    # that the things we are doing in the fixtures are working correctly!
    _global_config_path.unlink(missing_ok=True)


def test_config_sources_overrides(
    set_env, set_dotenv, set_pyproject, set_local_yaml, set_user_yaml, set_global_yaml
):
    """Test that the different config sources are overridden in the correct order"""
    set_global_yaml({"logs": {"file_n": 0}})
    assert Config().logs.file_n == 0
    set_user_yaml({"logs": {"file_n": 1}})
    assert Config().logs.file_n == 1
    set_pyproject({"logs": {"file_n": 2}})
    assert Config().logs.file_n == 2
    set_local_yaml({"logs": {"file_n": 3}})
    assert Config().logs.file_n == 3
    set_dotenv({"logs": {"file_n": 4}})
    assert Config().logs.file_n == 4
    set_env({"logs": {"file_n": 5}})
    assert Config().logs.file_n == 5
    assert Config(**{"logs": {"file_n": 6}}).logs.file_n == 6


def _flatten(d, parent_key="", separator="__") -> dict:
    """https://stackoverflow.com/a/6027615/13113166"""
    items = []
    for key, value in d.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(_flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)
