"""Functional test for communication with the Tuya Cloud API."""

import logging
from uuid import UUID
import httpx
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from freezegun import freeze_time
import pytest

from tuya_vacuum.tuya import CrossRegionAccessError, InvalidClientIDError, InvalidDeviceIDError, TuyaCloudAPI, InvalidClientSecretError

_LOGGER = logging.getLogger(__name__)

CLIENT_ID = "example"
CLIENT_SECRET = "example"
DEVICE_ID = "example"
ORIGIN = "https://openapi.tuyaus.com"
ENDPOINT = f"/v1.0/users/sweepers/file/{DEVICE_ID}/realtime-map"

# Mock the datetime module to a fixed time
@freeze_time("2024-11-02 12:00:01")
def test_get_timestamp():
    """Test TuyaCloudAPI.get_timestamp."""

    assert TuyaCloudAPI.get_timestamp() == "1730548801000"

def test_get_nonce(mocker: MockerFixture):
    """Test TuyaCloudAPI.get_nonce."""

    # Mock the UUID generation
    mocker.patch("uuid.uuid4", return_value=UUID('0e950a25-9a73-4b8e-bae7-86f131450350'))

    assert TuyaCloudAPI.get_nonce() == "0e950a259a734b8ebae786f131450350"

def test_create_signature():
    """Test TuyaCloudAPI.create_signature."""
    tuya = TuyaCloudAPI(origin=ORIGIN, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    method = "GET"
    endpoint = ENDPOINT
    timestamp = "1730548801000"
    nonce = "0e950a259a734b8ebae786f131450350"
    access_token = "example_access_token"

    tuya = TuyaCloudAPI(origin=ORIGIN, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    signature = tuya.create_signature(method, endpoint, timestamp, nonce, access_token)

    assert signature == "7ADE4474E49D93106F236A261C539CFEC7C89801047896F5A3376202B422A8FD"

# Mock the datetime module to a fixed time
@freeze_time("2024-11-02 12:00:01")
def test_request(mocker: MockerFixture, httpx_mock: HTTPXMock):
    """Test TuyaCloudAPI.request."""

    # Mock response for the request to get the access token
    httpx_mock.add_response(
        url = f"{ORIGIN}/v1.0/token?grant_type=1",
        json = {
            "success": True,
            "result": {
                "access_token": "example_access_token",
            }
        }
    )
    # Mock response for the request to get the map URLs
    httpx_mock.add_response(
        url = f"{ORIGIN}{ENDPOINT}",
        json = {
            "success": True,
            "result": [
                {
                    "map_url": "example_layout_map_url",
                    "map_type": 0
                },
                {
                    "map_url": "example_path_map_url",
                    "map_type": 1
                }
            ]
        }
    )

    # Mock the UUID generation
    mocker.patch("uuid.uuid4", return_value=UUID('0e950a25-9a73-4b8e-bae7-86f131450350'))

    with httpx.Client() as client:
        # Create a TuyaCloudAPI instance
        tuya = TuyaCloudAPI(
            origin=ORIGIN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            client=client
        )

        response = tuya.request("GET", ENDPOINT)

        # Check if the returned values are correct
        # Check if the response is successful
        assert response["success"]
        # Check if the layout map URL is correct
        assert response["result"][0]["map_url"] == "example_layout_map_url"
        # Check if the path map URL is correct
        assert response["result"][1]["map_url"] == "example_path_map_url"

        requests = httpx_mock.get_requests()

        # Check if the access token request was successful
        request = requests[0]
        headers = request.headers
        assert request.url == f"{ORIGIN}/v1.0/token?grant_type=1"
        assert headers.get("client_id") == CLIENT_ID
        assert headers.get("sign") == (
            "B557C364FD291EFF020769E5D1D1689C7C9BAF9AFAA7D936CCA26361D01B17DE"
        )
        assert headers.get("sign_method") == "HMAC-SHA256"
        assert headers.get("t") == "1730548801000"
        assert headers.get("lang") == "en"
        assert headers.get("nonce") == "0e950a259a734b8ebae786f131450350"

        # Check if the endpoint request was successful
        request = requests[1]
        headers = request.headers
        assert request.url == f"{ORIGIN}{ENDPOINT}"
        assert headers.get("client_id") == CLIENT_ID
        assert headers.get("sign") == (
            "7ADE4474E49D93106F236A261C539CFEC7C89801047896F5A3376202B422A8FD"
        )
        assert headers.get("sign_method") == "HMAC-SHA256"
        assert headers.get("t") == "1730548801000"
        assert headers.get("lang") == "en"
        assert headers.get("nonce") == "0e950a259a734b8ebae786f131450350"

def test_invalid_request(httpx_mock: HTTPXMock):
    """Test TuyaCloudAPI.request with an invalid request."""

    # Invalid client id request
    httpx_mock.add_response(
        url = f"{ORIGIN}/v1.0/token?grant_type=1",
        match_headers={"client_id": "wrong_client_id"},
        json = {
            "success": False,
            "code": 1005,
        }
    )


    # Invalid origin
    httpx_mock.add_response(
        url = "https://invalid_origin.com/v1.0/token?grant_type=1",
        json = {
            "success": False,
            "code": 2007,
        }
    )

    # Mock response for the request to get the map URLs
    httpx_mock.add_response(
        url = f"{ORIGIN}/invalid_device_id/realtime-map",
        json = {
            "success": False,
            "code": 1106
        }
    )

    with httpx.Client() as client:
        # # Create a TuyaCloudAPI instance
        # tuya = TuyaCloudAPI(
        #     origin=ORIGIN,
        #     client_id=CLIENT_ID,
        #     client_secret="wrong_client_secret",
        #     client=client
        # )

        # with pytest.raises(InvalidClientSecretError):
        #     tuya.request("GET", "/v1.0/token?grant_type=1", fetch_token=False)

        # Create a TuyaCloudAPI instance
        tuya = TuyaCloudAPI(
            origin=ORIGIN,
            client_id="wrong_client_id",
            client_secret=CLIENT_SECRET,
            client=client
        )

        with pytest.raises(InvalidClientIDError):
            tuya.request("GET", "/v1.0/token?grant_type=1", fetch_token=False)

        # Create a TuyaCloudAPI instance
        tuya = TuyaCloudAPI(
            origin="https://invalid_origin.com",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            client=client
        )

        with pytest.raises(CrossRegionAccessError):
            tuya.request("GET", "/v1.0/token?grant_type=1", fetch_token=False)

        # Create a TuyaCloudAPI instance
        tuya = TuyaCloudAPI(
            origin=ORIGIN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            client=client
        )

        with pytest.raises(InvalidDeviceIDError):
            tuya.request("GET", "/invalid_device_id/realtime-map", fetch_token=False)
