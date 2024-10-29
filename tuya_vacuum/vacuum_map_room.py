"""Handle rooms in a vacuum map."""

# Large parts of this script are based on the following code:
# https://github.com/tuya/tuya-panel-demo/blob/main/examples/laserSweepRobot/src/protocol/map/index.ts

import logging

from tuya_vacuum.utils import (
    chunks,
    combine_high_low_to_int,
    hex_to_ints,
)

# Max id number
MAX_ID = 255

INFO_BYTE_LEN = 26  # "Room properties"
NAME_BYTE_LEN = 20  # "Vertices_name"

_LOGGER = logging.getLogger(__name__)


class VacuumMapRoom:
    """Handle the data of a room in the vacuum map."""

    def __init__(self, data: str, byte_pos: int) -> None:
        """Parse the data of a room in the vacuum map.

        @param data: The `map_room_array`.
        @param byte_pos: The byte position of the room in the `map_room_array`.
        """

        # "room information" according to google translate
        room_info_str = data[
            byte_pos : (byte_pos + (INFO_BYTE_LEN + NAME_BYTE_LEN + 1) * 2)
        ]

        [self.id, self.order, self.sweep_count, self.mop_count] = [
            combine_high_low_to_int(integer[0], integer[1])
            for integer in chunks(hex_to_ints(room_info_str[:16]), 2)
        ]

        [
            self.color_order,
            self.sweep_forbidden,
            self.mop_forbidden,
            self.fan,
            self.water_level,
            self.y_mode,
        ] = hex_to_ints(room_info_str[16:28])

        self.name_length = int(room_info_str[52:54], 16)
        vertices_name_str = room_info_str[
            (INFO_BYTE_LEN * 2 + 1 * 2) : (
                INFO_BYTE_LEN * 2 + 1 * 2 + self.name_length * 2
            )
        ]

        self.name = bytes.fromhex(vertices_name_str).decode()

        self.vertex_num = int(room_info_str[-2:], 16)
        self.vertex_str = data[
            (byte_pos + (INFO_BYTE_LEN + NAME_BYTE_LEN + 1) * 2) : (
                byte_pos
                + (INFO_BYTE_LEN + NAME_BYTE_LEN + 1) * 2
                + self.vertex_num * 2 * 2 * 2
            )
        ]

    @staticmethod
    def parse_map_room_array(data: str) -> list["VacuumMapRoom"]:
        """Parse the map room array.

        @param data: The `map_room_array`.
        """

        rooms = []
        room_count = int(data[2:4], 16)

        byte_pos = 2 * 2  # "region_num"

        for _ in range(room_count):
            rooms.append(VacuumMapRoom(data, byte_pos))
            byte_pos = byte_pos + (INFO_BYTE_LEN + NAME_BYTE_LEN + 1) * 2

        return rooms
