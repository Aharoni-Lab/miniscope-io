"""
Classes for using in-memory data from a miniscope
"""
import numpy as np
from typing import List, Optional, overload, Literal, Union
from miniscope_io.sdcard import DataHeader
from pydantic import BaseModel, field_validator

import pandas as pd

class Frame(BaseModel, arbitrary_types_allowed=True):
    data: Optional[np.ndarray] = None
    headers: Optional[List[DataHeader]] = None

    @field_validator('headers')
    @classmethod
    def frame_nums_must_be_equal(cls, v:List[DataHeader]) -> Optional[List[DataHeader]]:
        if v is not None and not all([header.frame_num != v[0].frame_num for header in v]):
            raise ValueError(f"All frame numbers should be equal! Got f{[h.frame_num for h in v]}")
        return v

    @property
    def frame_num(self) -> int:
        """
        Frame number for this set of headers
        """
        return self.headers[0].frame_num


class Frames(BaseModel):
    frames: List[Frame]

    @overload
    def flatten_headers(self, as_dict:Literal[False] = False) -> List[DataHeader]: ...

    @overload
    def flatten_headers(self, as_dict:Literal[True] = True) -> List[dict]: ...

    def flatten_headers(self, as_dict:bool = False) -> Union[List[dict],List[DataHeader]]:
        """
        Return flat list of headers, not grouped by frame

        Args:
            as_dict (bool): If `True`, return a list of dictionaries, if `False` (default),
                return a list of :class:`.DataHeader` s.
        """
        h = []
        for frame in self.frames:
            if as_dict:
                headers = [header.model_dump() for header in frame.headers]
            else:
                headers = frame.headers
            h.extend(headers)
        return h

    def to_df(self, what:Literal['headers']='headers') -> pd.DataFrame:
        """
        Convert frames to pandas dataframe

        Arguments:
            what ('headers'): What information from the frame to include in the df,
                currently only 'headers' is possible
        """

        if what == "headers":
            return pd.DataFrame(self.flatten_headers(as_dict=True))
        else:
            raise ValueError('Return mode not implemented!')

