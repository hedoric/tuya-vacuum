"""Handle the layout of a vacuum map."""

import logging
import re

import numpy as np
from PIL import Image, ImageColor

from tuya_vacuum.const import (
    BITMAP_TYPE_HEX_MAP,
    ORIGIN_MAP_COLOR,
    pixel_types,
)
from tuya_vacuum.utils import (
    chunks,
    combine_high_low_to_int,
    hex_to_ints,
    shrink_number,
)
from tuya_vacuum.vacuum_map_room import VacuumMapRoom

from .lz4 import uncompress

# Length of map header in bytes
MAP_HEADER_LENGTH = 48

_LOGGER = logging.getLogger(__name__)


class VacuumMapLayout:
    """Handle the layout of a vacuum map."""

    def __init__(self, data: str) -> None:
        """Parse the data of a vacuum map.

        @param data: Hexadecimal string of the vacuum map.
        """

        self.raw_data = data

        # Parse the header of the map
        self._parse_header(data[:MAP_HEADER_LENGTH])

        # Invalid map type
        if self.type > 255:
            raise RuntimeError(f"Map layout header type: {self.type} is not valid.")

        # Parse the rest of the map data
        match self.version:
            case 0:
                self._parse_map_version_0(data)

            case 1:
                self._parse_map_version_1(data)

            case 2:
                self._parse_map_version_2(data)

            # Default case
            case _:
                raise NotImplementedError(
                    f"Map layout version {self.version} is not supported."
                )

    def _parse_header(self, data: str) -> None:
        """Parse the header of the vacuum map.

        @param data: The data of the map header.
        """
        # The version of the map (0: compressed, 1: uncompressed)
        self.version = int(data[0:2], 16)

        # Get the id of the map
        [self.id] = [
            combine_high_low_to_int(integer[0], integer[1])
            for integer in chunks(hex_to_ints(data[2:6]), 2)
        ]

        self.type = int(data[6:8], 16)  # The type of the map (0: layout, 1: path)
        self.total_count = int(data[36:44], 16)

        # Parse the rest of the data. Code taken from the Tuya Panel Demo
        [
            _,
            _,
            self.width,
            self.height,
            self.origin_x,
            self.origin_y,
            self.map_resolution,
            self.pile_x,
            self.pile_y,
            _,
            _,
            self.length_after_compression,
        ] = [
            combine_high_low_to_int(integer[0], integer[1])
            for integer in chunks(hex_to_ints(data), 2)
        ]

        self.origin_x = shrink_number(self.origin_x)
        self.origin_y = shrink_number(self.origin_y)
        self.pile_x = shrink_number(self.pile_x)
        self.pile_y = shrink_number(self.pile_y)

        self.room_editable = bool(self.type)

    def to_image(self) -> Image.Image:
        """Convert the map to an image.

        Taken from tuya_cloud_map_extractor.
        """
        pixels = []
        colors = {
            # "bg_color": default_colors.v1.get("bg_color"),
            "bg_color": ImageColor.getcolor("#006ee6", "RGB"),
            # "wall_color": default_colors.v1.get("wall_color"),
            "wall_color": ["50", "50", "50"],
            # "fun_color": default_colors.v1.get("room_color"),
            "fun_color": ["200", "200", "200"],
        }
        # This actually works perfectly, what?
        for room in self.rooms:
            colors["room_color_" + str(room.id)] = ImageColor.getcolor(
                # If the room id is higher then the amount of colors, wrap around
                ORIGIN_MAP_COLOR[room.id % len(ORIGIN_MAP_COLOR)],
                "RGB",
            )

        for height_counter in range(self.height):
            line = []
            for width_counter in range(self.width):
                pixel_type = pixel_types.v1.get(
                    self._map_data_array[width_counter + height_counter * self.width]
                )
                pixel = colors.get(pixel_type)
                if not pixel:
                    print(f"Unknown pixel type: {pixel_type}")
                    pixel = (20, 20, 20)
                line.append(pixel)
            pixels.append(line)
        return Image.fromarray(np.array(pixels, dtype=np.uint8))

    def _parse_map_version_0(self, data: str):
        """Parse the data of a vacuum map with version 0."""
        # "Normal Version" according to google translate
        # raise NotImplementedError("Map version 0 is not yet supported.")
        # If the data is compressed, decompress it
        if self.length_after_compression:
            max_buffer_length = self.total_count * 8
            encoded_data_array = bytes(hex_to_ints(data[MAP_HEADER_LENGTH:]))
            decoded_data_array = uncompress(encoded_data_array)
            area = self.width * self.height

            map_data_str = "".join(
                "".join(
                    "".join(
                        BITMAP_TYPE_HEX_MAP[x]
                        for x in re.findall(r"\w{2}", format(d, "08b"))
                    )
                )
                for d in decoded_data_array
            )[: area * 2]

            self.rooms = []
            self._map_data_array = bytes.fromhex(map_data_str)
        else:
            raise NotImplementedError("Uncompressed map data is not yet supported.")

    def _parse_map_version_1(self, data: str):
        """Parse the data of a vacuum map with version 1."""
        # "Partition Version" according to google translate

        # If the data is compressed, decompress it
        if self.length_after_compression:
            area = self.width * self.height
            info_length = MAP_HEADER_LENGTH + self.total_count * 2
            encoded_data_array = bytes(hex_to_ints(data[MAP_HEADER_LENGTH:info_length]))
            max_buffer_length = self.total_count * 4
            decoded_data_array = uncompress(encoded_data_array)
            self._map_data_array = decoded_data_array[:area]
            map_room_array = decoded_data_array[area:]

            rooms = VacuumMapRoom.parse_map_room_array(map_room_array.hex())

            for room in rooms:
                _LOGGER.debug(vars(room))

            self.rooms = rooms

        else:
            raise NotImplementedError("Uncompressed map data is not yet supported.")

    def _parse_map_version_2(self, data: str):
        """Parse the data of a vacuum map with version 2."""
        # "Floor Material Version" according to google translate
        raise NotImplementedError("Map version 2 is not yet supported.")
