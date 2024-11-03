"""Tests for the TuyaCloudAPI class."""

import logging
import os
from uuid import UUID

import freezegun
import httpx
import pytest
from dotenv import load_dotenv
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tuya_vacuum.tuya import (
    CrossRegionAccessError,
    InvalidClientIDError,
    InvalidClientSecretError,
    InvalidDeviceIDError,
    TuyaCloudAPI,
)

load_dotenv()

_LOGGER = logging.getLogger(__name__)

CORRECT_CLIENT_ID = "correct_client_id"
CORRECT_CLIENT_SECRET = "correct_client_secret"
CORRECT_DEVICE_ID = "correct_device_id"
CORRECT_ORIGIN = (
    "https://correct_origin.com"  # Origin of the correct server for the device
)

WRONG_CLIENT_ID = "wrong_client_id"
WRONG_CLIENT_SECRET = "wrong_client_secret"
WRONG_DEVICE_ID = "wrong_device_id"
WRONG_ORIGIN = "https://invalid_origin.com"  # Origin of the wrong server for the device

EXPECTED_TIMESTAMP = "1730548801000"
EXPECTED_NONCE = "0e950a259a734b8ebae786f131450350"
EXPECTED_TOKEN_SIGNATURE = (
    "FD292F4D67C58E088B953E4A66883C2394A56DC3806F3581876858F1F2A0F997"
)
EXPECTED_REALTIME_MAP_SIGNATURE = (
    "D8A0B35D37F75AEFE3B1F19F18A53FBCC9CB9C55779C4BF860CA0DFB43CAF5FD"
)
EXPECTED_ACCESS_TOKEN = "correct_access_token"
EXPECTED_LAYOUT_MAP_URL = "correct_layout_map_url"
EXPECTED_PATH_MAP_URL = "correct_path_map_url"

WRONG_TOKEN_SIGNATURE = (
    "16B758933F6DECA1098948359545C4FA6BC6899AA87C09579A9DDE7A6F2F6AA5"
)

# Mock the uuid4 function to a fixed value
DEFINED_UUID = UUID("0e950a25-9a73-4b8e-bae7-86f131450350")
# Mock the datetime module to a fixed time
DEFINED_TIME = "2024-11-02 12:00:01"

ACCESS_TOKEN_ENDPOINT = "/v1.0/token?grant_type=1"

# Dangerous to use this option as it can lead to regression
pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def get_realtime_map_endpoint(device_id: str) -> str:
    """Get the endpoint to request the realtime map data for a device."""

    return f"/v1.0/users/sweepers/file/{device_id}/realtime-map"


@pytest.fixture(autouse=True)
def frozen_time(request: pytest.FixtureRequest):
    """Set the time for all tests to a defined time by default."""

    # Skip the time freezing for functional tests
    if "functional" in request.keywords:
        yield
    else:
        # Freeze the time
        with freezegun.freeze_time(DEFINED_TIME):
            yield


@pytest.fixture(name="mock_api")
def fixture_mock_api(httpx_mock: HTTPXMock) -> httpx.Client:
    """Mock responses from the Tuya Cloud API."""

    # Correct access token request
    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}{ACCESS_TOKEN_ENDPOINT}",
        match_headers={
            "client_id": CORRECT_CLIENT_ID,
            "sign": EXPECTED_TOKEN_SIGNATURE,
            "t": EXPECTED_TIMESTAMP,
            "lang": "en",
            "nonce": EXPECTED_NONCE,
        },
        json={"success": True, "result": {"access_token": EXPECTED_ACCESS_TOKEN}},
    )

    # Correct realtime map request
    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}{get_realtime_map_endpoint(CORRECT_DEVICE_ID)}",
        match_headers={
            "client_id": CORRECT_CLIENT_ID,
            "sign": EXPECTED_REALTIME_MAP_SIGNATURE,
            "t": EXPECTED_TIMESTAMP,
            "lang": "en",
            "nonce": EXPECTED_NONCE,
        },
        json={
            "success": True,
            "result": [
                {"map_url": EXPECTED_LAYOUT_MAP_URL, "map_type": 0},
                {"map_url": EXPECTED_PATH_MAP_URL, "map_type": 1},
            ],
        },
    )

    # Invalid client id access token request
    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}{ACCESS_TOKEN_ENDPOINT}",
        match_headers={
            "client_id": WRONG_CLIENT_ID,
            # "sign": EXPECTED_TOKEN_SIGNATURE, Sign is tied to the client id
            "t": EXPECTED_TIMESTAMP,
            "lang": "en",
            "nonce": EXPECTED_NONCE,
        },
        json={"success": False, "code": 1005},
    )

    # Invalid sign access token request
    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}{ACCESS_TOKEN_ENDPOINT}",
        match_headers={
            "client_id": CORRECT_CLIENT_ID,
            "sign": WRONG_TOKEN_SIGNATURE,
            "t": EXPECTED_TIMESTAMP,
            "lang": "en",
            "nonce": EXPECTED_NONCE,
        },
        json={"success": False, "code": 1004},
    )

    # Invalid origin realtime map request
    httpx_mock.add_response(
        url=f"{WRONG_ORIGIN}{ACCESS_TOKEN_ENDPOINT}",
        match_headers={
            "client_id": CORRECT_CLIENT_ID,
            "sign": EXPECTED_TOKEN_SIGNATURE,
            "t": EXPECTED_TIMESTAMP,
            "lang": "en",
            "nonce": EXPECTED_NONCE,
        },
        json={"success": False, "code": 2007},
    )

    # Invalid device id realtime map request
    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}{get_realtime_map_endpoint(WRONG_DEVICE_ID)}",
        json={"success": False, "code": 1106},
    )

    return httpx.Client()


