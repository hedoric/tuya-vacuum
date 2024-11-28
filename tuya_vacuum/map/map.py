"""The Map class."""

import logging

from PIL import Image

from tuya_vacuum.map.layout import Layout
from tuya_vacuum.map.path import PATH_SCALE, Path

_LOGGER = logging.getLogger(__name__)


class Map:
    """A vacuum map, the combination of a layout and path."""

    def __init__(self, layout: Layout, path: Path) -> None:
        self.layout = layout
        self.path = path

    def to_image(self) -> Image.Image:
        """Create an image of the vacuum map."""

        # Get layout image
        layout_image = self.layout.to_image()
        layout_image = layout_image.resize(
            (layout_image.width * PATH_SCALE, layout_image.height * PATH_SCALE),
            resample=Image.Resampling.NEAREST,
        )

        # Get path image
        path_image = self.path.to_image(
            self.layout.width,
            self.layout.height,
            (self.layout.origin_x, self.layout.origin_y),
        )

        # Combine the images
        layout_image.paste(path_image, mask=path_image)

        return layout_image
