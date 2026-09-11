"""Base entity for Allegro."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_USERNAME, DOMAIN, NAME
from .coordinator import AllegroCoordinator


class AllegroEntity(CoordinatorEntity[AllegroCoordinator]):
    """Coordinator entity bound to one Allegro account."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        username = coordinator.config_entry.data.get(CONF_USERNAME) or ""
        self._user_prefix = f"{username.lower()}_" if username else ""
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"{NAME} {username}".strip() if username else NAME,
            manufacturer="Allegro",
        )