@pytest.fixture(name="tuya")
def fixture_tuya(
    request: pytest.FixtureRequest, mocker: MockerFixture, mock_api: httpx.Client
) -> TuyaCloudAPI:
    """Create a TuyaCloudAPI instance for testing."""

    # Mock the UUID generation
    mocker.patch("uuid.uuid4", return_value=DEFINED_UUID)

    # Avoid error if not parametrized
    if not hasattr(request, "param"):
        request.param = {}

    # Get the parameters for the TuyaCloudAPI instance
    origin = request.param.get("origin", CORRECT_ORIGIN)
    client_id = request.param.get("client_id", CORRECT_CLIENT_ID)
    client_secret = request.param.get("client_secret", CORRECT_CLIENT_SECRET)

    return TuyaCloudAPI(origin, client_id, client_secret, mock_api)


# Mock the datetime module to a fixed time
# @freeze_time("2024-11-02 12:00:01")
def test_get_timestamp(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.get_timestamp."""

    assert tuya.get_timestamp() == EXPECTED_TIMESTAMP


def test_get_nonce(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.get_nonce."""

    assert tuya.get_nonce() == EXPECTED_NONCE


def test_create_signature(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.create_signature."""

    method = "GET"
    endpoint = get_realtime_map_endpoint(CORRECT_DEVICE_ID)
    timestamp = EXPECTED_TIMESTAMP
    nonce = EXPECTED_NONCE
    access_token = EXPECTED_ACCESS_TOKEN

    signature = tuya.create_signature(method, endpoint, timestamp, nonce, access_token)

    assert signature == EXPECTED_REALTIME_MAP_SIGNATURE


def test_request(tuya: TuyaCloudAPI, httpx_mock: HTTPXMock):
    """Test TuyaCloudAPI.request."""

    response = tuya.request("GET", get_realtime_map_endpoint(CORRECT_DEVICE_ID))

    assert response["success"]
    assert response["result"][0]["map_url"] == EXPECTED_LAYOUT_MAP_URL
    assert response["result"][1]["map_url"] == EXPECTED_PATH_MAP_URL

    requests = httpx_mock.get_requests()

    # Check if the access token request was successful
    request = requests[0]
    headers = request.headers
    assert request.url == f"{CORRECT_ORIGIN}{ACCESS_TOKEN_ENDPOINT}"
    assert headers.get("client_id") == CORRECT_CLIENT_ID
    assert headers.get("sign") == EXPECTED_TOKEN_SIGNATURE
    assert headers.get("sign_method") == "HMAC-SHA256"
    assert headers.get("t") == EXPECTED_TIMESTAMP
    assert headers.get("lang") == "en"
    assert headers.get("nonce") == EXPECTED_NONCE

    # Check if the endpoint request was successful
    request = requests[1]
    headers = request.headers
    assert (
        request.url == f"{CORRECT_ORIGIN}{get_realtime_map_endpoint(CORRECT_DEVICE_ID)}"
    )
    assert headers.get("client_id") == CORRECT_CLIENT_ID
    assert headers.get("sign") == EXPECTED_REALTIME_MAP_SIGNATURE
    assert headers.get("sign_method") == "HMAC-SHA256"
    assert headers.get("t") == EXPECTED_TIMESTAMP
    assert headers.get("lang") == "en"
    assert headers.get("nonce") == EXPECTED_NONCE


@pytest.mark.parametrize("tuya", [{"client_id": WRONG_CLIENT_ID}], indirect=True)
def test_invalid_client_id(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.request with an invalid client id."""

    with pytest.raises(InvalidClientIDError):
        tuya.request("GET", ACCESS_TOKEN_ENDPOINT)


@pytest.mark.parametrize(
    "tuya", [{"client_secret": WRONG_CLIENT_SECRET}], indirect=True
)
def test_invalid_client_secret(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.request with an invalid client secret."""

    with pytest.raises(InvalidClientSecretError):
        tuya.request("GET", ACCESS_TOKEN_ENDPOINT)


@pytest.mark.parametrize("tuya", [{"origin": WRONG_ORIGIN}], indirect=True)
def test_invalid_origin(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.request with an invalid origin."""

    with pytest.raises(CrossRegionAccessError):
        tuya.request("GET", ACCESS_TOKEN_ENDPOINT)


def test_invalid_device_id(tuya: TuyaCloudAPI):
    """Test TuyaCloudAPI.request with an invalid device id."""

    with pytest.raises(InvalidDeviceIDError):
        tuya.request("GET", get_realtime_map_endpoint(WRONG_DEVICE_ID))


@pytest.mark.functional
def test_real_request():
    """Test TuyaCloudAPI.request with a real request to the cloud."""

    # Try to get the Tuya Cloud API credentials from the environment
    origin = os.getenv("ORIGIN")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    # Skip the test if the credentials are not available
    if not origin or not client_id or not client_secret:
        pytest.skip("Missing Tuya Cloud API credentials")

    # Create a TuyaCloudAPI instance
    tuya = TuyaCloudAPI(origin, client_id, client_secret)

    # Try to request a access token
    response = tuya.request("GET", "/v1.0/token?grant_type=1", False)

    # Check if the response is successful
    assert response["success"]
