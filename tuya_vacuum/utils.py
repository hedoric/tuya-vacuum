"""Collection of utility functions for the Tuya vacuum integration."""

from typing import Iterable


def chunks(lst: Iterable, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def hex_to_ints(hex_digits: str) -> list[int]:
    """Convert a hexadecimal string to a list of integers.

    Algorithm:
        1. Split the hex_digits into a list of two-character strings.
        2. Convert each two-character string from hex to an integer.
        3. Return the list of integers.

    Example:
        hex_digits = "4a6f686e"
        - "4a" -> 74
        - "6f" -> 111
        - "68" -> 104
        - "6e" -> 110
        Output: [74, 111, 104, 110]
    """
    return [int(hex_digits[i : i + 2], 16) for i in range(0, len(hex_digits), 2)]


def combine_high_low_to_int(high: int, low: int) -> int:
    """Combine two bytes into a single integer.

    This function combines two bytes (high and low) into a single integer.
    It does this by shifting the high byte 8 bits to the left and then adding the low byte.

    Example:
        high = `0x12` (18 in decimal)
        low = `0x34` (52 in decimal)
        1. Shift 'high' 8 bits to the left.
            `0x12 << 8 = 0x1200 (4608 in decimal)`
        2. Add 'low' to the result of the shift operation.
            `0x1200 + 0x34 = 0x1234 (4660 in decimal)`

    Usage:
        This function is useful when dealing with data that is split into high and low bytes.
        For example, when parsing binary data formats.
    """
    return low + (high << 8)


def scale_number(scale: float, value: float) -> float:
    """Scales the given number by dividing it and rounding it to the specified scale.

    Args:
        scale (float): The scale to which the number should be divided and rounded.
        value (float): The number to be scaled.

    Returns:
        out (float): The scaled and rounded number.
    """
    return round(value / 10**scale, scale)


def shrink_number(value: float) -> float:
    """Scales the given number by a factor of 1.

    Args:
        value (float): The number to be scaled.

    Returns:
        out (float): The scaled number.
    """
    return scale_number(1, value)


def deal_pl(point: float) -> float:
    """Normalize the given point to be within the range of a signed byte (-32768 to 32767).

    According to Google Translate:
        Compatible with negative numbers.
        The maximum value of byte is equally divided between the positive and negative ends.

    Returns:
        out (float): The normalized point.
    """
    # max_value = 16^4 min_value = max_value/2
    return point - 65536 if point > 32768 else point


def create_format_path(reverse_y: bool, hide_path: bool):
    """Create a function that formats a path point.

    Args:
        reverse_y (bool): Whether to reverse the y-axis.
        hide_path (bool): Whether to hide the path? (not sure).

    Returns:
        format_path (callable): A function that formats a path point.
    """

    def format_path(x: float, y: float) -> dict[float]:
        """Format the given path point.

        Args:
            x (float): The x-coordinate of the point.
            y (float): The y-coordinate of the point.

        Returns:
            real_point (list[float]): The formatted point.
        """

        # Check if the x and y coordinates are numbers.
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError(f"path point x or y is not number: x = {x}, y = {y}")

        if reverse_y:
            real_point = {
                "x": shrink_number(x),
                "y": -shrink_number(y),
            }
        else:
            real_point = {
                "x": shrink_number(x),
                "y": shrink_number(y),
            }

        if not hide_path:
            return real_point

        # This part is not implemented yet, so just return the real_point

        return real_point

    return format_path
