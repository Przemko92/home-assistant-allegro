"""Sensor platform for Allegro."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ICON_CART,
    ICON_DELIVERY,
    ICON_INVOICE,
    ICON_MESSAGES,
    ICON_OTHER_POINT,
    ICON_READY,
    ICON_TRANSIT,
    ICON_WAITING,
)
from .coordinator import AllegroConfigEntry, AllegroCoordinator
from .entity import AllegroEntity
from .messages import CATEGORY_ORDER_STATUS, MessageThread
from .models import AllegroData, Cart, Order

MAX_LISTED_THREADS = 30


@dataclass(frozen=True, kw_only=True)
class AllegroSensorDescription(SensorEntityDescription):
    """Description of an Allegro orders sensor."""

    orders_fn: Callable[[AllegroData], list[Order]]
    include_pickup: bool = False
    needs_default_pickup_point: bool = False


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
        key="waiting_other_pickup_point",
        translation_key="waiting_other_pickup_point",
        icon=ICON_OTHER_POINT,
        orders_fn=lambda data: data.waiting_other_pickup_point,
        include_pickup=True,
        needs_default_pickup_point=True,
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
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(
                AllegroOrdersSensor(coordinator, description)
                for description in SENSORS
                if coordinator.default_pickup_point
                or not description.needs_default_pickup_point
            ),
            AllegroCartSensor(coordinator),
            AllegroPickupDeadlineSensor(coordinator),
            AllegroMessagesSensor(coordinator),
            AllegroInvoicesSensor(coordinator),
        ]
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
        default_point = self.coordinator.default_pickup_point
        return {
            "details": [
                order.as_attributes(
                    include_pickup=include_pickup,
                    default_pickup_point=default_point,
                    package=self._package_for(order),
                )
                for order in self._orders
            ]
        }

    def _package_for(self, order: Order):
        data = self.coordinator.data
        return data.package_for(order) if data is not None else None

    @property
    def _orders(self) -> list[Order]:
        data = self.coordinator.data
        if data is None:
            return []
        return self.entity_description.orders_fn(data)


class AllegroCartSensor(AllegroEntity, SensorEntity):
    """Number of items in the Allegro cart, with details as attributes."""

    _attr_translation_key = "cart"
    _attr_icon = ICON_CART

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._user_prefix}cart"

    @property
    def native_value(self) -> int:
        """Return the number of pieces in the cart."""
        cart = self._cart
        return 0 if cart is None else cart.item_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return cart details for dashboards."""
        cart = self._cart
        if cart is None:
            return {"details": [], "total": 0, "currency": ""}
        return cart.as_attributes()

    @property
    def _cart(self) -> Cart | None:
        data = self.coordinator.data
        if data is None:
            return None
        return data.cart


class AllegroMessagesSensor(AllegroEntity, SensorEntity):
    """Unread message counter, with the unread threads as attributes."""

    _attr_translation_key = "messages_unread"
    _attr_icon = ICON_MESSAGES

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._user_prefix}messages_unread"

    @property
    def native_value(self) -> int:
        """Return the number of unread message threads."""
        data = self.coordinator.data
        return 0 if data is None else data.messages.unread

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return unread threads for dashboards."""
        data = self.coordinator.data
        threads: list[MessageThread] = (
            [] if data is None else data.messages.unread_threads
        )
        return {
            "automatic": sum(1 for t in threads if t.category == CATEGORY_ORDER_STATUS),
            "details": [t.as_attributes() for t in threads[:MAX_LISTED_THREADS]],
        }


class AllegroInvoicesSensor(AllegroEntity, SensorEntity):
    """Messages in which a seller sent an invoice or other sales document."""

    _attr_translation_key = "invoices"
    _attr_icon = ICON_INVOICE

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._user_prefix}invoices"

    @property
    def native_value(self) -> int:
        """Return the number of recent threads that contain an invoice."""
        data = self.coordinator.data
        return 0 if data is None else len(data.messages.invoices)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return invoice threads for dashboards and `allegro.download_invoice`."""
        data = self.coordinator.data
        threads = [] if data is None else data.messages.invoices
        return {"details": [t.as_attributes() for t in threads[:MAX_LISTED_THREADS]]}


class AllegroPickupDeadlineSensor(AllegroEntity, SensorEntity):
    """The earliest deadline for collecting a parcel that is waiting."""

    _attr_translation_key = "pickup_deadline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._user_prefix}pickup_deadline"

    @property
    def native_value(self):
        """Return the nearest pickup deadline, or None when nothing waits."""
        data = self.coordinator.data
        return None if data is None else data.next_pickup_deadline

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return every waiting parcel with its deadline, nearest first."""
        data = self.coordinator.data
        if data is None:
            return {"details": []}
        rows = []
        for order in data.waiting_for_pickup:
            package = data.package_for(order)
            deadline = package.valid_to if package else None
            rows.append(
                {
                    "seller": order.seller,
                    "offers": [offer.title for offer in order.offers],
                    "pickup_point_name": order.delivery.pickup_point_name,
                    "pickup_point_address": order.delivery.pickup_point_address,
                    "pickup_deadline": deadline.isoformat() if deadline else None,
                }
            )
        rows.sort(
            key=lambda row: (row["pickup_deadline"] is None, row["pickup_deadline"])
        )
        return {"details": rows}
