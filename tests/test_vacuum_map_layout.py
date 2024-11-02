"""Test the vacuum_map module."""

from tuya_vacuum.vacuum_map_layout import VacuumMapLayout



def test_vacuum_map_header():
    """Test how the vacuum map header is parsed."""

    with open("./tests/layout.bin", "rb") as file:
        # Read the file as a hex string
        data = file.read().hex()

        # Parse the map data
        vacuum_map = VacuumMapLayout(data)

        # Assert that the header values are correct
        assert vacuum_map.version == 1
        assert vacuum_map.id == 0
        assert vacuum_map.type == 0
        assert vacuum_map.total_count == 361391
        assert vacuum_map.width == 601
        assert vacuum_map.height == 601
        assert vacuum_map.origin_x == 300.0
        assert vacuum_map.origin_y == 300.0
        assert vacuum_map.map_resolution == 0
        assert vacuum_map.pile_x == 302.0
        assert vacuum_map.pile_y == 300.0
        assert vacuum_map.length_after_compression == 27666
        assert not vacuum_map.room_editable


def test_vacuum_map_room():
    """Test how a vacuum map room is parsed."""

    with open("./tests/layout.bin", "rb") as file:
        # Read the file as a hex string
        data = file.read().hex()

        # Parse the map data
        vacuum_map = VacuumMapLayout(data)

        # Assert that the room values are correct
        assert vacuum_map.rooms[0].id == 5
        assert vacuum_map.rooms[0].order == 65535
        assert vacuum_map.rooms[0].sweep_count == 1
        assert vacuum_map.rooms[0].mop_count == 2
        assert vacuum_map.rooms[0].color_order == 0
        assert vacuum_map.rooms[0].sweep_forbidden == 0
        assert vacuum_map.rooms[0].mop_forbidden == 0
        assert vacuum_map.rooms[0].fan == 2
        assert vacuum_map.rooms[0].water_level == 3
        assert vacuum_map.rooms[0].y_mode == 1
        assert vacuum_map.rooms[0].name_length == 0
        assert vacuum_map.rooms[0].name == ""
        assert vacuum_map.rooms[0].vertex_num == 0
        assert vacuum_map.rooms[0].vertex_str == ""
