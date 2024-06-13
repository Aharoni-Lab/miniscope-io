"""
Mixin classes that are to be used alongside specific models
to use composition for functionality and inheritance for semantics.
"""

import yaml

from typing import TypeVar, Type

T = TypeVar('T')


class YAMLMixin:
    """
    Mixin class that provides :meth:`.from_yaml` and :meth:`.to_yaml`
    classmethods
    """

    @classmethod
    def from_yaml(cls: Type[T], file_path: str) -> T:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return cls(**config_data)
