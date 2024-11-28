"""Download, parse, and save the current real-time vacuum map."""

import logging
import os

from dotenv import load_dotenv

from tuya_vacuum.map.layout import Layout
from tuya_vacuum.map.map import Map
from tuya_vacuum.map.path import Path
from tuya_vacuum.vacuum import Vacuum

logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Get environment variables
ORIGIN = os.environ["ORIGIN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
DEVICE_ID = os.environ["DEVICE_ID"]


def main():
    """Download, parse, and save the current real-time vacuum map."""
    vacuum = Vacuum(ORIGIN, CLIENT_ID, CLIENT_SECRET, DEVICE_ID)

    vacuum_map_data = vacuum.fetch_realtime_map_data()
    if (
        vacuum_map_data
        and vacuum_map_data["layout_data"]
        and vacuum_map_data["path_data"]
    ):
        layout_map = Layout(vacuum_map_data["layout_data"])
        path_map = Path(vacuum_map_data["path_data"])
        map = Map(layout_map, path_map)
        image = map.to_image()
        image.save("map.png")
    else:
        print("Err, what the hell")


if __name__ == "__main__":
    main()
