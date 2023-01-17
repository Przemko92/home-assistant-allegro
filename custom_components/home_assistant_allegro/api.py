"""Sample API Client."""
from .token_flow import TokenFlow

import asyncio
import logging
import socket
from typing import Any

import aiohttp
import async_timeout
from .const import ALLEGRO_API_URL, ALLEGRO_BASE_URL

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)


class HomeAssistantAllegroApiClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        token: object = None,
    ) -> None:
        """Sample API Client."""
        self._api_wrapper = ApiWrapper(session)
        self._token_flow = TokenFlow(session, client_id, client_secret, token)

    async def get_standard_header(self) -> dict:
        return {
            "Cookie": "cartUserId=14752576-ffff-ffff-ffff-ffffffffffffffffffff-ffff-ffff-ffff-ffffffffffff; QXLSESSID=697780b4fe33a53d55826c20f04744410168c566846f2f//03; ws3=LFM8liLCD1YT8cuU5bBrXsNBszx967S23; qeppo_login2=%7B%22welcome%22%3A%22Witaj%2C%22%2C%22id%22%3A%2214752576%22%2C%22username%22%3A%22HucK92%22%2C%22isCompany%22%3Afalse%7D; QXLDATA=stezXBvhhRSznYQhA%2BCEkWhg8w0XcwFcaLHFwC%2FU6VU%3D%23%23%23TdonRyC8uVCJwX6dGgBxUPVRNeInfh3vsBJLvoaYQxBtJ5tS%2FNqJhgx9yiyulcHs5JTDnvvKgEnK1i%2FrG1CloUhU6ZFSBZQ6WApVxUQMqyP5MiiMUfuUdHC4mSPrpsDbbWrCEDKdq5hza6I%3D; qeppo_priv_cookie=NWM5OQUMAAAHVg4PNDg3NQ%3D%3D; userIdentity=%7B%22id%22%3A%2214752576%22%7D; ws1=NWM5OQUMAAAHVg4PNDg3NQ%3D%3D; enc_ws1=NWM5OQUMAAAHVg4PNDg3NQ%3D%3D; dc1=NWM5OQUMAAAHVg4PNDg3NQ%3D%3D; dc2=NDRhNnxvfwR7ZTR7c3lzeWJTVWZ8fFUCemVcCzI4MjE%3D; datadome=5uRus8W9KqUr-lB4e4pnHE-XXsaB2RAAIxvGvD_5Abneva_iCn732NP4pfrMJwLj9JA49exOhVFIRXCXp0~XO~WNEmQsEswIxdzlGJDCD54MEwpzDl7GyKLNF5TGKbGs; __gfp_64b=-TURNEDOFF; wdctx=v4.M7NexS8Ugkk7albXrQwNrhcKYtGI1cIFBFflCC-45f-aHJyZgTu7qFCFsT9ra4KGE__Sw8Eo6JYrcZuzlVDvtYLvksZ7K2ImROvH9wyAujKDfXTsEtI3AgF39-FfAoHItpxCCBDBFjD7_bty7cwOg9B9kcW0NN7wNZ0BEXIv2hRO4eiA5YlkKh4zpbGw-QGUFPV0EX6Rraw1CjAflOXLSbVzWs1nfvqcIZWa3S9GraU6f5lxVd5IrbCpvEgs; _cmuid=fa64c75b-6855-4424-8d2e-fba0e46200c3; parcelsChecksum=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855; chronos_cookie=1; all_rct=rct42818809086588e33",
            "Accept": "application/vnd.allegro.public.v1+json",
            "Referer": "https://allegro.pl/",
        }

    async def get_auth_url(self) -> str:
        return await self._token_flow.get_auth_url()

    async def await_for_token(self):
        return await self._token_flow.await_for_token()

    async def get_user_info(self) -> dict:
        headers = await self.get_standard_header()
        user_info_response = await self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/me", headers=headers
        )
        return user_info_response

    async def get_orders(self) -> dict:
        headers = await self.get_standard_header()
        get_orders_response = await self._api_wrapper.get(
            f"{ALLEGRO_API_URL}/myorder-api/myorders/", headers=headers
        )
        return get_orders_response


class ApiWrapper:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def get(self, url: str, headers: dict = {}, auth: Any = None) -> dict:
        return await self.api_wrapper("get", url, headers=headers, auth=auth)

    async def post(
        self, url: str, data: dict = {}, headers: dict = {}, auth: Any = None
    ) -> dict:
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

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
