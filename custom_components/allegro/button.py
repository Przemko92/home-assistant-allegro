"""Button platform for Allegro."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import AllegroApiError
from .const import DOMAIN, ICON_MARK_READ
from .coordinator import AllegroConfigEntry, AllegroCoordinator
from .entity import AllegroEntity
from .messages import CATEGORY_ORDER_STATUS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AllegroConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Allegro buttons."""
    async_add_entities([AllegroMarkAutomaticReadButton(entry.runtime_data)])


class AllegroMarkAutomaticReadButton(AllegroEntity, ButtonEntity):
    """Mark automatic order status messages as read."""

    _attr_translation_key = "mark_automatic_read"
    _attr_icon = ICON_MARK_READ

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._user_prefix}mark_automatic_read"

    async def async_press(self) -> None:
        """Mark unread automatic order messages as read."""
        try:
            await self.coordinator.async_mark_threads_read(CATEGORY_ORDER_STATUS)
        except AllegroApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="mark_read_failed",
                translation_placeholders={"error": str(err)},
            ) from err
