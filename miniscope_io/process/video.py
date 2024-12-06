"""
This module contains functions for pre-processing video data.
"""

from typing import Iterator, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np

from miniscope_io import init_logger
from miniscope_io.models.frames import NamedFrame
from miniscope_io.plots.video import VideoPlotter

logger = init_logger("video")


class VideoReader:
    """
    A class to read video files.
    """

    def __init__(self, video_path: str):
        """
        Initialize the VideoReader object.

        Parameters:
        video_path (str): The path to the video file.

        Raises:
        ValueError: If the video file cannot be opened.
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(str(video_path))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        if not self.cap.isOpened():
            raise ValueError(f"Could not open video at {video_path}")

        logger.info(f"Opened video at {video_path}")

    def read_frames(self) -> Iterator[np.ndarray]:
        """
        Read frames from the video file.

        Yields:
        np.ndarray: The next frame in the video.
        """
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            logger.debug(f"Reading frame {self.cap.get(cv2.CAP_PROP_POS_FRAMES)}")
            if not ret:
                break
            yield frame

    def release(self) -> None:
        """
        Release the video capture object.
        """
        self.cap.release()

    def __del__(self):
        self.release()


def gen_freq_mask(
    width: int,
    height: int,
    center_LPF: int,
    vertical_BEF: int,
    horizontal_BEF: int,
    show_mask: bool = False,
) -> np.ndarray:
    """
    Generate a mask to filter out horizontal and vertical frequencies.
    A central circular region can be removed to allow low frequencies to pass.
    """
    crow, ccol = height // 2, width // 2

    # Create an initial mask filled with ones (pass all frequencies)
    mask = np.ones((height, width), np.uint8)

    # Zero out a vertical stripe at the frequency center
    mask[:, ccol - vertical_BEF : ccol + vertical_BEF] = 0

    # Zero out a horizontal stripe at the frequency center
    mask[crow - horizontal_BEF : crow + horizontal_BEF, :] = 0

    # Define spacial low pass filter
    y, x = np.ogrid[:height, :width]
    center_mask = (x - ccol) ** 2 + (y - crow) ** 2 <= center_LPF**2

    # Restore the center circular area to allow low frequencies to pass
    mask[center_mask] = 1

    # Visualize the mask if needed. Might delete later.
    if show_mask:
        cv2.imshow("Mask", mask * np.iinfo(np.uint8).max)
        while True:
            if cv2.waitKey(1) == 27:  # Press 'Esc' key to exit visualization
                break
        cv2.destroyAllWindows()
    return mask


class FrameProcessor:
    """
    A class to process video frames.
    """

    def __init__(self, height: int, width: int, buffer_size: int = 5032, buffer_split: int = 1):
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
        self.buffer_split = buffer_split

    def split_by_length(self, array: np.ndarray, segment_length: int) -> list[np.ndarray]:
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
            array[i * segment_length : (i + 1) * segment_length] for i in range(num_segments)
        ]

        # Add the remaining elements as a final shorter segment, if any
        if len(array) % segment_length != 0:
            split_arrays.append(array[num_segments * segment_length :])

        return split_arrays

    def patch_noisy_buffer(
        self, current_frame: np.ndarray, previous_frame: np.ndarray, noise_threshold: float
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

        split_current = self.split_by_length(
            serialized_current, self.buffer_size // self.buffer_split
        )
        split_previous = self.split_by_length(
            serialized_previous, self.buffer_size // self.buffer_split
        )

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

        serialized_output = np.concatenate(split_output)[: self.height * self.width]
        noise_output = np.concatenate(noisy_parts)[: self.height * self.width]

        # Deserialize processed frame
        processed_frame = serialized_output.reshape(self.width, self.height)
        noise_patch = noise_output.reshape(self.width, self.height)

        return np.uint8(processed_frame), np.uint8(noise_patch)

    def remove_stripes(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
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
        magnitude_spectrum = cv2.normalize(
            magnitude_spectrum, None, 0, np.iinfo(np.uint8).max, cv2.NORM_MINMAX
        )

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
    def get_minimum_projection(image_list: list[np.ndarray]) -> np.ndarray:
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
    def normalize_video_stack(image_list: list[np.ndarray]) -> list[np.ndarray]:
        """
        Normalize a stack of images to 0-255 using max and minimum values of the entire stack.
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
                np.iinfo(np.uint8).max,
                cv2.NORM_MINMAX,
                dtype=cv2.CV_32F,
            )
            # Apply global normalization
            normalized_image = (
                (stacked_images[i] - global_min)
                / (global_max - global_min)
                * np.iinfo(np.uint8).max
            )
            normalized_images.append(normalized_image.astype(np.uint8))

        return normalized_images


