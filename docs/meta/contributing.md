# Contributing

Standard flow:
- Fork the repository
- Create a new branch from `main`
- ~ do work ~
- Open pull request against `miniscope-io:main`
- Code review and discussion happens
- Merge contribution

normal i guess.

## Norms

- All new code should be tested if possible. Since this is a hardware
  interface package, some things may be impossible to test. For any
  major new hardware functionality, a mock class should be written
  to isolate software and hardware testing.
- All modifications to code should be documented: this includes both
  API documentation in docstrings as well as narrative usage documentation
  in the `docs` directory.

## Code of Conduct

(forthcoming, for now BDFLs enforce kindness and inclusiveness with their
arbitrary and expansive power)

## Development Environment

Install using the `all` extra, which should have all other extras in it

```shell
pdm install --with all
# or
pip install '.[all]'
```

### Linting

`miniscope-io` uses `black` for code formatting and `ruff` for linting.
We recommend you configure your IDE to do both automatically.

There are a few ways you can run linting manually:

First, just by running the raw commands:

```shell
ruff check --fix
black miniscope_io
```

Or you can use the `pre-commit` action to automatically run them
before committing code:

```shell
pre-commit install
```

Or you can use the `noxfile.py`

```shell
# just lint without formatting
nox -s lint
# lint and apply formatting
nox -s format
```





