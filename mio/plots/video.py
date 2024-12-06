"""
Plotting functions for video streams and frames.
"""

from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from matplotlib.backend_bases import KeyEvent
from matplotlib.widgets import Button, Slider


class VideoPlotter:
    """
    Class to display video streams and static images.
    """

    @staticmethod
    def show_video_with_controls(
        video_frames: Union[list[np.ndarray], np.ndarray], titles: list[str] = None, fps: int = 20
    ) -> None:
        """
        Plot multiple video streams or static images side-by-side.
        Can play/pause and navigate frames.

        Parameters
        ----------
        video_frames : list[np.ndarray] or np.ndarray
            List of video streams or static images to display.
            Each element of the list should be a list of frames or a single frame.
        titles : list[str], optional
            List of titles for each stream, by default None
        fps : int, optional
            Frames per second for playback, by default 20
        """
        # Wrap static images in lists to handle them uniformly
        video_frames = [frame if isinstance(frame, list) else [frame] for frame in video_frames]

        num_streams = len(video_frames)
        num_frames = max(len(stream) for stream in video_frames)

        fig, axes = plt.subplots(1, num_streams, figsize=(20, 5))

        frame_displays = []
        for idx, ax in enumerate(axes):
            initial_frame = video_frames[idx][0]
            frame_display = ax.imshow(initial_frame, cmap="gray", vmin=0, vmax=255)
            frame_displays.append(frame_display)
            if titles:
                ax.set_title(titles[idx])
            ax.axis("off")

        # Slider
        ax_slider = plt.axes([0.1, 0.1, 0.65, 0.05], facecolor="lightgoldenrodyellow")
        slider = Slider(
            ax=ax_slider, label="Frame", valmin=0, valmax=num_frames - 1, valinit=0, valstep=1
        )

        playing = [False]  # Use a mutable object to track play state
        ax_button = plt.axes([0.8, 0.1, 0.1, 0.05])
        button = Button(ax_button, "Play/Pause")

        # Callback to toggle play/pause
        def toggle_play(event: KeyEvent) -> None:
            playing[0] = not playing[0]

        button.on_clicked(toggle_play)

        # Update function for the slider and frame displays
        def update_frame(index: int) -> None:
            for idx, frame_display in enumerate(frame_displays):
                # Repeat last frame for static images or when the index is larger than stream length
                if index < len(video_frames[idx]):
                    frame = video_frames[idx][index]
                else:
                    frame = video_frames[idx][-1]  # Keep showing last frame for shorter streams
                frame_display.set_data(frame)
            fig.canvas.draw_idle()

        # Slider update callback
        def on_slider_change(val: float) -> None:
            index = int(slider.val)
            update_frame(index)

        # Connect the slider update function
        slider.on_changed(on_slider_change)

        # Animation function
        def animate(i: int) -> None:
            if playing[0]:
                current_frame = int(slider.val)
                next_frame = (current_frame + 1) % num_frames
                slider.set_val(next_frame)  # This will also trigger on_slider_change

        # Use FuncAnimation to update the figure at the specified FPS
        # This needs to be stored in a variable to prevent animation getting deleted
        ani = animation.FuncAnimation(  # noqa: F841
            fig, animate, frames=num_frames, interval=1000 // fps, blit=False
        )

        plt.show()

    @staticmethod
    def show_video_side_by_side(
        fig: plt.Figure, frames: list[np.ndarray], titles: str = None
    ) -> None:
        """
        Plot a list of frames side by side using matplotlib.

        Parameters
        ----------
        fig : plt.Figure
            Figure to plot on
        frames : list[np.ndarray]
            List of frames to plot
        titles : str, optional
            List of titles for each frame, by default None

        Raises
        ------
        ValueError
            If the number of frames and titles do not match
        """
        num_frames = len(frames)
        plt.clf()  # Clear current figure

        for i, frame in enumerate(frames):
            plt.subplot(1, num_frames, i + 1)
            plt.imshow(frame, cmap="gray")
            if titles:
                plt.title(titles[i])

            plt.axis("off")  # Turn off axis labels

        plt.tight_layout()
        fig.canvas.draw()