class VideoProcessor:
    """
    A class to process video files.
    """

    def denoise(
        video_path: str,
        slider_plot: bool = True,
        end_frame: int = 100,
        noise_threshold: float = 20,
        spatial_LPF: int = 10,
        vertical_BEF: int = 2,
        horizontal_BEF: int = 0,
        diff_mag: int = 10,
        buffer_split: int = 1,
    ) -> None:
        """
        Process a video file and display the results.
        Might be useful to define some using environment variables.
        """
        reader = VideoReader(video_path)
        raw_frames = []
        patched_frames = []
        freq_domain_frames = []
        noise_patchs = []
        freq_filtered_frames = []
        diff_frames = []

        index = 0
        fig = plt.figure()

        processor = FrameProcessor(
            height=reader.height,
            width=reader.width,
            buffer_split=buffer_split,
        )

        freq_mask = gen_freq_mask(
            width=reader.width,
            height=reader.width,
            center_LPF=spatial_LPF,
            vertical_BEF=vertical_BEF,
            horizontal_BEF=horizontal_BEF,
            show_mask=False,
        )

        try:
            for frame in reader.read_frames():
                raw_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if index > end_frame:
                    break

                logger.debug(f"Processing frame {index}")

                if index == 0:
                    previous_frame = raw_frame

                patched_frame, noise_patch = processor.patch_noisy_buffer(
                    raw_frame, previous_frame, noise_threshold=noise_threshold
                )
                freq_filtered_frame, frame_freq_domain = processor.remove_stripes(
                    img=patched_frame, mask=freq_mask
                )
                diff_frame = cv2.absdiff(raw_frame, freq_filtered_frame)

                raw_frames.append(raw_frame)
                patched_frames.append(patched_frame)
                freq_domain_frames.append(frame_freq_domain)
                noise_patchs.append(noise_patch * np.iinfo(np.uint8).max)
                freq_filtered_frames.append(freq_filtered_frame)
                diff_frames.append(diff_frame * diff_mag)

                index += 1
        finally:
            reader.release()
            plt.close(fig)

            normalized_frames = FrameListProcessor.normalize_video_stack(freq_filtered_frames)
            minimum_projection = FrameListProcessor.get_minimum_projection(normalized_frames)

            subtract_minimum = [(frame - minimum_projection) for frame in normalized_frames]

            subtract_minimum = FrameListProcessor.normalize_video_stack(subtract_minimum)

            raw_video = NamedFrame(name="RAW", video_frame=raw_frames)
            patched_video = NamedFrame(name="Patched", video_frame=patched_frames)
            diff_video = NamedFrame(name=f"Diff {diff_mag}x", video_frame=diff_frames)
            noise_patch = NamedFrame(name="Noisy area", video_frame=noise_patchs)
            freq_mask_frame = NamedFrame(
                name="Freq mask", static_frame=freq_mask * np.iinfo(np.uint8).max
            )
            freq_domain_video = NamedFrame(name="Freq domain", video_frame=freq_domain_frames)
            freq_filtered_video = NamedFrame(name="Freq filtered", video_frame=freq_filtered_frames)
            normalized_video = NamedFrame(name="Normalized", video_frame=normalized_frames)
            min_proj_frame = NamedFrame(name="Min Proj", static_frame=minimum_projection)
            subtract_video = NamedFrame(name="Subtracted", video_frame=subtract_minimum)

            if slider_plot:
                videos = [
                    raw_video,
                    patched_video,
                    diff_video,
                    noise_patch,
                    freq_mask_frame,
                    freq_domain_video,
                    freq_filtered_video,
                    normalized_video,
                    min_proj_frame,
                    subtract_video,
                ]
                VideoPlotter.show_video_with_controls(
                    videos,
                )
