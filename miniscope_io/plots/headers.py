"""
Plot headers from :class:`.SDCard`
"""

from logging import Logger
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from miniscope_io.models.stream import StreamBufferHeader

try:
    import matplotlib.pyplot as plt
except ImportError as e:
    raise ImportError(
        "matplotlib is not a required dependency of miniscope-io, "
        "install it with the miniscope-io[plot] extra or manually in your environment :)"
    ) from e


def buffer_count(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    """
    Plot number of buffers by time
    """
    cols = ("write_buffer_count", "dropped_buffer_count", "buffer_count")
    labels = ("Write Buffer", "Dropped Buffer", "Total Buffer")
    for col, label in zip(cols, labels):
        ax.plot(headers[col], label=label)
    ax.legend()
    ax.set_xlabel("Buffer index")
    ax.set_xlabel("Buffer count")
    return ax


def dropped_buffers(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    """
    Plot number of buffers by time
    """
    ax.plot(headers["dropped_buffer_count"], label="Dropped buffers")
    ax.legend()
    ax.set_xlabel("Buffer index")
    return ax


def timestamps(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    """
    Plot frame number against time
    """
    frames = headers["frame_num"].max() - headers["frame_num"].min()
    seconds = headers["timestamp"].max() - headers["timestamp"].min()
    fps = frames / seconds

    ax.plot(headers["timestamp"], headers["frame_num"], label=f"Record: {fps:.2f} FPS")
    ax.legend()
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Frame Count")
    return ax


def battery_voltage(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    """
    Plot battery voltage against time
    """
    ax.plot(headers["timestamp"], headers["battery_voltage"], label="Battery voltage")
    ax.legend()
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Battery Voltage")
    return ax


def plot_headers(
    headers: pd.DataFrame, size: Optional[Tuple[int, int]] = None
) -> (plt.Figure, plt.Axes):
    """
    Plot the headers (generated from :meth:`.Frame.to_df` )

    Mimicking the plot in https://github.com/Aharoni-Lab/Miniscope-v4-Wire-Free/blob/2fd86cc85b810b2ecc6f71c8ee2dffdb838badcf/Miniscope-v4-Wire-Free-Python%20DAQ%20Interface/Load%20raw%20data%20from%20SD%20card%20and%20write%20video%20-%20WireFree%20V4%20Miniscope.ipynb
    For more generic plotting, see :meth:`pandas.DataFrame.plot`

    Arguments:
        headers (:class:`pandas.DataFrame`): headers to plot
        size (tuple[int, int]): Manually override plot ``(width, height)`` . Arbitrary units
    """
    subplots = 4 if "battery_voltage" in headers.columns else 3

    fig, ax = plt.subplots(1, subplots)

    # Successful Buffers
    ax[0] = buffer_count(headers, ax[0])

    # Dropped buffers
    ax[1] = dropped_buffers(headers, ax[1])

    # fps/timestamps
    ax[2] = timestamps(headers, ax[2])

    if "battery_voltage" in headers.columns:
        ax[3] = battery_voltage(headers, ax[3])

    if size is None:
        size = ((subplots * 3) + 1, 3)

    fig.set_figwidth(size[0])
    fig.set_figheight(size[1])

    return fig, ax

class StreamPlotter:
    """
    Plot headers from StreamDaq
    """

    def __init__(
        self,
        header_keys: str,
        history_length: int = 100,
    ) -> None:
        """
        Constructor of StreamPlotter.

        Parameters:
            header_keys: List of header keys to plot
            history_length: Number of headers to plot
        """    
        self.header_keys = header_keys
        self.history_length = history_length
        
        # initialize matplotlib
        plt.ion()
        plt.figure()

        metadata_trunc = np.zeros((0, 2))
        x_data = metadata_trunc[:, 0]
        y_data = metadata_trunc[:, 1]
        self.li, = plt.plot(x_data, y_data)

        plt.xlabel("index")
        plt.ylabel(header_keys)
        plt.title(header_keys)

    def _get_streamheader_values(
            self,
            header: List[StreamBufferHeader],
            ) -> np.ndarray:
        """
        Extract the values from the StreamBufferHeader objects.

        Parameters:
            header: List of StreamBufferHeader objects
        """
        if len(header) < 1:
            return np.zeros((0, 2))

        sliced_list = header if len(header) < self.history_length else header[-self.history_length:]

        extracted_values = []

        for index, item in enumerate(sliced_list):
            if hasattr(item, self.header_keys):
                extracted_values.append((index, getattr(item, self.header_keys)))

        if not extracted_values:
            return np.zeros((0, 2))

        return np.array(extracted_values)
    
    def update_plot(
            self,
            header: List[StreamBufferHeader],
            ) -> None:
        """
        Update the plot with the latest data.

        Parameters:
            header: List of StreamBufferHeader objects
        """
        metadata_trunc = self._get_streamheader_values(header)
        x_data = metadata_trunc[:, 0]
        y_data = metadata_trunc[:, 1]
        if len(x_data) > 0 and len(y_data) > 0:
            self.li.set_xdata(x_data)
            self.li.set_ydata(y_data)
            plt.xlim(x_data.min(), x_data.max())
            plt.ylim(y_data.min(), y_data.max())
            plt.draw()
            plt.pause(0.01)