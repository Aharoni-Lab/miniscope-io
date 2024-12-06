"""
This module contains functions for pre-processing video data.
"""

from typing import Iterator, Tuple

import cv2
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider

from miniscope_io import init_logger

logger = init_logger("video")

def plot_video_streams_with_controls(
        video_frames: list[list[np.ndarray] or np.ndarray],
        titles: list[str] = None,
        fps: int = 20
        ) -> None:
    """
    Plot multiple video streams or static images side-by-side.
    Can play/pause and navigate frames.
    """
    # Wrap static images in lists to handle them uniformly
    video_frames = [frame if isinstance(frame, list) else [frame] for frame in video_frames]

    num_streams = len(video_frames)
    num_frames = max(len(stream) for stream in video_frames)

    fig, axes = plt.subplots(1, num_streams, figsize=(20, 5))

    frame_displays = []
    for idx, ax in enumerate(axes):
        # Adjust static images to display them consistently
        initial_frame = video_frames[idx][0]
        frame_display = ax.imshow(initial_frame, cmap='gray', vmin=0, vmax=255)
        frame_displays.append(frame_display)
        if titles:
            ax.set_title(titles[idx])
        ax.axis('off')

    # Define the slider
    ax_slider = plt.axes([0.1, 0.1, 0.65, 0.05], facecolor='lightgoldenrodyellow')
    slider = Slider(ax=ax_slider, label='Frame', valmin=0, valmax=num_frames - 1, valinit=0, valstep=1)

    playing = [False]  # Use a mutable object to track play state
    ax_button = plt.axes([0.8, 0.1, 0.1, 0.05])
    button = Button(ax_button, 'Play/Pause')
    
    # Callback to toggle play/pause
    def toggle_play(event):
        playing[0] = not playing[0]

    button.on_clicked(toggle_play)

    # Update function for the slider and frame displays
    def update_frame(index):
        for idx, frame_display in enumerate(frame_displays):
            # Repeat last frame for static images or when the index is larger than stream length
            if index < len(video_frames[idx]):
                frame = video_frames[idx][index]
            else:
                frame = video_frames[idx][-1]  # Keep showing last frame for shorter streams
            frame_display.set_data(frame)
        fig.canvas.draw_idle()

    # Slider update callback
    def on_slider_change(val):
        index = int(slider.val)
        update_frame(index)

    # Connect the slider update function
    slider.on_changed(on_slider_change)

    # Animation function
    def animate(i):
        if playing[0]:
            current_frame = int(slider.val)
            next_frame = (current_frame + 1) % num_frames
            slider.set_val(next_frame) # This will also trigger on_slider_change

    # Use FuncAnimation to update the figure at the specified FPS
    ani = animation.FuncAnimation(fig, animate, frames=num_frames, interval=1000//fps, blit=False)

    plt.show()

def plot_frames_side_by_side(
        fig: plt.Figure,
        frames: list[np.ndarray],
        titles: str =None
        ) -> None:
    """
    Plot a list of frames side by side using matplotlib.
    """
    num_frames = len(frames)
    plt.clf()  # Clear current figure

    for i, frame in enumerate(frames):
        plt.subplot(1, num_frames, i + 1)
        plt.imshow(frame, cmap='gray')
        if titles:
            plt.title(titles[i])
        
        plt.axis('off')  # Turn off axis labels

    plt.tight_layout()
    fig.canvas.draw()

class VideoReader:
    """
    A class to read video files.
    """
    def __init__(self, video_path: str):
        """
        Initialize the VideoReader object.
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(str(video_path))

        if not self.cap.isOpened():
            raise ValueError(f"Could not open video at {video_path}")
        
        logger.info(f"Opened video at {video_path}")
    
    def read_frames(self) -> Iterator[np.ndarray]:
        """
        Read frames from the video file.
        """
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            logger.debug(f"Reading frame {self.cap.get(cv2.CAP_PROP_POS_FRAMES)}")
            if not ret:
                break
            yield frame
    
    def release(self)-> None:
        """
        Release the video capture object.
        """
        self.cap.release()

    def __del__(self):
        self.release()

def show_frame(frame: np.ndarray) -> None:
    """
    Display a single frame using OpenCV.
    """
    cv2.imshow('Mask', frame * 255)
    while True:
        if cv2.waitKey(1) == 27:  # Press 'Esc' key to exit visualization
            break

    cv2.destroyAllWindows()

def gen_freq_mask(
        width: int = 200,
        height: int = 200,
        center_radius: int = 5,
        show_mask: bool = True
        ) -> np.ndarray:
    """
    Generate a mask to filter out horizontal and vertical frequencies.
    A central circular region can be removed to allow low frequencies to pass.
    """
    crow, ccol = height // 2, width // 2
    
    # Create an initial mask filled with ones (pass all frequencies)
    mask = np.ones((height, width), np.uint8)
    
    # Define band widths for vertical and horizontal suppression
    vertical_band_width = 2
    horizontal_band_width = 0
    
    # Zero out a vertical stripe at the frequency center
    mask[:, ccol - vertical_band_width:ccol + vertical_band_width] = 0
    
    # Zero out a horizontal stripe at the frequency center
    mask[crow - horizontal_band_width:crow + horizontal_band_width, :] = 0
    
    # Define the radius of the circular region to retain at the center
    radius = center_radius
    y, x = np.ogrid[:height, :width]
    center_mask = (x - ccol) ** 2 + (y - crow) ** 2 <= radius ** 2
    
    # Restore the center circular area to allow low frequencies to pass
    mask[center_mask] = 1

    # Visualize the mask if needed
    if show_mask:
        cv2.imshow('Mask', mask * 255)
        while True:
            if cv2.waitKey(1) == 27:  # Press 'Esc' key to exit visualization
                break
        cv2.destroyAllWindows()
    return mask
    
class FrameProcessor:
    """
    A class to process video frames.
    """
    def __init__(self,
                 height: int,
                 width: int,
                 buffer_size: int=5032,
                 block_size: int=32
                 ):
        """
        Initialize the FrameProcessor object.
        Block size/buffer size will be set by dev config later.

        Parameters:
        height (int): Height of the video frame.
        width (int): Width of the video frame.
        buffer_size (int): Size of the buffer to process.
        block_size (int): Size of the blocks to process. Not used now.

        """
        self.height = height
        self.width = width
        self.buffer_size = buffer_size
        self.buffer_split = 1
    
    def split_by_length(
            self,
            array: np.ndarray,
            segment_length: int
            ) -> list[np.ndarray]:
        """
        Split an array into sub-arrays of a specified length.

        Parameters:
        array (np.ndarray): The array to split.
        segment_length (int): The length of each sub-array.

        Returns:
        list[np.ndarray]: A list of sub-arrays.
        """
        num_segments = len(array) // segment_length

        # Create sub-arrays of the specified segment length
        split_arrays = [
            array[i * segment_length: (i + 1) * segment_length] for i in range(num_segments)
            ]

        # Add the remaining elements as a final shorter segment, if any
        if len(array) % segment_length != 0:
            split_arrays.append(array[num_segments * segment_length:])

        return split_arrays
    
    def patch_noisy_buffer(
            self,
            current_frame: np.ndarray,
            previous_frame: np.ndarray,
            noise_threshold: float
            ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Process the frame, replacing noisy blocks with those from the previous frame.

        Parameters:
        current_frame (np.ndarray): The current frame to process.
        previous_frame (np.ndarray): The previous frame to compare against.
        noise_threshold (float): The threshold for mean error to consider a block noisy.

        Returns:
        Tuple[np.ndarray, np.ndarray]: The processed frame and the noise patch
        """
        serialized_current = current_frame.flatten().astype(np.int16)
        serialized_previous = previous_frame.flatten().astype(np.int16)

        split_current = self.split_by_length(serialized_current, self.buffer_size//5)
        split_previous = self.split_by_length(serialized_previous, self.buffer_size//5)

        split_output = split_current.copy()
        noisy_parts = split_current.copy()

        for i in range(len(split_current)):
            mean_error = abs(split_current[i] - split_previous[i]).mean()
            if mean_error > noise_threshold:
                logger.info(f"Replacing buffer {i} with mean error {mean_error}")
                split_output[i] = split_previous[i]
                noisy_parts[i] = np.ones_like(split_current[i], np.uint8)
            else:
                split_output[i] = split_current[i]
                noisy_parts[i] = np.zeros_like(split_current[i], np.uint8)

        serialized_output = np.concatenate(split_output)[:self.height * self.width]
        noise_output = np.concatenate(noisy_parts)[:self.height * self.width]
            
        # Deserialize processed frame
        processed_frame = serialized_output.reshape(
            self.width,
            self.height)
        noise_patch = noise_output.reshape(
            self.width,
            self.height)

        return np.uint8(processed_frame), np.uint8(noise_patch)
    
    def remove_stripes(
            self,
            img: np.ndarray,
            mask: np.ndarray
            )-> np.ndarray:
        """
        Perform FFT/IFFT to remove horizontal stripes from a single frame.

        Parameters:
        img (np.ndarray): The image to process.
        mask (np.ndarray): The frequency mask to apply.

        Returns:
        np.ndarray: The filtered image
        """
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = np.log(np.abs(fshift) + 1)  # Use log for better visualization

        # Normalize the magnitude spectrum for visualization
        magnitude_spectrum = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX)

        # Apply mask and inverse FFT
        fshift *= mask
        f_ishift = np.fft.ifftshift(fshift)
        img_back = np.fft.ifft2(f_ishift)
        img_back = np.abs(img_back)

        return np.uint8(img_back), np.uint8(magnitude_spectrum)
    
class FrameListProcessor:
    """
    A class to process a list of video frames.
    """
    @staticmethod
    def get_minimum_projection(
            image_list: list[np.ndarray]
            )-> np.ndarray:
        """
        Get the minimum projection of a list of images.

        Parameters:
        image_list (list[np.ndarray]): A list of images to project.

        Returns:
        np.ndarray: The minimum projection of the images.
        """
        stacked_images = np.stack(image_list, axis=0)
        min_projection = np.min(stacked_images, axis=0)
        return min_projection
        
    @staticmethod
    def normalize_video_stack(
        image_list: list[np.ndarray]
    ) -> list[np.ndarray]:
        """
        Normalize a stack of images to 0-255 using max and minimum values throughout the entire stack.
        Return a list of images.

        Parameters:
        image_list (list[np.ndarray]): A list of images to normalize.

        Returns:
        list[np.ndarray]: The normalized images as a list.
        """

        # Stack images along a new axis (axis=0)
        stacked_images = np.stack(image_list, axis=0)

        # Find the global min and max across the entire stack
        global_min = stacked_images.min()
        global_max = stacked_images.max()

        # Normalize each frame using the global min and max
        normalized_images = []
        for i in range(stacked_images.shape[0]):
            normalized_image = cv2.normalize(
                stacked_images[i],
                None,
                0,
                255,
                cv2.NORM_MINMAX,
                dtype=cv2.CV_32F
                )
            # Apply global normalization
            normalized_image = (stacked_images[i] - global_min) / (global_max - global_min) * 255
            normalized_images.append(normalized_image.astype(np.uint8))

        return normalized_images

if __name__ == "__main__":
    """
    For inital debugging.
    Will be removed later.
    """
    video_path = 'output_001_test.avi'
    reader = VideoReader(video_path)
    streaming_plot = False
    slider_plot = True
    freq_masks = []
    gray_frames = []
    processed_frames = []
    freq_domain_frames = []
    noise_patchs = []
    filtered_frames = []
    diff_frames = []

    index = 0

    fig = plt.figure(figsize=(16, 4))

    processor = FrameProcessor(
        height=200,
        width=200,
    )

    freq_mask = gen_freq_mask(
        width=200,
        height=200,
        show_mask=False
        )
    
    try:
        for frame in reader.read_frames():
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            index += 1
            if index > 100:
                break
            logger.debug(f"Processing frame {index}")
            if index == 1:
                previous_frame = gray_frame
            processed_frame, noise_patch = processor.patch_noisy_buffer(
                gray_frame,
                previous_frame,
                noise_threshold=15
                )
            filtered_frame, freq_domain_frame = processor.remove_stripes(
                img=processed_frame,
                mask=freq_mask
                )            
            diff_frame = cv2.absdiff(gray_frame, filtered_frame)
            gray_frames.append(gray_frame)
            processed_frames.append(processed_frame)
            freq_domain_frames.append(freq_domain_frame)
            noise_patchs.append(noise_patch*255)
            filtered_frames.append(filtered_frame)
            diff_frames.append(diff_frame*10)
    finally:
        reader.release()
        plt.close(fig)

        normalized_frames = FrameListProcessor.normalize_video_stack(filtered_frames)
        minimum_projection = FrameListProcessor.get_minimum_projection(normalized_frames)

        subtract_minimum = [(frame - minimum_projection) for frame in normalized_frames]

        subtract_minimum = FrameListProcessor.normalize_video_stack(subtract_minimum)

        if slider_plot:
            video_frames = [
                gray_frames,
                processed_frames,
                diff_frames,
                noise_patchs,
                freq_mask * 255,
                freq_domain_frames,
                filtered_frames,
                normalized_frames,
                minimum_projection,
                subtract_minimum,
            ]
            plot_video_streams_with_controls(
                video_frames,
                titles=[
                    'Original',
                    'Patched',
                    'Diff',
                    'Noisy area',
                    'Freq mask',
                    'Freq domain',
                    'Freq filtered',
                    'Normalized',
                    'Min Proj',
                    'Subtracted',
                ]
            )