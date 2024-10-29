"""Functional test for communication with the Tuya Cloud API."""

import logging
import os

from dotenv import load_dotenv

from tuya_vacuum.tuya import TuyaCloudAPI

_LOGGER = logging.getLogger(__name__)


def test_tuya_request():
    """Functionally test the tuya_request."""

    # Load environment variables
    load_dotenv()

    # Get environment variables
    CLIENT_ID = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
    DEVICE_ID = os.environ["DEVICE_ID"]

    BASE = "https://openapi.tuyaus.com"
    ENDPOINT = f"/v1.0/users/sweepers/file/{DEVICE_ID}/realtime-map"
    tuya = TuyaCloudAPI(origin=BASE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    response = tuya.request("GET", ENDPOINT)
    print(response)
    assert response["success"]
