"""
This module contains functions for pre-processing video data.
"""

import copy
from typing import Iterator, Optional

import cv2
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, Field

from miniscope_io import init_logger

logger = init_logger("video")

def serialize_image(image: np.ndarray) -> np.ndarray:
    """
    Serializes a 2D image into a 1D array.
    """
    return image.flatten()

def deserialize_image(
        serialized_image: np.ndarray,
        height: int,
        width: int)-> np.ndarray:
    """
    Deserializes a 1D array back into a 2D image.
    """
    return serialized_image.reshape((height, width))

def detect_noisy_parts(
        current_frame: np.ndarray,
        previous_frame: np.ndarray,
        noise_threshold: float,
        buffer_size: int,
        block_size: int = 32
        ) -> np.ndarray:
    """
    Detect noisy parts in the current frame by comparing it with the previous frame.
    """
    current_frame_serialized = serialize_image(current_frame)
    previous_frame_serialized = serialize_image(previous_frame)



    noisy_parts = np.zeros_like(current_frame_serialized)
    noize_mask = deserialize_image(noisy_parts, current_frame.shape[0], current_frame.shape[1])

def plot_frames_side_by_side(
        fig: plt.Figure,
        frames: list[np.ndarray],
        titles: str =None
        ) -> None:
    """
    Plot a list of frames side by side using matplotlib.

    :param frames: List of frames (images) to be plotted
    :param titles: Optional list of titles for each subplot
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
class AnnotatedFrameModel(BaseModel):
    """
    A class to represent video data.
    """
    data: np.ndarray = Field(
        ...,
        description="The video data as a NumPy array."
    )
    status_tag: Optional[str] = Field(
        None,
        description="A tag indicating the status of the video data."
    )
    index: Optional[int] = Field(
        None,
        description="The index of the video data."
    )
    fps: Optional[float] = Field(
        None,
        description="The frames per second of the video."
    )

    # Might be a numpydantic situation? Need to look later but will skip.
    class Config:
        arbitrary_types_allowed = True
class AnnotatedFrameListModel(BaseModel):
    """
    A class to represent a list of annotated video frames.
    Not used yet
    """
    frames: list[AnnotatedFrameModel] = Field(
        ...,
        description="A list of annotated video frames."
    )
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

def gen_freq_mask(
        width: int = 200,
        height: int = 200,
        center_radius: int = 6,
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
        """
        self.height = height
        self.width = width
        self.buffer_size = buffer_size
        self.block_size = block_size
    
    def split_by_length(
            self,
            array: np.ndarray,
            segment_length: int
            ) -> list[np.ndarray]:
        """
        Split an array into sub-arrays of a specified length.
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
            ) -> np.ndarray:
        """
        Process the frame, replacing noisy blocks with those from the previous frame.
        """

        serialized_current = current_frame.flatten()
        serialized_previous = previous_frame.flatten()

        split_current = self.split_by_length(serialized_current, self.buffer_size)
        split_previous = self.split_by_length(serialized_previous, self.buffer_size)

        # Not best to deepcopy this. Just doing for now to take care of
        # inhomogeneous array sizes.
        split_output = copy.deepcopy(split_current)
        noisy_parts = copy.deepcopy(split_current)

        for i in range(len(split_current)):
            mean_error = abs(split_current[i] - split_previous[i]).mean()
            if mean_error > noise_threshold:
                logger.debug(f"Replacing buffer {i} with mean error {mean_error}")
                split_output[i] = split_previous[i]
                noisy_parts[i] = np.ones_like(split_current[i]) * 255
            else:
                split_output[i] = split_current[i]
                noisy_parts[i] = np.zeros_like(split_current[i])

        serialized_output = np.concatenate(split_output)[:self.height * self.width]
        noise_output = np.concatenate(noisy_parts)[:self.height * self.width]
            
        # Deserialize processed frame
        processed_frame = serialized_output.reshape(
            self.width,
            self.height)
        noise_patch = noise_output.reshape(
            self.width,
            self.height)

        return processed_frame, noise_patch
    
    def remove_stripes(
            self,
            img: np.ndarray,
            mask: np.ndarray
            )-> np.ndarray:
        """Perform FFT/IFFT to remove horizontal stripes from a single frame."""
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = np.log(np.abs(fshift) + 1)  # Use log for better visualization

        # Normalize the magnitude spectrum for visualization
        magnitude_spectrum = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX)

        if False:
            # Display the magnitude spectrum
            cv2.imshow('Magnitude Spectrum', np.uint8(magnitude_spectrum))
            while True:
                if cv2.waitKey(1) == 27:  # Press 'Esc' key to exit visualization
                    break
            cv2.destroyAllWindows()
        logger.debug(f"FFT shape: {fshift.shape}")

        # Apply mask and inverse FFT
        fshift *= mask
        f_ishift = np.fft.ifftshift(fshift)
        img_back = np.fft.ifft2(f_ishift)
        img_back = np.abs(img_back)

        # Normalize the result:
        img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX)

        return np.uint8(img_back)  # Convert to 8-bit image for display and storage 

if __name__ == "__main__":
    """
    For inital debugging.
    Will be removed later.
    """
    video_path = 'output_001_test.avi'
    reader = VideoReader(video_path)

    frames = []
    index = 0
    fig = plt.figure(figsize=(12, 4))

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
            logger.info(f"Processing frame {index}")
            if index == 1:
                previous_frame = gray_frame
            processed_frame, noise_patch = processor.patch_noisy_buffer(
                gray_frame,
                previous_frame,
                noise_threshold=250
                )
            filtered_frame = processor.remove_stripes(
                img=processed_frame,
                mask=freq_mask
                )
            frames.append(filtered_frame)

            frames_to_plot = [
                freq_mask,
                gray_frame,
                processed_frame,
                noise_patch,
                filtered_frame,
                ]
            plot_frames_side_by_side(
                fig,
                frames_to_plot,
                titles=[
                    'Frequency Mask',
                    'Original Frame',
                    'Processed Frame',
                    'Noisy Patch',
                    'Filtered Frame',
                    ]
                )
            plt.pause(0.01)

    finally:
        reader.release()
        plt.close(fig)