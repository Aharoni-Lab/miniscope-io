"""
Mixin classes that are to be used alongside specific models
to use composition for functionality and inheritance for semantics.
"""

from pathlib import Path
from typing import Any, Optional, Type, TypeVar, Union

import yaml
from pydantic import BaseModel

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
        data = self.model_dump(**kwargs) if isinstance(self, BaseModel) else self.__dict__

        data = yaml.dump(data, Dumper=YamlDumper)

        if path:
            with open(path, "w") as file:
                file.write(data)

        return data
