"""The Path class."""

import logging

from PIL import Image, ImageDraw

from tuya_vacuum.lz4 import uncompress
from tuya_vacuum.utils import (
    chunks,
    combine_high_low_to_int,
    create_format_path,
    deal_pl,
    hex_to_ints,
)

# The length of the path header in bytes
PATH_HEADER_LENGTH = 26

# Multiplier to increase the size of the path
PATH_SCALE = 8

# Path
PATH_WIDTH = 8
PATH_COLOR = "white"

# Vacuum Position Marker
PATH_VACUUM_MARKER_RADIUS = 16
PATH_VACUUM_MARKER_COLOR = "blue"
PATH_VACUUM_MARKER_OUTLINE_RADIUS = 20
PATH_VACUUM_MARKER_OUTLINE_COLOR = "white"

# Vacuum Charger Marker
PATH_CHARGER_MARKER_RADIUS = 16
PATH_CHARGER_MARKER_COLOR = "green"
PATH_CHARGER_MARKER_OUTLINE_RADIUS = 20
PATH_CHARGER_MARKER_OUTLINE_COLOR = "white"

_LOGGER = logging.getLogger(__name__)


class Path:
    """The navigation path of a vacuum cleaner."""

    def __init__(self, data: bytes) -> None:
        """Parse the data of a vacuum path.

        @param data: Raw bytes of the vacuum path.
        """
        _LOGGER.debug("Parsing path")

        self.raw = data

        # Convert bytes to hex
        hex_data = data.hex()

        # Parse the header of the path
        self._parse_header(hex_data[: PATH_HEADER_LENGTH * 2])

        # Parse the body of the path
        self._parse_body(hex_data)

        _LOGGER.debug("Finished parsing path")

    def _parse_header(self, data: str) -> None:
        """Parse the header of the vacuum path.

        @param data: Hexidecimal string of the path header.
        """
        data_array = hex_to_ints(data)
        self.version = data_array[0]
        self.force_update = data_array[3]
        self.type = data_array[4]

        # This might be missing proper formatDataHeaderException handling
        self.id = [
            combine_high_low_to_int(integer[0], integer[1])
            for integer in chunks(data_array[1:3], 2)
        ][0]

        self.total_count = int(data[10:18], 16)

        # This might be missing proper formatDataHeaderException handling
        [self.theta, self.length_after_compression] = [
            combine_high_low_to_int(integer[0], integer[1])
            for integer in chunks(data_array[9:13], 2)
        ]

    def _parse_body(self, data: str) -> None:
        """Parse the body of the vacuum path.

        @param data: Hexidecimal string of the path body.
        """
        data_array = hex_to_ints(data)

        if self.length_after_compression:
            max_buffer_length = self.total_count * 4
            encoded_data_array = bytes(hex_to_ints(data[PATH_HEADER_LENGTH:]))
            decoded_data_array = uncompress(encoded_data_array)
            path_data_array = chunks(decoded_data_array, 4)
        else:
            # Floor division
            header_length = PATH_HEADER_LENGTH // 2
            path_data_array = chunks(data_array[header_length:], 4)

        # This code is not accurate to what's expected to happen
        path_data = []
        for point in path_data_array:
            [x, y] = [
                deal_pl(combine_high_low_to_int(high, low))
                for high, low in chunks(point, 2)
            ]
            format_path_point = create_format_path(reverse_y=True, hide_path=True)
            real_point = format_path_point(x, y)
            path_data.append(real_point)

        self._path_data = path_data
        self.start_count = len(path_data)
        self.current_count = len(path_data)

    def to_image(
        self, width: int, height: int, origin_point: tuple[int, int]
    ) -> Image.Image:
        """Create an image of the vacuum path.

        Arguments:
            width (int): The width of the image (before scaling).
            height (int): The height of the image (before scaling).
            origin_point ((x, y)): The origin point of the path.
        """

        origin_x = origin_point[0]
        origin_y = origin_point[1]

        coordinates = []
        for point in self._path_data:
            x = (point["x"] + origin_x) * PATH_SCALE
            y = (point["y"] + origin_y) * PATH_SCALE
            coordinates.append(x)
            coordinates.append(y)

        # Create a new image with a transparent background
        image = Image.new(
            mode="RGBA",
            size=(width * PATH_SCALE, height * PATH_SCALE),
            color=(255, 0, 0, 0),
        )

        # Draw the path on the image
        draw = ImageDraw.Draw(image)
        draw.line(coordinates, fill=PATH_COLOR, width=PATH_WIDTH, joint="curve")

        # Draw the charger marker
        draw.circle(
            (origin_x * PATH_SCALE, origin_y * PATH_SCALE),
            PATH_CHARGER_MARKER_OUTLINE_RADIUS,
            fill=PATH_CHARGER_MARKER_OUTLINE_COLOR,
        )
        draw.circle(
            (origin_x * PATH_SCALE, origin_y * PATH_SCALE),
            PATH_CHARGER_MARKER_RADIUS,
            fill=PATH_CHARGER_MARKER_COLOR,
        )

        # Draw the vacuum marker
        if len(coordinates) >= 2:
            draw.circle(
                (coordinates[-2], coordinates[-1]),
                PATH_VACUUM_MARKER_OUTLINE_RADIUS,
                fill=PATH_VACUUM_MARKER_OUTLINE_COLOR,
            )
            draw.circle(
                (coordinates[-2], coordinates[-1]),
                PATH_VACUUM_MARKER_RADIUS,
                fill=PATH_VACUUM_MARKER_COLOR,
            )

        return image
