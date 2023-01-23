"""Sample API Client."""
import logging
import asyncio
from typing import Any, Optional
import aiohttp
import async_timeout

from .types.get_user_info import GetUserInfoResult
from .types.get_order_result import GetOrdersResult

from .const import ALLEGRO_API_URL

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class AllegroApiClient:
    """Api client"""

    def __init__(self, cookie: str, session: aiohttp.ClientSession) -> None:
        """Sample API Client."""
        self._cookie = cookie
        self._api_wrapper = ApiWrapper(session)

    async def get_standard_header(self, api_ver=1) -> dict:
        """Returns standard request header"""
        return {
            "Cookie": "QXLSESSID=" + self._cookie,
            "Accept": f"application/vnd.allegro.public.v{api_ver}+json",
            "Referer": "https://allegro.pl/",
        }

    async def get_orders(self) -> GetOrdersResult:
        """Get orders from api"""
        headers = await self.get_standard_header(3)
        get_orders_response = await self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/myorder-api/myorders?limit=25", headers=headers
        )
        return GetOrdersResult(get_orders_response)

    async def get_user_info(self) -> GetUserInfoResult:
        """Get info about current user"""
        headers = await self.get_standard_header(2)
        get_orders_response = await self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/users", headers=headers
        )
        return GetUserInfoResult(get_orders_response)


class ApiWrapper:
    """Helper class"""

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def get(self, url: str, headers: dict = {}, auth: Any = None) -> dict:
        """Run http GET method"""
        return await self.api_wrapper("get", url, headers=headers, auth=auth)

    async def post(
        self, url: str, data: dict = {}, headers: dict = {}, auth: Any = None
    ) -> dict:
        """Run http POST method"""
        return await self.api_wrapper(
            "post", url, data=data, headers=headers, auth=auth
        )

    async def api_wrapper(
        self,
        method: str,
        url: str,
        data: dict = {},
        headers: dict = {},
        auth: Any = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "get":
                    response = await self._session.get(url, headers=headers, auth=auth)
                    return await response.json()

                elif method == "post":
                    response = await self._session.post(
                        url, headers=headers, data=data, auth=auth
                    )
                    return await response.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
