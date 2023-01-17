"""Sensor platform for home-assistant-allegro."""
from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import SENSOR
from .entity import HomeAssistantAllegroEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([HomeAssistantAllegroSensor(coordinator, entry)])


class HomeAssistantAllegroSensor(HomeAssistantAllegroEntity):
    """home_assistant_allegro Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"sensor.{DEFAULT_NAME}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "allegro_custom_device_class"
