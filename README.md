# tuya-vacuum
tuya-vacuum is a python library to view maps from Tuya robot vacuums.

## Installation
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install tuya-vacuum.

```bash
pip install tuya-vacuum
```

## Usage
```python
from tuya_vacuum.tuya import TuyaCloudAPI
import requests

# Create a new TuyaCloudAPI instance
tuya = TuyaCloudAPI(
    origin="https://openapi.tuyaus.com",
    client_id="<Client ID>",
    client_secret="<Client Secret>"
)

# Request the current realtime map data from the cloud
device_id = "<Device ID>"
response = tuya.request("GET", f"/v1.0/users/sweepers/file/{device_id}/realtime-map")

# Get the layout and path data using the returned map urls
layout_data = requests.get(response["result"][0]["map_url"]).content.hex()
path_data = requests.get(response["result"][1]["map_url"]).content.hex()

# Parse the map data
vacuum_map = VacuumMap(layout_data, path_data)

# Save the map as an image
image = vacuum_map.to_image()
image.save("output.png")
```

## Compatability List

This is a list of all currently tested devices. Create a new [issue](https://github.com/jaidenlab/tuya-vacuum/issues) to add your device.

| Device                                                | Support                           |
| ----------------------------------------------------- | --------------------------------- |
| [Lefant M1](https://www.lefant.com/en-ca/products/m1) | <text style="color:lightgreen">Supported</text> |

## Special Thanks
- [Tuya Cloud Vacuum Map Extractor](https://github.com/oven-lab/tuya_cloud_map_extractor) by [@oven-lab](https://github.com/oven-lab)