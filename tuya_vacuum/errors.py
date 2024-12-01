"""Package level errors"""


class TuyaError(Exception):
    """Tuya Error."""


class InvalidClientIDError(TuyaError):
    """Invalid Client ID Error."""


class InvalidClientSecretError(TuyaError):
    """Invalid Client Secret Error."""


class InvalidDeviceIDError(TuyaError):
    """Invalid Device ID Error."""


class CrossRegionAccessError(TuyaError):
    """Cross Region Access Error."""
