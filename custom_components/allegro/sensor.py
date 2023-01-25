"""Sensor platform for allegro_integration."""
from homeassistant.components.sensor import SensorEntity

from . import AllegroDataUpdateCoordinator

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    ICON_WAITING,
    ICON_READY,
    ICON_TRANSIT,
    ICON_DELIVERY,
    SENSOR,
    CONF_USERNAME,
)
from .entity import AllegroEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        [
            WaitingForDeliverySensor(coordinator, entry),
            WaitingForPickupSensor(coordinator, entry),
            InTransitSensor(coordinator, entry),
            InDeliverySensor(coordinator, entry),
        ]
    )


class WaitingForDeliverySensor(AllegroEntity, SensorEntity):
    """WaitingForDelivery Sensor class."""

    def __init__(self, coordinator, config_entry) -> None:
        """Init method"""
        super().__init__(coordinator, config_entry)

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{self.get_user_name}in_progress"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return len(self.get_allegro_data.get_not_delivered_orders)

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.get_user_name}in_progress"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_WAITING

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        orders = self.get_allegro_data.get_not_delivered_orders
        items = []

        for item in orders:
            items.append(
                {
                    "Seller": item.get_seller,
                    "Status": item.get_status.get_current_status,
                    "Offers": list(map(lambda i: i.get_title, item.get_offers)),
                    "tracing_url": item.get_delivery.get_url,
                    "delivery_name": item.get_delivery.get_name,
                    "pickup_code": item.get_delivery.get_pickup_code,
                    "receiver_phone_number": item.get_delivery.get_receiver_phone_number,
                    "qr_code": item.get_delivery.get_qr_code,
                }
            )

        return {
            "details": items,
        }


class WaitingForPickupSensor(AllegroEntity, SensorEntity):
    """WaitingForPickupSensor Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{self.get_user_name}waiting_for_pickup"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return len(self.get_allegro_data.get_waiting_for_pickup)

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.get_user_name}waiting_for_pickup"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_READY

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        orders = self.get_allegro_data.get_waiting_for_pickup
        items = []

        for item in orders:
            items.append(
                {
                    "Seller": item.get_seller,
                    "Status": item.get_status.get_current_status,
                    "Offers": list(map(lambda i: i.get_title, item.get_offers)),
                    "tracing_url": item.get_delivery.get_url,
                    "delivery_name": item.get_delivery.get_name,
                    "pickup_code": item.get_delivery.get_pickup_code,
                    "receiver_phone_number": item.get_delivery.get_receiver_phone_number,
                    "qr_code": item.get_delivery.get_qr_code,
                }
            )

        return {
            "details": items,
        }


class InTransitSensor(AllegroEntity, SensorEntity):
    """InTransit Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{self.get_user_name}in_transit"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return len(self.get_allegro_data.get_in_transit)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_TRANSIT

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.get_user_name}in_transit"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        orders = self.get_allegro_data.get_in_transit
        items = []

        for item in orders:
            items.append(
                {
                    "Seller": item.get_seller,
                    "Status": item.get_status.get_current_status,
                    "Offers": list(map(lambda i: i.get_title, item.get_offers)),
                    "tracing_url": item.get_delivery.get_url,
                    "delivery_name": item.get_delivery.get_name,
                }
            )

        return {
            "details": items,
        }


class InDeliverySensor(AllegroEntity, SensorEntity):
    """InDeliverySensor Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{self.get_user_name}in_delivery"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return len(self.get_allegro_data.get_in_delivery)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_DELIVERY

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.get_user_name}in_delivery"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        orders = self.get_allegro_data.get_in_delivery
        items = []

        for item in orders:
            items.append(
                {
                    "Seller": item.get_seller,
                    "Status": item.get_status.get_current_status,
                    "Offers": list(map(lambda i: i.get_title, item.get_offers)),
                    "tracing_url": item.get_delivery.get_url,
                    "delivery_name": item.get_delivery.get_name,
                }
            )

        return {
            "details": items,
        }
