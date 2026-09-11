"""Home Assistant services for Allegro."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import AllegroApiError
from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_ITEM_ID,
    ATTR_QUANTITY,
    DOMAIN,
    SERVICE_ADD_TO_CART,
)
from .coordinator import AllegroCoordinator

SERVICE_ADD_TO_CART_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ITEM_ID): vol.All(
            vol.Coerce(str), str.strip, vol.Length(min=1)
        ),
        vol.Optional(ATTR_QUANTITY, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register domain services once."""
    if hass.services.has_service(DOMAIN, SERVICE_ADD_TO_CART):
        return

    async def _add_to_cart(call: ServiceCall) -> ServiceResponse | None:
        coordinator = _async_get_coordinator(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        item_id = call.data[ATTR_ITEM_ID]
        quantity: int = call.data[ATTR_QUANTITY]
        try:
            await coordinator.async_add_to_cart(item_id, quantity)
        except AllegroApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="add_to_cart_failed",
                translation_placeholders={"item_id": item_id, "error": str(err)},
            ) from err
        if not call.return_response:
            return None
        cart = coordinator.data.cart if coordinator.data is not None else None
        return cart.as_attributes() if cart is not None else {"details": []}

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TO_CART,
        _add_to_cart,
        schema=SERVICE_ADD_TO_CART_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


def _async_get_coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> AllegroCoordinator:
    loaded = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if entry_id:
        for entry in loaded:
            if entry.entry_id == entry_id:
                return entry.runtime_data
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_account",
            translation_placeholders={"entry_id": entry_id},
        )
    if len(loaded) == 1:
        return loaded[0].runtime_data
    if not loaded:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_account",
        )
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="multiple_accounts",
    )
