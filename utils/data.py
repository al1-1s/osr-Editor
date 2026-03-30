"""Utility functions for encoding and decoding various data types."""

class uleb128:
    @staticmethod
    def encode(value: int) -> bytes:
        """Encode an unsigned integer using ULEB128 encoding.
        
        Args:
            value (int): A non-negative integer to encode.
        
        Returns:
            result (bytes): A bytes object containing the ULEB128-encoded value.
        """
        if value < 0:
            raise ValueError("Value must be a non-negative integer.")
        
        result = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            if value != 0:
                byte |= 0x80
            result.append(byte)
            if value == 0:
                break
        return bytes(result)

    @staticmethod
    def decode(data: bytes) -> tuple[int, bool, int]:
        """Decode a ULEB128-encoded byte sequence into an unsigned integer.
        
        Args:
            data (bytes): A bytes object containing the ULEB128-encoded value.
        
        Returns:
            (result, end, length) (tuple[int, bool, int]): A tuple of the decoded integer, a boolean indicating whether the end of the sequence was reached, and the number of bytes consumed.
        """
        end = False
        result = 0
        shift = 0
        length = 0
        for byte in data:
            length += 1

            result |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                end = True
                break
            shift += 7
        return result, end, length

class strings:
    @staticmethod
    def encode(value: str) -> bytes:
        """Encode a string using ULEB128 encoding for its length followed by UTF-8 bytes.
        
        Args:
            value (str): The string to encode.
        Returns:
            result (bytes): A bytes object containing the ULEB128-encoded length followed by the UTF-8 encoded string.
        """
        encoded_length = uleb128.encode(len(value))
        indicator = b'\x0b'  # Indicator byte for string type
        return indicator + encoded_length + value.encode('utf-8')

    @staticmethod
    def decode(data: bytes) -> tuple[str, int]:
        """Decode a ULEB128-encoded string from a byte sequence.
        
        Args:
            data (bytes): A bytes object containing the ULEB128-encoded length followed by the UTF-8 encoded string.
        
        Returns:
            (result, length) (tuple[str, int]): A tuple of the decoded string and the total number of bytes consumed from the input data.
            length is -1 if there was an error in decoding.
        """
        if not data:
            return "", 0

        indicator = data[0]
        if indicator != 11:
            return "", 1  # Invalid indicator, return empty string and 1 byte consumed

        # Decode the length of the string
        length, end, length_size = uleb128.decode(data[1:])
        if not end:
            return "", -1  # Invalid ULEB128 encoding, return empty string and -1 to indicate error
        string_data = data[1 + length_size:1 + length_size + length]
        return string_data.decode('utf-8'), 1 + length_size + length
    
class shorts:
    @staticmethod
    def encode(value: int) -> bytes:
        """Encode a short integer (16-bit) in little-endian format.
        
        Args:
            value (int): The short integer to encode.
        
        Returns:
            result (bytes): A bytes object containing the encoded short integer.
        """
        return value.to_bytes(2, byteorder='little', signed=True)

    @staticmethod
    def decode(data: bytes) -> tuple[int, int]:
        """Decode a short integer (16-bit) from a byte sequence in little-endian format.
        
        Args:
            data (bytes): A bytes object containing the encoded short integer.
        
        Returns:
            (result, length) (tuple[int, int]): A tuple of the decoded short integer and the number of bytes consumed.
        """
        if len(data) < 2:
            raise ValueError("Insufficient data for short integer decoding.")
        return int.from_bytes(data[:2], byteorder='little', signed=True), 2

