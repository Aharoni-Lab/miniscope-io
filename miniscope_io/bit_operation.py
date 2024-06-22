from typing import Tuple
import numpy as np

class BufferFormatter:
    """
    A class for formatting buffers and returning header (uint32) and payload (uint8) data.
    """

    @classmethod
    def _reverse_bits_in_byte(cls, byte: int) -> int:
        """
        Reverse the bits in a byte.
        
        Args:
            byte (int): The byte to reverse.
        
        Returns:
            int: The byte with its bits reversed.
        """
        return int(f'{byte:08b}'[::-1], 2)

    @classmethod
    def _reverse_bits_in_32bit_int(cls, x: int) -> int:
        """
        Reverse the bits in each byte of a 32-bit integer.
        
        Args:
            x (int): The 32-bit integer.
        
        Returns:
            int: The 32-bit integer with bits in each byte reversed.
        """
        reversed_bytes = [
            cls._reverse_bits_in_byte((x >> (8 * i)) & 0xFF) 
            for i in range(4)
        ]
        return (
            (reversed_bytes[0] << 24) | 
            (reversed_bytes[1] << 16) | 
            (reversed_bytes[2] << 8) | 
            reversed_bytes[3]
        )

    @classmethod
    def _reverse_byte_order_32bit_int(cls, x: int) -> int:
        """
        Reverse the byte order of a 32-bit integer.
        
        Args:
            x (int): The 32-bit integer.
        
        Returns:
            int: The 32-bit integer with byte order reversed.
        """
        return (
            ((x & 0x000000FF) << 24) | 
            ((x & 0x0000FF00) << 8) | 
            ((x & 0x00FF0000) >> 8) | 
            ((x & 0xFF000000) >> 24)
        )

    @classmethod
    def bytebuffer_to_ndarrays(cls,
                               buffer,
                               header_length_words,
                               preamble_length_words,
                               reverse_header_bits=True,
                               reverse_header_bytes=True,
                               reverse_body_bits=True, 
                               reverse_body_bytes=True
                               ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Format the buffer by optionally reversing bits in the header and body.
        
        Args:
            buffer (bytes): The binary buffer to format.
            header_length_bits (int): Length of the header in bits.
            reverse_header_bits (bool): Reverse bits in the header if True. Default is True.
            reverse_body_bits (bool): Reverse bits in the body if True. Default is True.
            reverse_body_bytes (bool): Reverse byte order in the body if True. Default is True.
        
        Returns:
            tuple: A tuple containing the processed header as a numpy array of uint32 
                   and the processed payload as a numpy array of uint8.
        
        Raises:
            ValueError: If header_length_bits is not a multiple of 32.
        """
        
        # Padding in case the buffer is not a multiple of 4 bytes (32 bits)
        padding_length = (4 - (len(buffer) % 4)) % 4
        padded_buffer = buffer + b'\x00' * padding_length

        # Convert the padded buffer to a uint32 numpy array
        data = np.frombuffer(padded_buffer, dtype=np.uint32)

        # Process header
        header = data[preamble_length_words:header_length_words]
        if reverse_header_bits:
            header = np.array(
                [cls._reverse_bits_in_32bit_int(x) for x in header], 
                dtype=np.uint32
            )
        if reverse_header_bytes:
            header = np.array(
                [cls._reverse_byte_order_32bit_int(x) for x in header], 
                dtype=np.uint32
            )


        # Process body
        payload_data = data[header_length_words:]
        if reverse_body_bits:
            payload_data = np.array(
                [cls._reverse_bits_in_32bit_int(x) for x in payload_data], 
                dtype=np.uint32
            )
        
        if reverse_body_bytes:
            payload_data = np.array(
                [cls._reverse_byte_order_32bit_int(x) for x in payload_data], 
                dtype=np.uint32
            )

        # Convert processed body buffer to uint8 numpy array
        payload_uint8 = payload_data.view(np.uint8)
        return header, payload_uint8