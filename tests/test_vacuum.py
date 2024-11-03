"""Test the vacuum module."""

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tuya_vacuum.vacuum import TuyaVacuum
from tuya_vacuum.vacuum_map_layout import VacuumMapLayout
from tuya_vacuum.vacuum_map_path import VacuumMapPath

CORRECT_CLIENT_ID = "correct_client_id"
CORRECT_CLIENT_SECRET = "correct_client_secret"
CORRECT_DEVICE_ID = "correct_device_id"
CORRECT_ORIGIN = (
    "https://correct_origin.com"  # Origin of the correct server for the device
)


@pytest.mark.skip(reason="Test not correctly implemented yet")
def test_fetch_realtime_map(mocker: MockerFixture, httpx_mock: HTTPXMock):
    """Test fetching the realtime map."""
    vacuum = TuyaVacuum(
        CORRECT_ORIGIN, CORRECT_CLIENT_ID, CORRECT_CLIENT_SECRET, CORRECT_DEVICE_ID
    )

    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}/v1.0/token?grant_type=1",
        json={
            "success": True,
            "result": {
                "access_token": "correct_access_token",
            },
        },
    )

    httpx_mock.add_response(
        url=f"{CORRECT_ORIGIN}{f"/v1.0/users/sweepers/file/{CORRECT_DEVICE_ID}/realtime-map"}",
        json={
            "success": True,
            "result": [
                {
                    "map_url": f"{CORRECT_ORIGIN}/layout.bin",
                    "map_type": 0,
                },
                {
                    "map_url": f"{CORRECT_ORIGIN}/path.bin",
                    "map_type": 1,
                },
                {
                    "map_url": f"{CORRECT_ORIGIN}/unknown.bin",
                    "map_type": 2,
                },
            ],
        },
    )

    httpx_mock.add_response(url=f"{CORRECT_ORIGIN}/path.bin", content=b"path_data")
    httpx_mock.add_response(url=f"{CORRECT_ORIGIN}/layout.bin", content=b"layout_data")
    httpx_mock.add_response(url=f"{CORRECT_ORIGIN}/unknown.bin")

    f1 = mocker.patch(
        "tuya_vacuum.vacuum_map_layout.VacuumMapLayout.__init__", return_value=None
    )
    f2 = mocker.patch(
        "tuya_vacuum.vacuum_map_path.VacuumMapPath.__init__", return_value=None
    )

    vacuum_map = vacuum.fetch_realtime_map()

    # Check that the VacuumMapLayout and VacuumMapPath were initialized correctly
    f1.assert_called_once_with(b"layout_data")
    f2.assert_called_once_with(b"path_data")

    # Check that the VacuumMap was initialized correctly
    assert isinstance(vacuum_map.layout, VacuumMapLayout)
    assert isinstance(vacuum_map.path, VacuumMapPath)
