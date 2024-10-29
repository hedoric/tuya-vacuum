"""Script to parse data from a vacuum map."""

import logging

from tuya_vacuum.vacuum_map import VacuumMap


logging.basicConfig(level=logging.DEBUG)


def main():
    """Parse data from a vacuum map."""

    with open("path.bin", "rb") as path_file:
        with open("layout.bin", "rb") as layout_file:
            # Read each file as a hex string
            layout_data = layout_file.read().hex()
            path_data = path_file.read().hex()

            vacuum_map = VacuumMap(layout_data, path_data)
            map_image = vacuum_map.to_image()
            map_image = VacuumMap.crop_image(
                map_image,
                410,
                250,
                vacuum_map.layout.origin_x,
                vacuum_map.layout.origin_y,
                offset_x=50,
                offset_y=60,
            )

            map_image.save("combined.png")


if __name__ == "__main__":
    main()
