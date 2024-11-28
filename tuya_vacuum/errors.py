"""Package level errors"""


class InvalidClientIDError(Exception):
    """Invalid Client ID Error."""


class InvalidClientSecretError(Exception):
    """Invalid Client Secret Error."""


class InvalidDeviceIDError(Exception):
    """Invalid Device ID Error."""


class CrossRegionAccessError(Exception):
    """Cross Region Access Error."""
