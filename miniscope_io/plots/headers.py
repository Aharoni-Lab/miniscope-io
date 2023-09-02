from typing import TYPE_CHECKING, Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sdcard import DataHeader

def buffer_count(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    cols = ('write_buffer_count', 'dropped_buffer_count', 'buffer_count')
    labels = ('Write Buffer', 'Dropped Buffer', 'Total Buffer')
    for col, label in zip(cols, labels):
        ax[0].plot(headers[col], label=label)
    ax.legend()
    ax.set_xlabel('Buffer index')
    ax.set_xlabel('Buffer count')
    return ax

def dropped_buffers(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    ax.plot(headers['dropped_buffer_count'], label='Dropped buffers')
    ax.legend()
    ax.set_xlabel('Buffer index')
    return ax

def timestamps(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    frames = headers['frame_num'].max() - headers['frame_num'].min()
    seconds = headers['timestamp'].max() - headers['timestamp'].min()
    fps = frames/seconds

    ax.plot(headers['timestamp'], headers['frame_num'],
               label=f'Record: {fps:.2f} FPS')
    ax.legend()
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Frame Count")
    return ax

def battery_voltage(headers: pd.DataFrame, ax: plt.Axes) -> plt.Axes:
    ax.plot(headers['timestamp'], headers['battery_voltage'],
            label='Battery voltage')
    ax.legend()
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Battery Voltage')
    return ax

def plot_headers(headers: pd.DataFrame) -> (plt.Figure, plt.Axes):
    """
    Plot the headers (generated from :meth:`.Frame.to_df` )

    Mimicking the plot in https://github.com/Aharoni-Lab/Miniscope-v4-Wire-Free/blob/2fd86cc85b810b2ecc6f71c8ee2dffdb838badcf/Miniscope-v4-Wire-Free-Python%20DAQ%20Interface/Load%20raw%20data%20from%20SD%20card%20and%20write%20video%20-%20WireFree%20V4%20Miniscope.ipynb
    For more generic plotting, see :meth:`pandas.DataFrame.plot`

    Arguments:
        headers (:class:`pandas.DataFrame`): headers to plot
    """
    if 'battery_voltage' in headers.columns:
        subplots = 4
    else:
        subplots = 3

    fig, ax =  plt.subplots(1,subplots)

    # Successful Buffers
    ax[0] = buffer_count(headers, ax[0])

    # Dropped buffers
    ax[1] = dropped_buffers(headers, ax[1])

    # fps/timestamps
    ax[2] = timestamps(headers, ax[2])

    if 'battery_voltage' in headers.columns:
        ax[3] = battery_voltage(headers, ax[3])

    return fig, ax




