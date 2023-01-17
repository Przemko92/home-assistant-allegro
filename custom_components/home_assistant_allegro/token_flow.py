import aiohttp
import time
import async_timeout
import logging
import asyncio
import socket
from datetime import datetime, timedelta
from typing import Any
from .const import ALLEGRO_BASE_URL

TIMEOUT = 10
_LOGGER: logging.Logger = logging.getLogger(__package__)


class TokenFlow:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        token: Any,
    ) -> None:
        """Token Flow."""
        self._session = session
        self._client_id = client_id

        self._client_secret = client_secret
        self._token = token
        if token:
            self._token_expire_time = datetime.now() + timedelta(
                seconds=int(token["expires_in"])
            )
        else:
            self._token_expire_time = None
        self._device_code = None

    async def get_auth_url(self) -> str:
        payload = {"client_id": self._client_id}
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        device_code = await self.post(
            f"{ALLEGRO_BASE_URL}/auth/oauth/device",
            headers=headers,
            data=payload,
            auth=aiohttp.BasicAuth(self._client_id, self._client_secret),
        )

        self._device_code = device_code
        return device_code["verification_uri_complete"]

    async def get_token(self) -> Any:
        if self._device_code is not None:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": self._device_code["device_code"],
            }
            api_call_response = await self.post(
                f"{ALLEGRO_BASE_URL}/auth/oauth/token",
                auth=(aiohttp.BasicAuth(self._client_id, self._client_secret)),
                headers=headers,
                data=data,
            )
            return api_call_response

    async def await_for_token(self):
        if self._device_code is not None:
            interval = int(self._device_code["interval"])

            while True:
                time.sleep(interval)
                token = await self.get_token()

                if "access_token" in token:
                    self._token = token
                    self._token_expire_time = datetime.now() + timedelta(
                        seconds=int(token["expires_in"])
                    )
                    return token
                if token["error"] == "slow_down":
                    interval += interval
                if token["error"] == "access_denied":
                    break
                if token["error"] == "Invalid device code":
                    break

    async def get_access_token(self) -> str:
        if self.token_is_valid():
            return self._token["access_token"]
        else:
            return await self.refresh_token()

    def token_is_valid(self) -> bool:
        if self._token_expire_time is not None:
            return self._token_expire_time > (datetime.now() + timedelta(minutes=1))
        return False

    async def refresh_token(self) -> Any:
        return None

    async def post(
        self,
        url: str,
        data: dict = {},
        headers: dict = {},
        auth: Any = None,
    ) -> Any:
        """Get information from the API."""
        async with async_timeout.timeout(TIMEOUT):
            response = await self._session.post(
                url, headers=headers, data=data, auth=auth
            )
            return await response.json()
