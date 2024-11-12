"""
Mixin classes that are to be used alongside specific models
to use composition for functionality and inheritance for semantics.
"""

import re
from importlib.metadata import version
from itertools import chain
from pathlib import Path
from typing import Any, List, Literal, Optional, Type, TypeVar, Union, overload

import yaml
from pydantic import BaseModel

from miniscope_io import CONFIG_DIR, Config
from miniscope_io.logging import init_logger

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
        data = self._dump_data(**kwargs)
        data_str = yaml.dump(data, Dumper=YamlDumper, sort_keys=False)

        if path:
            with open(path, "w") as file:
                file.write(data_str)

        return data_str

    def _dump_data(self, **kwargs: Any) -> dict:
        data = self.model_dump(**kwargs) if isinstance(self, BaseModel) else self.__dict__
        return data


class ConfigYAMLMixin(YAMLMixin):
    """
    Yaml Mixin class that always puts a header consisting of

     * `id` - unique identifier for this config
     * `model` - fully-qualified module path to model class
     * `mio_version` - version of miniscope-io when this model was created
    """

    HEADER_FIELDS = {"id", "model", "mio_version"}

    @classmethod
    def from_yaml(cls: Type[T], file_path: Union[str, Path]) -> T:
        """Instantiate this class by passing the contents of a yaml file as kwargs"""
        with open(file_path) as file:
            config_data = yaml.safe_load(file)
        instance = cls(**config_data)

        # fill in any missing fields in the source file needed for a header
        cls._complete_header(instance, config_data, file_path)

        return instance

    @classmethod
    def from_id(cls, id: str) -> T:
        """
        Instantiate a model from a config `id` specified in one of the .yaml configs in
        either the user :attr:`.Config.config_dir` or the packaged ``config`` dir.

        .. note::

            this method does not yet validate that the config matches the model loading it

        """
        for config_file in chain(Config().config_dir.rglob("*.y*ml"), CONFIG_DIR.rglob("*.y*ml")):
            try:
                file_id = yaml_peek("id", config_file)
                if file_id == id:
                    return cls.from_yaml(config_file)
            except KeyError:
                continue
        raise KeyError(f"No config with id {id} found in {Config().config_dir}")

    def _dump_data(self, **kwargs: Any) -> dict:
        """Ensure that header is prepended to model data"""
        return {**self._yaml_header(self), **super()._dump_data(**kwargs)}

    @classmethod
    def _yaml_header(cls, instance: T) -> dict:
        return {
            "id": instance.id,
            "model": f"{cls.__module__}.{cls.__name__}",
            "mio_version": version("miniscope_io"),
        }

    @classmethod
    def _complete_header(
        cls: Type[T], instance: T, data: dict, file_path: Union[str, Path]
    ) -> None:
        """fill in any missing fields in the source file needed for a header"""

        missing_fields = cls.HEADER_FIELDS - set(data.keys())
        if missing_fields:
            logger = init_logger(cls.__name__)
            logger.warning(
                f"Missing required header fields {missing_fields} in config model "
                f"{str(file_path)}. Updating file..."
            )
            header = cls._yaml_header(instance)
            data = {**header, **data}
            with open(file_path, "w") as yfile:
                yaml.safe_dump(data, yfile, sort_keys=False)


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
        pattern = re.compile(rf"^(?P<key>{key}):\s*(?P<value>\S.*)")
    else:
        pattern = re.compile(rf"^\s*(?P<key>{key}):\s*(?P<value>\S.*)")

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
