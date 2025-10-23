"""Representation of a Tuya vacuum cleaner."""

import logging
import base64
import gzip
import json

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

    # --- existing realtime map fetch ---
    def fetch_map(self) -> tuya_vacuum.Map:
        """Get the current real-time map from the vacuum cleaner."""
        response = self.api.request(
            "GET", f"/v1.0/users/sweepers/file/{self.device_id}/realtime-map"
        )

        # Fallback trigger: some models (e.g., Mongsa MS1) return an empty result
        if not response.get("result"):
            _LOGGER.debug("Realtime map empty, falling back to file-based map")
            return self.fetch_latest_map_file()

        layout = None
        path = None

        for map_part in response["result"]:
            map_url = map_part["map_url"]
            map_type = map_part["map_type"]

            map_data = self.api.client.request("GET", map_url).content

            match map_type:
                case 0:
                    layout = tuya_vacuum.map.Layout(map_data)
                case 1:
                    path = tuya_vacuum.map.Path(map_data)
                case _:
                    _LOGGER.warning("Unknown map type: %s", map_type)

        if layout is None:
            _LOGGER.warning("No layout data found")
        if path is None:
            _LOGGER.warning("No path data found")

        return tuya_vacuum.Map(layout, path)

    # --- new fallback for devices with no realtime map ---
    def fetch_latest_map_file(self) -> tuya_vacuum.Map:
        """
        Download the most recent map file via Tuya's /list and /download endpoints.
        Used when the realtime-map result is empty.
        """
        # 1) List available map files
        list_resp = self.api.request(
            "GET",
            f"/v1.0/users/sweepers/file/{self.device_id}/list?page_no=1&page_size=1",
        )
        items = (list_resp.get("result") or {})
        if isinstance(items, dict) and "list" in items:
            items = items["list"]
        if not items:
            raise RuntimeError("No map files available for fallback")

        first = items[0]
        record_id = first["id"] if isinstance(first, dict) and "id" in first else first

        # 2) Get download links for latest map
        dl_resp = self.api.request(
            "GET",
            f"/v1.0/users/sweepers/file/{self.device_id}/download?id={record_id}",
        )
        result = dl_resp.get("result") or {}
        url = result.get("app_map") or result.get("robot_map")
        if not url:
            raise RuntimeError("Download links missing (no app_map/robot_map)")

        # 3) Download map file
        raw = self.api.client.request("GET", url).content

        # 4) Decode if necessary
        data = raw
        if len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B:
            data = gzip.decompress(data)
        if data[:1] in (b"{", b"["):
            try:
                j = json.loads(data.decode("utf-8", "ignore"))
                if isinstance(j, dict):
                    enc = j.get("img") or j.get("map") or j.get("data")
                    if isinstance(enc, str):
                        data = base64.b64decode(enc)
            except Exception as e:
                _LOGGER.debug("Fallback map JSON parse failed: %s", e)

        # Some devices deliver the map as a single PNG image
        try:
            layout = tuya_vacuum.map.Layout(data)
            path = None
        except Exception as e:
            _LOGGER.warning("Failed to parse fallback map layout: %s", e)
            layout = None
            path = None

        return tuya_vacuum.Map(layout, path)
