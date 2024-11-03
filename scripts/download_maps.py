"""Script to download the current realtime map from a vacuum using the Tuya Cloud API."""

import os

from dotenv import load_dotenv

import tuya_vacuum

# Load environment variables
load_dotenv()

# Get environment variables
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
DEVICE_ID = os.environ["DEVICE_ID"]


def main():
    """Download the current realtime map from a vacuum using the Tuya Cloud API."""

    BASE = "https://openapi.tuyaus.com"
    ENDPOINT = f"/v1.0/users/sweepers/file/{DEVICE_ID}/realtime-map"

    vacuum = tuya_vacuum.TuyaVacuum(
        origin=BASE,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        device_id=DEVICE_ID,
    )

    vacuum_map = vacuumzetch_realtime_map()


if __name__ == "__main__":
    main()
