# Configuration

```{tip}
See also the API docs in {mod}`mio.models.config`
```

Config in `mio` uses a combination of pydantic models and
[`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

Configuration takes a few forms:

- **Global config:** control over basic operation of `mio` like logging,
  location of user directories, plugins, etc.
- **Device config:** control over the operation of specific devices and miniscopes like
  firmware versions, ports, capture parameters, etc.
- **Runtime/experiment config:** control over how a device behaves when it runs, like
  plotting, data output, etc.

## Global Config

Global config uses the {class}`~mio.models.config.Config` class

Config values can be set (in order of priority from high to low, where higher
priorities override lower priorities)

* in the arguments passed to the class constructor (not user configurable)
* in environment variables like `export MIO_LOG_DIR=~/`
* in a `.env` file in the working directory
* in a `mio_config.yaml` file in the working directory
* in the `tool.mio.config` table in a `pyproject.toml` file in the working directory
* in a user `mio_config.yaml` file in the user directory (see [below](user-directory))
* in the global `mio_config.yaml` file in the platform-specific data directory
  (use `mio config global path` to find its location)
* the default values in the {class}`~mio.models.config.Config` model

Parent directories are _not_ checked - `.env` files, `mio_config.yaml`, and `pyproject.toml`
files need to be in the current working directory to be discovered.

You can see your current configuration with `mio config`

(user-directory)=
### User Directory

The configuration system allows project-specific configs per-directory with
`mio_config.yaml` files in the working directory, as well as global configuration
via `mio_config.yaml` in the system-specific config directory 
(via [platformdirs](https://pypi.org/project/platformdirs/)). 
By default, `mio` does not create new directories in the user's home directory
to be polite, but the site config directory might be inconvenient or hard to reach,
so it's possible to create a user directory in a custom location.

`mio` discovers this directory from the `user_dir` setting from 
any of the available sources, though the global `mio_config.yaml` file is the most reliable.

To create a user directory, use the `mio config user create` command.
(ignore the `--dry-run` flag, which are just used to avoid
overwriting configs while rendering the docs ;)

```{command-output} mio config user create ~/my_new_directory --dry-run
```   

You can confirm that this will be where mio discovers the user directory like

```{command-output} mio config user path
```

If a directory is not supplied, the default `~/.config/mio` is used:

```{command-output} mio config user create --dry-run
```

### Setting Values

```{todo}
Implement setting values from CLI.

For now, please edit the configuration files directly.
```

### Keys

#### Prefix

Keys for environment variables (i.e. set in a shell with e.g. `export` or in a `.env` file)
are prefixed with `MIO_` to not shadow other environment variables.
Keys in `toml` or `yaml` files are not prefixed with `MIO_` .

#### Nesting

Keys for nested models are separated by a `__` double underscore in `.env`
files or environment variables (eg. `MIO_LOGS__LEVEL`)

Keys in `toml` or `yaml` files do not have a dunder separator because
they can represent the nesting directly (see examples below)

When setting values from the cli, keys for nested models are separated with a `.`.

#### Case

Keys are case-insensitive, i.e. these are equivalent::

    export MIO_LOGS__LEVEL=INFO
    export mio_logs__level=INFO

### Examples

`````{tab-set}
````{tab-item} mio_config.yaml
```{code-block} yaml
user_dir: ~/.config/mio
log_dir: ~/.config/mio/logs
logs:
  level_file: INFO
  level_stream: WARNING
  file_n: 5
``` 
````
````{tab-item} env vars
```{code-block} bash
export MIO_USER_DIR='~/.config/mio'
export MIO_LOG_DIR='~/config/mio/logs'
export MIO_LOGS__LEVEL_FILE='INFO'
export MIO_LOGS__LEVEL_STREAM='WARNING'
export MIO_LOGS__FILE_N=5
```
````
````{tab-item} .env file
```{code-block} python
MIO_USER_DIR='~/.config/mio'
MIO_LOG_DIR='~/config/mio/logs'
MIO_LOG__LEVEL_FILE='INFO'
MIO_LOG__LEVEL_STREAM='WARNING'
MIO_LOG__FILE_N=5
```
````
````{tab-item} pyproject.toml
```{code-block} toml
[tool.mio.config]
user_dir = "~/.config/mio"

[tool.linkml.config.log]
dir = "~/config/mio/logs"
level_file = "INFO"
level_stream = "WARNING"
file_n = 5
``` 
````
````{tab-item} cli
TODO
````
`````

## Device Configs

```{todo}
Document device configuration
```