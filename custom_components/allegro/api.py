"""Allegro API client."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import quote, urlsplit

import aiohttp

from .const import ALLEGRO_API_URL, ALLEGRO_EDGE_URL, CONF_COOKIE
from .messages import (
    ATTACHMENT_HOST,
    Attachment,
    Messages,
    parse_attachments,
    parse_messages,
)
from .models import Cart, Order, parse_cart, parse_orders

TIMEOUT = aiohttp.ClientTimeout(total=10)
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=60)
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
MESSAGE_PAGES = 5
MESSAGE_CENTER_HEADERS = {"x-message-center-mode": "default"}
THREAD_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_LOGGER = logging.getLogger(__package__)

CART_DECORATORS = "CART_DEPRECATED,BENEFITS_DEPRECATED"


class AllegroApiError(Exception):
    """Raised when an Allegro API request fails."""


class AllegroApiClient:
    """HTTP client for Allegro buyer endpoints."""

    def __init__(self, cookie: str, session: aiohttp.ClientSession) -> None:
        self._cookie = cookie
        self._session = session

    def _headers(
        self,
        api_ver: int,
        *,
        public: bool = True,
        content_type: str | None = None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        kind = "public" if public else "internal"
        headers = {
            "Cookie": f"{CONF_COOKIE}={self._cookie}",
            "Accept": f"application/vnd.allegro.{kind}.v{api_ver}+json",
            "Referer": "https://allegro.pl/",
        }
        if content_type:
            headers["Content-Type"] = content_type
        if extra:
            headers.update(extra)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        api_ver: int,
        *,
        public: bool = True,
        base_url: str = ALLEGRO_API_URL,
        params: dict[str, str] | None = None,
        payload: Any | None = None,
        expected_status: int | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{base_url}{path}"
        content_type = None
        data = None
        if payload is not None:
            kind = "public" if public else "internal"
            content_type = f"application/vnd.allegro.{kind}.v{api_ver}+json"
            data = json.dumps(payload)
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(
                    api_ver,
                    public=public,
                    content_type=content_type,
                    extra=extra_headers,
                ),
                params=params,
                data=data,
                timeout=TIMEOUT,
            ) as response:
                if expected_status is not None:
                    ok = response.status == expected_status
                else:
                    ok = response.status < 400
                if not ok:
                    body = await response.text()
                    _LOGGER.error(
                        "Allegro API error %s for %s: %s",
                        response.status,
                        path,
                        body,
                    )
                    raise AllegroApiError(f"HTTP {response.status} for {path}")
                if response.status == 204:
                    return None
                return await response.json()
        except TimeoutError as err:
            _LOGGER.error("Timeout fetching %s", url)
            raise AllegroApiError(f"Timeout fetching {url}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
            raise AllegroApiError(f"Error fetching {url}") from err

    async def _get(self, path: str, api_ver: int, **kwargs: Any) -> Any:
        return await self._request("GET", path, api_ver, **kwargs)

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

    async def async_get_cart(self) -> Cart:
        """Return the current shopping cart."""
        payload = await self._get(
            "/cart",
            7,
            public=False,
            base_url=ALLEGRO_EDGE_URL,
            params={"decorators": CART_DECORATORS},
        )
        if not isinstance(payload, dict):
            raise AllegroApiError("Unexpected cart response")
        return parse_cart(payload)

    async def async_add_to_cart(self, item_id: str, quantity: int = 1) -> None:
        """Increase cart quantity for an offer. Succeeds on HTTP 204."""
        await self._request(
            "POST",
            "/carts/changeQuantityCommand",
            5,
            base_url=ALLEGRO_EDGE_URL,
            payload={"items": [{"itemId": item_id, "delta": quantity}]},
            expected_status=204,
        )

    async def async_get_messages(self) -> Messages:
        """Return the unread counter and the most recent message threads."""
        counters = await self._get(
            "/message-center/threads/counters",
            1,
            public=False,
            base_url=ALLEGRO_EDGE_URL,
        )
        try:
            unread = int(counters["unread"])
        except (KeyError, TypeError, ValueError) as err:
            raise AllegroApiError("Unexpected message counters response") from err
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        for _ in range(MESSAGE_PAGES):
            payload = await self._get(
                "/message-center/threads/view/list",
                1,
                public=False,
                base_url=ALLEGRO_EDGE_URL,
                params={"nextCursor": cursor} if cursor else None,
                extra_headers=MESSAGE_CENTER_HEADERS,
            )
            if not isinstance(payload, dict):
                raise AllegroApiError("Unexpected message list response")
            pages.append(payload)
            pagination = payload.get("pagination")
            cursor = (
                pagination.get("nextCursor") if isinstance(pagination, dict) else None
            )
            if not cursor:
                break
        return parse_messages(unread, pages)

    async def async_open_thread(self, thread_id: str) -> list[Attachment]:
        """Open a message thread, which marks it as read, and list its attachments."""
        if not THREAD_ID.match(thread_id):
            raise AllegroApiError("Invalid message thread id")
        payload = await self._get(
            f"/message-center/facade/chats/{quote(thread_id, safe='')}",
            3,
            public=False,
            base_url=ALLEGRO_EDGE_URL,
            params={"sort": "DESC"},
            extra_headers=MESSAGE_CENTER_HEADERS,
        )
        return parse_attachments(payload)

    async def async_download_attachment(self, url: str) -> bytes:
        """Download a message attachment. The session cookie is sent to Allegro only."""
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname != ATTACHMENT_HOST:
            raise AllegroApiError("Attachment is not hosted by Allegro")
        try:
            async with self._session.get(
                url,
                headers={
                    "Cookie": f"{CONF_COOKIE}={self._cookie}",
                    "Referer": "https://allegro.pl/",
                },
                timeout=DOWNLOAD_TIMEOUT,
            ) as response:
                if response.status != 200:
                    raise AllegroApiError(f"HTTP {response.status} for attachment")
                data = await response.content.read(MAX_ATTACHMENT_BYTES + 1)
        except TimeoutError as err:
            raise AllegroApiError("Timeout downloading attachment") from err
        except aiohttp.ClientError as err:
            raise AllegroApiError(f"Error downloading attachment: {err}") from err
        if len(data) > MAX_ATTACHMENT_BYTES:
            raise AllegroApiError("Attachment is too large")
        return data
