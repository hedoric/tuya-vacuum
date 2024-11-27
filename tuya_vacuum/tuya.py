"""Handles communication with a Tuya Cloud API."""

import datetime
import hmac
import logging

# from uuid import uuid4
import uuid

import httpx

_LOGGER = logging.getLogger(__name__)

# The SHA256 hash of a empty request body
EMPTY_BODY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Tuya Cloud API endpoint to get an access token
ACCESS_TOKEN_ENDPOINT = "/v1.0/token?grant_type=1"


class InvalidClientIDError(Exception):
    """Invalid Client ID Error."""


class InvalidClientSecretError(Exception):
    """Invalid Client Secret Error."""


class InvalidDeviceIDError(Exception):
    """Invalid Device ID Error."""


class CrossRegionAccessError(Exception):
    """Cross Region Access Error."""


class TuyaCloudAPI:
    """Handles communication with a Tuya Cloud API."""

    def __init__(
        self,
        origin: str,
        client_id: str,
        client_secret: str,
        client: httpx.Client = None,
    ) -> None:
        """
        Initialize the TuyaCloudAPI instance.

        Parameters:
            origin (str): The Tuya Cloud API endpoint.
            client_id (str): The client ID for the Tuya API.
            client_secret (str): The client secret for the Tuya API.
            client (httpx.Client): (optional) The HTTP client/session to use for requests.

        The **origin** must contain the protocol and host of the Tuya API endpoint.
        URL anatomy is defined here https://developer.mozilla.org/en-US/docs/Web/API/Location.
        """
        self.origin = origin
        self.client_id = client_id
        self.client_secret = client_secret

        if client is None:
            self.client = httpx.Client(timeout=2.5)
        else:
            self.client = client

    def create_signature(
        self,
        method: str,
        endpoint: str,
        timestamp: str,
        nonce: str,
        access_token: str,
        signature_key: str = "",
    ) -> str:
        """
        Generate a signature required for Tuya Cloud authorization.

        To make a request to a API endpoint,
        you need to provide a signature to verify your identity and ensure data security.

        Parameters:
            method (str): The HTTP method used for the request.
            endpoint (str): The endpoint requested.
            timestamp (str): The 13-digit timestamp.
            nonce (str): The UUID generated for each API request.
            access_token (str): The access token used for the request.
            signature_key (str):
                (optional) A string in which all headers are concatenated with newlines.

        Returns:
            signature (str): The signature for the request.

        The signature algorithm is documented here:
        https://developer.tuya.com/en/docs/iot/new-singnature?id=Kbw0q34cs2e5g
        """

        str_to_sign = (
            f"{self.client_id}"
            f"{access_token}"
            f"{timestamp}"
            f"{nonce}"
            f"{method}\n"
            f"{EMPTY_BODY_HASH}\n"
            f"{signature_key}\n"
            f"{endpoint}"
        )

        signature = (
            hmac.new(
                self.client_secret.encode(),
                msg=str_to_sign.encode(),
                digestmod="sha256",
            )
            .hexdigest()
            .upper()
        )

        return signature

    @staticmethod
    def get_timestamp() -> str:
        """
        Get the 13-digit timestamp needed for Tuya Cloud API requests.
        """
        return str(int(round(datetime.datetime.now().timestamp() * 1000, 0)))

    @staticmethod
    def get_nonce() -> str:
        """
        Get a UUID optionally required for each API request.

        Returns:
            nonce (str): A random 32-character lowercase hexadecimal string.
        """
        return uuid.uuid4().hex

    def request(self, method: str, endpoint: str, fetch_token: bool = True) -> dict:
        """
        Make a request to a Tuya Cloud API endpoint.

        Parameters:
            method (str): The HTTP method to use for the request.
            endpoint (str): The endpoint to request.
            fetch_token (bool): (optional) Whether to fetch a new access token first.

        If **fetch_token** is True but **access_token** is provided,
        the **access_token** will be used.

        The request structure is documented here:
        https://developer.tuya.com/en/docs/iot/api-request?id=Ka4a8uuo1j4t4
        """

        _LOGGER.debug(
            "Making '%s' request to '%s' at '%s'", method, self.origin, endpoint
        )

        access_token = ""
        if fetch_token:
            _LOGGER.debug("Fetching access token")
            response = self.request("GET", ACCESS_TOKEN_ENDPOINT, fetch_token=False)
            access_token = response["result"]["access_token"]

        # The 13-digit timestamp
        timestamp = self.get_timestamp()

        # UUID generated for each API request
        # 32-character lowercase hexadecimal string
        nonce = self.get_nonce()

        # Generate sign
        signature = self.create_signature(
            method=method,
            endpoint=endpoint,
            timestamp=timestamp,
            nonce=nonce,
            access_token=access_token,
        )

        headers = {
            "client_id": self.client_id,  # The user ID
            "sign": signature,  # The signature generated by signature algorithm
            "sign_method": "HMAC-SHA256",  # The signature digest algorithm
            "t": timestamp,  # The 13-digit timestamp
            "lang": "en",  # (optional) The type of language
            "nonce": nonce,  # (optional) The UUID generated for each API request
        }

        if access_token:
            headers["access_token"] = access_token

        response = self.client.request(
            method,
            f"{self.origin}{endpoint}",
            headers=headers,
        ).json()

        # Check if the request failed
        if not response["success"]:
            # Check Tuya global error codes
            # https://developer.tuya.com/en/docs/iot/error-code?id=K989ruxx88swc
            error_code = response["code"]
            # error_message = response["msg"]

            if error_code == 1001 or error_code == 1004:
                # The secret is invalid or the sign is invalid
                raise InvalidClientSecretError("Invalid Client Secret")
            elif error_code == 1005 or error_code == 2009:
                # The client_id is invalid
                raise InvalidClientIDError("Invalid Client ID")
            elif error_code == 2007:
                # The IP address of the request is from another data center.
                # Access is not allowed.
                raise CrossRegionAccessError(
                    "Wrong server region. Cross-region access is not allowed."
                )
            elif error_code == 1106:
                # No permission.
                # Not allowed to access the API or device.
                # Assume the device ID is invalid.
                raise InvalidDeviceIDError("Invalid Device ID")
            else:
                # Unknown error code
                raise RuntimeError(f"Request failed, unknown error: {response}")

        return response
