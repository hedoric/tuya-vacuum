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

    def fetch_map(self) -> tuya_vacuum.Map:
        """
        Get the current map from the vacuum cleaner.

        Falls back to /list + /download if realtime-map is empty
        (as on Mongsa MS1).
        """
        response = self.api.request(
            "GET", f"/v1.0/users/sweepers/file/{self.device_id}/realtime-map"
        )

        if not response.get("result"):
            _LOGGER.debug("Realtime map empty → falling back to file-based map")
            return self.fetch_latest_map_file()

        layout = None
        path = None

        for map_part in response["result"]:
            map_url = map_part.get("map_url")
            map_type = map_part.get("map_type")

            if not map_url:
                continue

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

    def fetch_latest_map_file(self) -> tuya_vacuum.Map:
        """Retrieve the most recent map via /list → /download endpoints."""
        # Step 1: list maps
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
        record_id = first["id"] if isinstance(first, dict) else first

        # Step 2: download links
        dl_resp = self.api.request(
            "GET",
            f"/v1.0/users/sweepers/file/{self.device_id}/download?id={record_id}",
        )
        result = dl_resp.get("result") or {}
        url = result.get("app_map") or result.get("robot_map")
        if not url:
            raise RuntimeError("Download links missing (no app_map/robot_map)")

        # Step 3: download and decode
        raw = self.api.client.request("GET", url).content
        data = raw
        if len(data) >= 2 and data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        if data[:1] in (b"{", b"["):
            try:
                j = json.loads(data.decode("utf-8", "ignore"))
                if isinstance(j, dict):
                    enc = j.get("img") or j.get("map") or j.get("data")
                    if isinstance(enc, str):
                        data = base64.b64decode(enc)
            except Exception as e:
                _LOGGER.debug("JSON parse error on fallback map: %s", e)

        # Step 4: wrap in Map
        try:
            layout = tuya_vacuum.map.Layout(data)
            path = None
        except Exception as e:
            _LOGGER.warning("Failed to parse fallback map layout: %s", e)
            layout, path = None, None

        return tuya_vacuum.Map(layout, path)
