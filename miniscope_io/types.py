"""
Type and type annotations
"""

import sys
from typing import Annotated, Tuple, Union

from pydantic import AfterValidator

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias


def _is_identifier(val: str) -> str:
    for part in val.split("."):
        assert part.isidentifier(), f"{part} is not a valid python identifier within {val}"
    return val


Range: TypeAlias = Union[Tuple[int, int], Tuple[float, float]]
PythonIdentifier: TypeAlias = Annotated[str, AfterValidator(_is_identifier)]
"""
A valid python identifier, including globally namespace pathed like 
module.submodule.ClassName
"""
