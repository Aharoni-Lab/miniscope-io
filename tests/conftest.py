import pytest

from pathlib import Path

@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / 'data'

@pytest.fixture(scope="session")
def config_dir(data_dir) -> Path:
    return data_dir / 'config'