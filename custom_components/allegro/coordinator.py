"""Data update coordinator for Allegro."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AllegroApiClient, AllegroApiError
from .const import DOMAIN
from .models import AllegroData, Cart

_LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(minutes=30)

type AllegroConfigEntry = ConfigEntry["AllegroCoordinator"]


class AllegroCoordinator(DataUpdateCoordinator[AllegroData]):
    """Fetch and cache Allegro orders and cart."""

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

    async def _async_update_data(self) -> AllegroData:
        """Fetch orders and cart from Allegro."""
        orders, cart_result = await asyncio.gather(
            self.api.async_get_orders(),
            self.api.async_get_cart(),
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
        return AllegroData(orders=orders, cart=cart)

    async def async_add_to_cart(self, item_id: str, quantity: int = 1) -> None:
        """Add an offer to the cart and refresh cart state."""
        await self.api.async_add_to_cart(item_id, quantity)
        try:
            cart = await self.api.async_get_cart()
        except AllegroApiError as err:
            _LOGGER.warning("Added to cart but failed to refresh cart: %s", err)
            await self.async_request_refresh()
            return
        orders = self.data.orders if self.data is not None else []
        self.async_set_updated_data(AllegroData(orders=orders, cart=cart))