class ints:
    @staticmethod
    def encode(value: int) -> bytes:
        """Encode an integer (32-bit) in little-endian format.
        
        Args:
            value (int): The integer to encode.
        
        Returns:
            result (bytes): A bytes object containing the encoded integer.
        """
        return value.to_bytes(4, byteorder='little', signed=True)

    @staticmethod
    def decode(data: bytes) -> tuple[int, int]:
        """Decode an integer (32-bit) from a byte sequence in little-endian format.
        
        Args:
            data (bytes): A bytes object containing the encoded integer.
        
        Returns:
            (result, length) (tuple[int, int]): A tuple of the decoded integer and the number of bytes consumed.
        """
        if len(data) < 4:
            raise ValueError("Insufficient data for integer decoding.")
        return int.from_bytes(data[:4], byteorder='little', signed=True), 4

class longs:
    @staticmethod
    def encode(value: int) -> bytes:
        """Encode a long integer (64-bit) in little-endian format.
        
        Args:
            value (int): The long integer to encode.
        
        Returns:
            result (bytes): A bytes object containing the encoded long integer.
        """
        return value.to_bytes(8, byteorder='little', signed=True)

    @staticmethod
    def decode(data: bytes) -> tuple[int, int]:
        """Decode a long integer (64-bit) from a byte sequence in little-endian format.
        
        Args:
            data (bytes): A bytes object containing the encoded long integer.
            
        Returns:
            (result, length) (tuple[int, int]): A tuple of the decoded long integer and the number of bytes consumed.
        """
        if len(data) < 8:
            raise ValueError("Insufficient data for long integer decoding.")
        return int.from_bytes(data[:8], byteorder='little', signed=True), 8

class byte:
    @staticmethod
    def encode(value: int) -> bytes:
        """Encode a single byte.
        
        Args:
            value (int): The byte value to encode (0-255).
        
        Returns:
            result (bytes): A bytes object containing the encoded byte.
        """
        if not (0 <= value <= 255):
            raise ValueError("Value must be in the range 0-255 for a single byte.")
        return bytes([value])

    @staticmethod
    def decode(data: bytes) -> tuple[int, int]:
        """Decode a single byte from a byte sequence.
        
        Args:
            data (bytes): A bytes object containing the encoded byte.
        
        Returns:
            (result, length) (tuple[int, int]): A tuple of the decoded byte value and the number of bytes consumed.
        """
        if len(data) < 1:
            raise ValueError("Insufficient data for byte decoding.")
        return data[0], 1


if __name__ == "__main__":
    original_string = "Hello, World!"
    encoded = strings.encode(original_string)
    print(f"Encoded: {encoded}, Length: {len(encoded)}")

    decoded_string, bytes_consumed = strings.decode(encoded)
    print(f"Decoded: {decoded_string}, Bytes Consumed: {bytes_consumed}")

    # Test short integer encoding and decoding
    original_short = 12345
    encoded_short = shorts.encode(original_short)
    print(f"Encoded short: {encoded_short}")

    decoded_short, bytes_consumed_short = shorts.decode(encoded_short)
    print(f"Decoded short: {decoded_short}, Bytes Consumed: {bytes_consumed_short}")

    # Test integer encoding and decoding
    original_int = 123456789
    encoded_int = ints.encode(original_int)
    print(f"Encoded int: {encoded_int}")

    decoded_int, bytes_consumed_int = ints.decode(encoded_int)
    print(f"Decoded int: {decoded_int}, Bytes Consumed: {bytes_consumed_int}")

    # Test long integer encoding and decoding
    original_long = 1234567890123456789
    encoded_long = longs.encode(original_long)
    print(f"Encoded long: {encoded_long}")

    decoded_long, bytes_consumed_long = longs.decode(encoded_long)
    print(f"Decoded long: {decoded_long}, Bytes Consumed: {bytes_consumed_long}")

    # Test byte encoding and decoding
    original_byte = 255
    encoded_byte = byte.encode(original_byte)
    print(f"Encoded byte: {encoded_byte}")

    decoded_byte, bytes_consumed_byte = byte.decode(encoded_byte)
    print(f"Decoded byte: {decoded_byte}, Bytes Consumed: {bytes_consumed_byte}")