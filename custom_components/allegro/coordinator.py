"""Data update coordinator for Allegro."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import AllegroApiClient, AllegroApiError
from .const import (
    CONF_AUTO_READ,
    CONF_AUTO_READ_DAYS,
    CONF_DEFAULT_PICKUP_POINT,
    DEFAULT_AUTO_READ_DAYS,
    DOMAIN,
)
from .messages import Attachment, Messages, MessageThread
from .models import AllegroData, Cart

_LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(minutes=30)
MAX_AUTO_READ = 10
MAX_BULK_READ = 50

type AllegroConfigEntry = ConfigEntry["AllegroCoordinator"]


class AllegroCoordinator(DataUpdateCoordinator[AllegroData]):
    """Fetch and cache Allegro orders, cart and messages."""

    config_entry: AllegroConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: AllegroConfigEntry,
        client: AllegroApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = client

    @property
    def default_pickup_point(self) -> str:
        """Code of the user's usual parcel locker, for example `WAW01A`."""
        value = self.config_entry.options.get(CONF_DEFAULT_PICKUP_POINT) or ""
        return str(value).strip()

    async def _async_update_data(self) -> AllegroData:
        """Fetch orders, cart and messages from Allegro."""
        orders, cart_result, messages_result = await asyncio.gather(
            self.api.async_get_orders(),
            self.api.async_get_cart(),
            self.api.async_get_messages(),
            return_exceptions=True,
        )
        if isinstance(orders, BaseException):
            if isinstance(orders, AllegroApiError):
                raise UpdateFailed(str(orders)) from orders
            raise orders
        if isinstance(cart_result, AllegroApiError):
            _LOGGER.warning("Could not refresh Allegro cart: %s", cart_result)
            cart = self.data.cart if self.data is not None else Cart.empty()
        elif isinstance(cart_result, BaseException):
            raise cart_result
        else:
            cart = cart_result
        if isinstance(messages_result, AllegroApiError):
            _LOGGER.warning("Could not refresh Allegro messages: %s", messages_result)
            messages = self.data.messages if self.data is not None else Messages()
        elif isinstance(messages_result, BaseException):
            raise messages_result
        else:
            messages = messages_result
        data = AllegroData(
            orders=orders,
            cart=cart,
            messages=messages,
            default_pickup_point=self.default_pickup_point,
        )
        return await self._async_auto_read(data)

    def _older_threads(self, data: AllegroData) -> list[MessageThread]:
        """Unread automatic order messages that no longer need attention."""
        days = float(
            self.config_entry.options.get(CONF_AUTO_READ_DAYS) or DEFAULT_AUTO_READ_DAYS
        )
        return data.messages.auto_read_candidates(
            data.active_sellers, days, dt_util.utcnow()
        )

    async def _async_auto_read(self, data: AllegroData) -> AllegroData:
        """Mark automatic order messages as read when they are no longer useful."""
        if not self.config_entry.options.get(CONF_AUTO_READ):
            return data
        candidates = self._older_threads(data)
        read: set[str] = set()
        for thread in candidates[:MAX_AUTO_READ]:
            try:
                await self.api.async_open_thread(thread.id)
            except AllegroApiError as err:
                _LOGGER.warning("Could not mark message as read: %s", err)
                break
            read.add(thread.id)
        if not read:
            return data
        _LOGGER.debug("Marked %d automatic Allegro messages as read", len(read))
        return replace(data, messages=data.messages.with_read(read))

    def _apply_read(self, thread_ids: set[str]) -> None:
        if self.data is None or not thread_ids:
            return
        self.async_set_updated_data(
            replace(self.data, messages=self.data.messages.with_read(thread_ids))
        )

    async def async_open_thread(self, thread_id: str) -> list[Attachment]:
        """Open a thread, which marks it as read, and return its attachments."""
        attachments = await self.api.async_open_thread(thread_id)
        self._apply_read({thread_id})
        return attachments

    async def async_mark_threads_read(self, category: str) -> int:
        """Mark unread threads of a category as read. Returns how many were read."""
        threads = (
            self.data.messages.unread_in_category(category)
            if self.data is not None
            else []
        )
        read: set[str] = set()
        try:
            for thread in threads[:MAX_BULK_READ]:
                await self.api.async_open_thread(thread.id)
                read.add(thread.id)
        finally:
            self._apply_read(read)
        return len(read)

    async def async_mark_older_read(self) -> int:
        """Mark older automatic order messages as read. Returns how many."""
        if self.data is None:
            return 0
        read: set[str] = set()
        try:
            for thread in self._older_threads(self.data)[:MAX_BULK_READ]:
                await self.api.async_open_thread(thread.id)
                read.add(thread.id)
        finally:
            self._apply_read(read)
        return len(read)

    async def async_add_to_cart(self, item_id: str, quantity: int = 1) -> None:
        """Add an offer to the cart and refresh cart state."""
        await self.api.async_add_to_cart(item_id, quantity)
        try:
            cart = await self.api.async_get_cart()
        except AllegroApiError as err:
            _LOGGER.warning("Added to cart but failed to refresh cart: %s", err)
            await self.async_request_refresh()
            return
        if self.data is None:
            await self.async_request_refresh()
            return
        self.async_set_updated_data(replace(self.data, cart=cart))
