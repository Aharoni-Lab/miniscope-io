"""
Mixin classes that are to be used alongside specific models
to use composition for functionality and inheritance for semantics.
"""

from pathlib import Path
from typing import Type, TypeVar, Union

import yaml

T = TypeVar("T")


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
