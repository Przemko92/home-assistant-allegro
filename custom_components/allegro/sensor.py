"""Sensor platform for Allegro."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ICON_DELIVERY, ICON_READY, ICON_TRANSIT, ICON_WAITING
from .coordinator import AllegroConfigEntry, AllegroCoordinator
from .entity import AllegroEntity
from .models import AllegroData, Order


@dataclass(frozen=True, kw_only=True)
class AllegroSensorDescription(SensorEntityDescription):
    """Description of an Allegro orders sensor."""

    orders_fn: Callable[[AllegroData], list[Order]]
    include_pickup: bool = False


SENSORS: tuple[AllegroSensorDescription, ...] = (
    AllegroSensorDescription(
        key="in_progress",
        translation_key="in_progress",
        icon=ICON_WAITING,
        orders_fn=lambda data: data.not_delivered,
        include_pickup=True,
    ),
    AllegroSensorDescription(
        key="waiting_for_pickup",
        translation_key="waiting_for_pickup",
        icon=ICON_READY,
        orders_fn=lambda data: data.waiting_for_pickup,
        include_pickup=True,
    ),
    AllegroSensorDescription(
        key="in_transit",
        translation_key="in_transit",
        icon=ICON_TRANSIT,
        orders_fn=lambda data: data.in_transit,
    ),
    AllegroSensorDescription(
        key="in_delivery",
        translation_key="in_delivery",
        icon=ICON_DELIVERY,
        orders_fn=lambda data: data.in_delivery,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AllegroConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Allegro sensors."""
    async_add_entities(
        AllegroOrdersSensor(entry.runtime_data, description) for description in SENSORS
    )


class AllegroOrdersSensor(AllegroEntity, SensorEntity):
    """Number of orders in a given status, with details as attributes."""

    entity_description: AllegroSensorDescription

    def __init__(
        self,
        coordinator: AllegroCoordinator,
        description: AllegroSensorDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._user_prefix}{description.key}"

    @property
    def native_value(self) -> int:
        """Return the number of matching orders."""
        return len(self._orders)

    @property
    def extra_state_attributes(self) -> dict[str, list[dict[str, Any]]]:
        """Return order details for dashboards."""
        include_pickup = self.entity_description.include_pickup
        return {
            "details": [
                order.as_attributes(include_pickup=include_pickup)
                for order in self._orders
            ]
        }

    @property
    def _orders(self) -> list[Order]:
        data = self.coordinator.data
        if data is None:
            return []
        return self.entity_description.orders_fn(data)
