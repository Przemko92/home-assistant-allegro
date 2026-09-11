"""Allegro API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import ALLEGRO_API_URL, CONF_COOKIE
from .models import Order, parse_orders

TIMEOUT = aiohttp.ClientTimeout(total=10)
_LOGGER = logging.getLogger(__package__)


class AllegroApiError(Exception):
    """Raised when an Allegro API request fails."""


class AllegroApiClient:
    """HTTP client for Allegro buyer endpoints."""

    def __init__(self, cookie: str, session: aiohttp.ClientSession) -> None:
        self._cookie = cookie
        self._session = session

    def _headers(self, api_ver: int) -> dict[str, str]:
        return {
            "Cookie": f"{CONF_COOKIE}={self._cookie}",
            "Accept": f"application/vnd.allegro.public.v{api_ver}+json",
            "Referer": "https://allegro.pl/",
        }

    async def _get(self, path: str, api_ver: int) -> Any:
        url = f"{ALLEGRO_API_URL}{path}"
        try:
            async with self._session.get(
                url, headers=self._headers(api_ver), timeout=TIMEOUT
            ) as response:
                if response.status >= 400:
                    raise AllegroApiError(f"HTTP {response.status} for {path}")
                return await response.json()
        except TimeoutError as err:
            _LOGGER.error("Timeout fetching %s", url)
            raise AllegroApiError(f"Timeout fetching {url}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
            raise AllegroApiError(f"Error fetching {url}") from err

    async def async_get_orders(self) -> list[Order]:
        """Return parsed buyer orders."""
        payload = await self._get("/myorder-api/myorders?limit=25", 3)
        if not isinstance(payload, dict):
            raise AllegroApiError("Unexpected orders response")
        return parse_orders(payload)

    async def async_get_login(self) -> str:
        """Return the Allegro login for the current cookie."""
        payload = await self._get("/users", 2)
        try:
            return payload["accounts"]["allegro"]["login"]
        except (KeyError, TypeError) as err:
            raise AllegroApiError("Unexpected user info response") from err
