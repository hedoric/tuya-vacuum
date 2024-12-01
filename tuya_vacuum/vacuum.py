"""Reprensentation of a Tuya vacuum cleaner."""

import logging

import httpx

import tuya_vacuum
import tuya_vacuum.tuya

_LOGGER = logging.getLogger(__name__)


class Vacuum:
    """Representation of a vacuum cleaner."""

    def __init__(
        self,
        origin: str,
        client_id: str,
        client_secret: str,
        device_id: str,
        client: httpx.Client = None,
    ) -> None:
        """Initialize the Vacuum instance."""

        self.device_id = device_id
        self.api = tuya_vacuum.tuya.TuyaCloudAPI(
            origin, client_id, client_secret, client
        )

    def fetch_map(self) -> tuya_vacuum.Map:
        """Get the current real-time map from the vacuum cleaner."""

        # Get the URLs where map data (ex. layout, path) is stored
        response = self.api.request(
            "GET", f"/v1.0/users/sweepers/file/{self.device_id}/realtime-map"
        )

        layout = None
        path = None

        for map_part in response["result"]:
            map_url = map_part["map_url"]
            map_type = map_part["map_type"]

            # Use the httpx client to get the map data directly
            map_data = self.api.client.request("GET", map_url).content

            match map_type:
                case 0:
                    layout = tuya_vacuum.map.Layout(map_data)
                case 1:
                    path = tuya_vacuum.map.Path(map_data)
                case _:
                    _LOGGER.warning("Unknown map type: %s", map_type)

        # Important issue for debugging, but still attempt to create the map
        if layout is None:
            _LOGGER.warning("No layout data found")
        if path is None:
            _LOGGER.warning("No path data found")

        return tuya_vacuum.Map(layout, path)
