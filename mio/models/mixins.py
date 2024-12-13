"""
Mixin classes that are to be used alongside specific models
to use composition for functionality and inheritance for semantics.
"""

import re
import shutil
from importlib.metadata import version
from itertools import chain
from pathlib import Path
from typing import Any, ClassVar, List, Literal, Optional, Type, TypeVar, Union, overload

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from mio.types import ConfigID, ConfigSource, PythonIdentifier, valid_config_id

T = TypeVar("T")


class YamlDumper(yaml.SafeDumper):
    """Dumper that can represent extra types like Paths"""

    def represent_path(self, data: Path) -> yaml.ScalarNode:
        """Represent a path as a string"""
        return self.represent_scalar("tag:yaml.org,2002:str", str(data))


YamlDumper.add_representer(type(Path()), YamlDumper.represent_path)


class YAMLMixin:
    """
    Mixin class that provides :meth:`.from_yaml` and :meth:`.to_yaml`
    classmethods
    """

    @classmethod
    def from_yaml(cls: Type[T], file_path: Union[str, Path]) -> T:
        """Instantiate this class by passing the contents of a yaml file as kwargs"""
        with open(file_path) as file:
            config_data = yaml.safe_load(file)
        return cls(**config_data)

    def to_yaml(self, path: Optional[Path] = None, **kwargs: Any) -> str:
        """
        Dump the contents of this class to a yaml file, returning the
        contents of the dumped string
        """
        data_str = self.to_yamls(**kwargs)
        if path:
            with open(path, "w") as file:
                file.write(data_str)

        return data_str

    def to_yamls(self, **kwargs: Any) -> str:
        """
        Dump the contents of this class to a yaml string

        Args:
            **kwargs: passed to :meth:`.BaseModel.model_dump`
        """
        data = self._dump_data(**kwargs)
        return yaml.dump(data, Dumper=YamlDumper, sort_keys=False)

    def _dump_data(self, **kwargs: Any) -> dict:
        data = self.model_dump(**kwargs) if isinstance(self, BaseModel) else self.__dict__
        return data


class ConfigYAMLMixin(BaseModel, YAMLMixin):
    """
    Yaml Mixin class that always puts a header consisting of

     * `id` - unique identifier for this config
     * `mio_model` - fully-qualified module path to model class
     * `mio_version` - version of mio when this model was created

     at the top of the file.
    """

    id: ConfigID
    mio_model: PythonIdentifier = Field(None, validate_default=True)
    mio_version: str = version("mio")

    HEADER_FIELDS: ClassVar[tuple[str]] = ("id", "mio_model", "mio_version")

    @classmethod
    def from_yaml(cls: Type[T], file_path: Union[str, Path]) -> T:
        """Instantiate this class by passing the contents of a yaml file as kwargs"""
        with open(file_path) as file:
            config_data = yaml.safe_load(file)

        # fill in any missing fields in the source file needed for a header
        config_data = cls._complete_header(config_data, file_path)
        try:
            instance = cls(**config_data)
        except ValidationError:
            if (backup_path := file_path.with_suffix(".yaml.bak")).exists():
                from mio.logging import init_logger

                init_logger("config").debug(
                    f"Model instantiation failed, restoring modified backup from {backup_path}..."
                )
                shutil.copy(backup_path, file_path)
            raise

        return instance

    @classmethod
    def from_id(cls: Type[T], id: ConfigID) -> T:
        """
        Instantiate a model from a config `id` specified in one of the .yaml configs in
        either the user :attr:`.Config.config_dir` or the packaged ``config`` dir.

        .. note::

            this method does not yet validate that the config matches the model loading it

        """
        globs = [src.rglob("*.y*ml") for src in cls.config_sources]
        for config_file in chain(*globs):
            try:
                file_id = yaml_peek("id", config_file)
                if file_id == id:
                    from mio.logging import init_logger

                    init_logger("config").debug(
                        "Model for %s found at %s", cls._model_name(), config_file
                    )
                    return cls.from_yaml(config_file)
            except KeyError:
                continue

        from mio import Config

        raise KeyError(f"No config with id {id} found in {Config().config_dir}")

    @classmethod
    def from_any(cls: Type[T], source: Union[ConfigSource, T]) -> T:
        """
        Try and instantiate a config model from any supported constructor.

        Args:
            source (:class:`.ConfigID`, :class:`.Path`, :class:`.PathLike[str]`):
                Either

                * the ``id`` of a config file in the user configs directory or builtin
                * a relative ``Path`` to a config file, relative to the current working directory
                * a relative ``Path`` to a config file, relative to the user config directory
                * an absolute ``Path`` to a config file
                * an instance of the class to be constructed (returned unchanged)

        """
        if isinstance(source, cls):
            return source
        elif valid_config_id(source):
            return cls.from_id(source)
        else:
            from mio import Config

            source = Path(source)
            if source.suffix in (".yaml", ".yml"):
                if source.exists():
                    # either relative to cwd or absolute
                    return cls.from_yaml(source)
                elif (
                    not source.is_absolute()
                    and (user_source := Config().config_dir / source).exists()
                ):
                    return cls.from_yaml(user_source)

        raise ValueError(
            f"Instance of config model {cls.__name__} could not be instantiated from "
            f"{source} - id or file not found, or type not supported"
        )

    @field_validator("mio_model", mode="before")
    @classmethod
    def fill_mio_model(cls, v: Optional[str]) -> PythonIdentifier:
        """Get name of instantiating model, if not provided"""
        if v is None:
            v = cls._model_name()
        return v

    @classmethod
    @property
    def config_sources(cls: Type[T]) -> List[Path]:
        """
        Directories to search for config files, in order of priority
        such that earlier sources are preferred over later sources.
        """
        from mio import CONFIG_DIR, Config

        return [Config().config_dir, CONFIG_DIR]

    def _dump_data(self, **kwargs: Any) -> dict:
        """Ensure that header is prepended to model data"""
        return {**self._yaml_header(self), **super()._dump_data(**kwargs)}

    @classmethod
    def _model_name(cls) -> PythonIdentifier:
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def _yaml_header(cls, instance: Union[T, dict]) -> dict:
        if isinstance(instance, dict):
            model_id = instance.get("id", None)
            mio_model = instance.get("mio_model", cls._model_name())
            mio_version = instance.get("mio_version", version("mio"))
        else:
            model_id = getattr(instance, "id", None)
            mio_model = getattr(instance, "mio_model", cls._model_name())
            mio_version = getattr(instance, "mio_version", version("mio"))

        if model_id is None:
            # if missing an id, try and recover with model default cautiously
            # so we throw the exception during validation and not here, for clarity.
            model_id = getattr(cls.model_fields.get("id", None), "default", None)
            if type(model_id).__name__ == "PydanticUndefinedType":
                model_id = None

        return {
            "id": model_id,
            "mio_model": mio_model,
            "mio_version": mio_version,
        }

    @classmethod
    def _complete_header(cls: Type[T], data: dict, file_path: Union[str, Path]) -> dict:
        """fill in any missing fields in the source file needed for a header"""

        missing_fields = set(cls.HEADER_FIELDS) - set(data.keys())
        keys = tuple(data.keys())
        out_of_order = len(keys) >= 3 and keys[0:3] != cls.HEADER_FIELDS

        if missing_fields or out_of_order:
            if missing_fields:
                msg = f"Missing required header fields {missing_fields} in config model "
                f"{str(file_path)}. Updating file (preserving backup)..."
            else:
                msg = f"Header keys were present, but either not at the start of {str(file_path)} "
                "or in out of order. Updating file (preserving backup)..."
            from mio import CONFIG_DIR
            from mio.logging import init_logger

            logger = init_logger(cls.__name__)
            logger.warning(msg)
            logger.debug(data)

            header = cls._yaml_header(data)
            data = {**header, **data}
            if CONFIG_DIR not in file_path.parents:
                shutil.copy(file_path, file_path.with_suffix(".yaml.bak"))
            with open(file_path, "w") as yfile:
                yaml.dump(data, yfile, Dumper=YamlDumper, sort_keys=False)

        return data


