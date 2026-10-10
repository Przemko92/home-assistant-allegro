"""Home Assistant services for Allegro."""

from __future__ import annotations

from pathlib import Path

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
from homeassistant.util import slugify

from .api import AllegroApiError
from .const import (
    ATTR_CATEGORY,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DIRECTORY,
    ATTR_ITEM_ID,
    ATTR_QUANTITY,
    ATTR_THREAD_ID,
    DOMAIN,
    SERVICE_ADD_TO_CART,
    SERVICE_DOWNLOAD_INVOICE,
    SERVICE_MARK_MESSAGE_READ,
    SERVICE_MARK_MESSAGES_READ,
)
from .coordinator import AllegroCoordinator
from .messages import CATEGORIES, CATEGORY_ORDER_STATUS

INVOICE_DIRECTORY = "allegro_invoices"
ATTACHMENT_SUFFIXES = frozenset({".pdf", ".xml", ".jpg", ".jpeg", ".png"})
THREAD_ID_SCHEMA = vol.All(
    vol.Coerce(str), str.strip, cv.matches_regex(r"^[A-Za-z0-9_-]{1,128}$")
)

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

SERVICE_MARK_MESSAGE_READ_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_THREAD_ID): THREAD_ID_SCHEMA,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)
SERVICE_MARK_MESSAGES_READ_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CATEGORY, default=CATEGORY_ORDER_STATUS): vol.In(CATEGORIES),
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)
SERVICE_DOWNLOAD_INVOICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_THREAD_ID): THREAD_ID_SCHEMA,
        vol.Optional(ATTR_DIRECTORY): cv.string,
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

    async def _mark_message_read(call: ServiceCall) -> None:
        coordinator = _async_get_coordinator(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        try:
            await coordinator.async_open_thread(call.data[ATTR_THREAD_ID])
        except AllegroApiError as err:
            raise _mark_read_failed(err) from err

    async def _mark_messages_read(call: ServiceCall) -> ServiceResponse | None:
        coordinator = _async_get_coordinator(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        try:
            count = await coordinator.async_mark_threads_read(call.data[ATTR_CATEGORY])
        except AllegroApiError as err:
            raise _mark_read_failed(err) from err
        return {"marked_read": count} if call.return_response else None

    async def _download_invoice(call: ServiceCall) -> ServiceResponse | None:
        coordinator = _async_get_coordinator(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        thread_id: str = call.data[ATTR_THREAD_ID]
        directory = Path(
            call.data.get(ATTR_DIRECTORY) or hass.config.path(INVOICE_DIRECTORY)
        )
        if not hass.config.is_allowed_path(str(directory)):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="directory_not_allowed",
                translation_placeholders={"directory": str(directory)},
            )
        thread = coordinator.data.messages.get(thread_id) if coordinator.data else None
        try:
            attachments = await coordinator.async_open_thread(thread_id)
            if not attachments:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="no_attachment",
                )
            files: list[tuple[str, bytes]] = []
            for index, attachment in enumerate(attachments, start=1):
                suffix = Path(attachment.file_name).suffix.lower()
                if suffix not in ATTACHMENT_SUFFIXES:
                    suffix = ".pdf"
                prefix = (thread.timestamp or "")[:10] if thread else ""
                seller = thread.seller if thread else thread_id
                name = slugify(f"{prefix} {seller} {index}") + suffix
                files.append(
                    (
                        name,
                        await coordinator.api.async_download_attachment(attachment.url),
                    )
                )
        except AllegroApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="download_failed",
                translation_placeholders={"thread_id": thread_id, "error": str(err)},
            ) from err
        paths = await hass.async_add_executor_job(_write_files, directory, files)
        return {"files": paths} if call.return_response else None

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TO_CART,
        _add_to_cart,
        schema=SERVICE_ADD_TO_CART_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_MESSAGE_READ,
        _mark_message_read,
        schema=SERVICE_MARK_MESSAGE_READ_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_MESSAGES_READ,
        _mark_messages_read,
        schema=SERVICE_MARK_MESSAGES_READ_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DOWNLOAD_INVOICE,
        _download_invoice,
        schema=SERVICE_DOWNLOAD_INVOICE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


def _mark_read_failed(err: AllegroApiError) -> HomeAssistantError:
    return HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="mark_read_failed",
        translation_placeholders={"error": str(err)},
    )


def _write_files(directory: Path, files: list[tuple[str, bytes]]) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, data in files:
        path = directory / name
        path.write_bytes(data)
        paths.append(str(path))
    return paths


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
