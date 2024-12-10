import pdb

import pytest
from click.testing import CliRunner

from mio.cli.config import config
from mio import Config
from mio.models import config as _config_mod


@pytest.mark.skip("Needs to be implemented")
def test_cli_stream():
    """should be able to invoke streamdaq, using various capture options"""
    pass


def test_cli_config_show():
    """
    `mio config` should show current config
    """
    runner = CliRunner()
    result = runner.invoke(config)
    cfg_yaml = Config().to_yaml()
    assert cfg_yaml in result.output


def test_cli_config_show_global():
    """
    `mio config global` should show contents of the global config file
    """
    runner = CliRunner()
    result = runner.invoke(config, ["global"])
    cfg_yaml = _config_mod._global_config_path.read_text()
    assert str(_config_mod._global_config_path) in result.output
    assert cfg_yaml in result.output


def test_cli_config_global_path():
    """
    `mio global path` should show the path to the global config file
    """
    runner = CliRunner()
    result = runner.invoke(config, ["global", "path"])
    assert str(_config_mod._global_config_path) in result.output


def test_cli_config_user_show(set_user_yaml):
    """
    `mio config user` should show contents of the user config file
    """
    user_yaml_path = set_user_yaml({"logs": {"level": "WARNING"}})
    runner = CliRunner()
    result = runner.invoke(config, ["user"])
    user_config = user_yaml_path.read_text()
    assert "level: WARNING" in user_config
    assert user_config in result.output


@pytest.mark.parametrize("clean", [True, False])
@pytest.mark.parametrize("dry_run", [True, False])
def test_cli_config_user_create(clean, dry_run, tmp_path):
    """
    `mio config user create` creates a new user config file,
    optionally with clean/dirty mode or dry_run or not
    """
    dry_run_cmd = "--dry-run" if dry_run else "--no-dry-run"
    clean_cmd = "--clean" if clean else "--dirty"

    config_path = tmp_path / "mio_config.yaml"

    runner = CliRunner()
    result = runner.invoke(config, ["user", "create", dry_run_cmd, clean_cmd, str(config_path)])

    if dry_run:
        assert "DRY RUN" in result.output
        assert not config_path.exists()
    else:
        assert "DRY RUN" not in result.output
        assert config_path.exists()

    if clean:
        assert "level" not in result.output
    else:
        assert "level" in result.output

    assert f"user_dir: {str(config_path.parent)}" in result.output


def test_cli_config_user_path(set_env, set_user_yaml):
    """
    `mio config user path` should show the path to the user config file
    """
    user_config_path = set_user_yaml({"logs": {"level": "WARNING"}})

    runner = CliRunner()
    result = runner.invoke(config, ["user", "path"])
    assert str(user_config_path) in result.output
