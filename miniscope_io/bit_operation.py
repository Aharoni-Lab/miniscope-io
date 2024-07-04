"""
Bit operations for parsing header and payload information. Currently for use in streamDaq module
"""

from typing import Tuple

import numpy as np


class BufferFormatter:
    """
    A class for formatting buffers and returning header (uint32) and payload (uint8) data.
    """

    @staticmethod
    def _reverse_bits_in_array(arr: np.ndarray) -> np.ndarray:
        """
        Reverse the bits in each element of a numpy array.

        Args:
            arr (np.ndarray): The input array.

        Returns:
            np.ndarray: The array with bits in each element reversed.
        """
        arr = np.unpackbits(arr.view(np.uint8)).reshape(-1, 32)[:, ::-1]
        return np.packbits(arr).view(np.uint32)

    @staticmethod
    def _reverse_byte_order_in_array(arr: np.ndarray) -> np.ndarray:
        """
        Reverse the byte order of each element in a numpy array.

        Args:
            arr (np.ndarray): The input array.

        Returns:
            np.ndarray: The array with byte order in each element reversed.
        """
        return arr.byteswap()

    @classmethod
    def bytebuffer_to_ndarrays(
        cls,
        buffer: bytes,
        header_length_words: int,
        preamble_length_words: int,
        reverse_header_bits: bool,
        reverse_header_bytes: bool,
        reverse_payload_bits: bool,
        reverse_payload_bytes: bool,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Format the buffer by optionally reversing bits in the header and body.

        Args:
            buffer (bytes): The binary buffer to format.
            header_length_words (int): Length of the header in words.
            preamble_length_words (int): Length of the preamble in words.
            reverse_header_bits (bool): Reverse bits in the header if True. Default is True.
            reverse_header_bytes (bool): Reverse byte order in the header if True. Default is True.
            reverse_payload_bits (bool): Reverse bits in the body if True. Default is True.
            reverse_payload_bytes (bool): Reverse byte order in the body if True. Default is True.

        Returns:
            tuple: A tuple containing the processed header as a numpy array of uint32
                   and the processed payload as a numpy array of uint8.
        """

        # Padding in case the buffer is not a multiple of 4 bytes (32 bits)
        padding_length = (4 - (len(buffer) % 4)) % 4
        padded_buffer = buffer + b"\x00" * padding_length

        # Convert the padded buffer to a uint32 numpy array
        data = np.frombuffer(padded_buffer, dtype=np.uint32)

        # Process header
        header = data[preamble_length_words:header_length_words]
        if reverse_header_bits:
            header = cls._reverse_bits_in_array(header)
        if reverse_header_bytes:
            header = cls._reverse_byte_order_in_array(header)

        # Process body
        payload_data = data[header_length_words:]
        if reverse_payload_bits:
            payload_data = cls._reverse_bits_in_array(payload_data)
        if reverse_payload_bytes:
            payload_data = cls._reverse_byte_order_in_array(payload_data)

        # Convert processed body buffer to uint8 numpy array
        payload_uint8 = payload_data.view(np.uint8)
        return header, payload_uint8
