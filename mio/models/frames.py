"""
Pydantic models for storing frames and videos.
"""

from typing import List, Optional, TypeVar

import numpy as np
from pydantic import BaseModel, Field, model_validator

T = TypeVar("T", np.ndarray, List[np.ndarray], List[List[np.ndarray]])


class NamedFrame(BaseModel):
    """
    Pydantic model to store an array (frame/video/video list) together with a name.
    """

    name: str = Field(
        ...,
        description="Name of the video.",
    )
    static_frame: Optional[np.ndarray] = Field(
        None,
        description="Frame data, if provided.",
    )
    video_frame: Optional[List[np.ndarray]] = Field(
        None,
        description="Video data, if provided.",
    )
    video_list_frame: Optional[List[List[np.ndarray]]] = Field(
        None,
        description="List of video data, if provided.",
    )
    frame_type: Optional[str] = Field(
        None,
        description="Type of frame data.",
    )

    @model_validator(mode="before")
    def check_frame_type(cls, values: dict) -> dict:
        """
        Ensure that exactly one of static_frame, video_frame, or video_list_frame is provided.
        """
        static = values.get("static_frame")
        video = values.get("video_frame")
        video_list = values.get("video_list_frame")

        # Identify which fields are present
        present_fields = [
            (field_name, field_value)
            for field_name, field_value in zip(
                ("static_frame", "video_frame", "video_list_frame"), (static, video, video_list)
            )
            if field_value is not None
        ]

        if len(present_fields) != 1:
            raise ValueError(
                "Exactly one of static_frame, video_frame, or video_list_frame must be provided."
            )

        # Record which frame type is present
        values["frame_type"] = present_fields[0][0]

        return values

    @property
    def data(self) -> T:
        """Return the content of the populated field."""
        if self.frame_type == "static_frame":
            return self.static_frame
        elif self.frame_type == "video_frame":
            return self.video_frame
        elif self.frame_type == "video_list_frame":
            return self.video_list_frame
        else:
            raise ValueError("Unknown frame type or no frame data provided.")

    class Config:
        """
        Pydantic config for allowing np.ndarray types.
        Could be an Numpydantic situation so will look into it later.
        """

        arbitrary_types_allowed = True
