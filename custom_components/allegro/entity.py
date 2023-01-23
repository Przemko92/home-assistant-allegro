"""AllegroEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USERNAME
from .data import AllegroData


class AllegroEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def get_allegro_data(self) -> AllegroData:
        return self.coordinator.data

    @property
    def get_user_name(self) -> str:
        if self.config_entry.data[CONF_USERNAME]:
            return f"{self.config_entry.data[CONF_USERNAME].lower()}_"
        else:
            return ""
