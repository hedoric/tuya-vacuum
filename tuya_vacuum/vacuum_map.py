"""Handle vacuum maps for Tuya vacuums. Each map consists of a layout and a path."""

from PIL import Image

from tuya_vacuum.vacuum_map_layout import VacuumMapLayout
from tuya_vacuum.vacuum_map_path import VacuumMapPath, PATH_SCALE


class VacuumMap:
    """A vacuum map from a vacuum."""

    def __init__(self, layout: str, path: str) -> None:
        """Parse the layout and path of a vacuum map.

        @param layout: Hexadecimal string of the layout.
        @param path: Hexadecimal string of the path.
        """
        self.layout = VacuumMapLayout(layout)
        self.path = VacuumMapPath(path)

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

    @staticmethod
    def crop_image(
        image: Image.Image,
        crop_height: int,
        crop_width: int,
        origin_x: int,
        origin_y: int,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> Image.Image:
        """Return a cropped version of the given image"""

        height = PATH_SCALE * crop_height
        width = PATH_SCALE * crop_width
        origin_x = (origin_x + offset_x) * PATH_SCALE
        origin_y = (origin_y + offset_y) * PATH_SCALE

        return image.crop(
            (
                origin_x - width / 2,
                origin_y - height / 2,
                origin_x + width / 2,
                origin_y + height / 2,
            )
        )