@overload
def yaml_peek(
    key: str, path: Union[str, Path], root: bool = True, first: Literal[True] = True
) -> str: ...


@overload
def yaml_peek(
    key: str, path: Union[str, Path], root: bool = True, first: Literal[False] = False
) -> List[str]: ...


@overload
def yaml_peek(
    key: str, path: Union[str, Path], root: bool = True, first: bool = True
) -> Union[str, List[str]]: ...


def yaml_peek(
    key: str, path: Union[str, Path], root: bool = True, first: bool = True
) -> Union[str, List[str]]:
    """
    Peek into a yaml file without parsing the whole file to retrieve the value of a single key.

    This function is _not_ designed for robustness to the yaml spec, it is for simple key: value
    pairs, not fancy shit like multiline strings, tagged values, etc. If you want it to be,
    then i'm afraid you'll have to make a PR about it.

    Returns a string no matter what the yaml type is so ya have to do your own casting if you want

    Args:
        key (str): The key to peek for
        path (:class:`pathlib.Path` , str): The yaml file to peek into
        root (bool): Only find keys at the root of the document (default ``True`` ), otherwise
            find keys at any level of nesting.
        first (bool): Only return the first appearance of the key (default). Otherwise return a
            list of values (not implemented lol)

    Returns:
        str
    """
    if root:
        pattern = re.compile(
            rf"^(?P<key>{key}):\s*\"*\'*(?P<value>\S.*?)\"*\'*$", flags=re.MULTILINE
        )
    else:
        pattern = re.compile(
            rf"^\s*(?P<key>{key}):\s*\"*\'*(?P<value>\S.*?)\"*\'*$", flags=re.MULTILINE
        )

    res = None
    if first:
        with open(path) as yfile:
            for line in yfile:
                res = pattern.match(line)
                if res:
                    break
        if res:
            return res.groupdict()["value"]
    else:
        with open(path) as yfile:
            text = yfile.read()
        res = [match.groupdict()["value"] for match in pattern.finditer(text)]
        if res:
            return res
    raise KeyError(f"Key {key} not found in {path}")
