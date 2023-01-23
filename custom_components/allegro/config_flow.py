"""Adds config flow for Allegro."""
import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol

from .api import AllegroApiClient
from .const import (
    CONF_COOKIE,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class AllegroFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Allegro."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            login = await self._test_credentials(user_input[CONF_COOKIE])
            if login:
                if user_input[CONF_USERNAME]:
                    return self.async_create_entry(
                        title="Allegro " + user_input[CONF_USERNAME], data=user_input
                    )
                user_input[CONF_USERNAME] = login
                return self.async_create_entry(
                    title="Allegro " + login, data=user_input
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_COOKIE] = ""
        user_input[CONF_USERNAME] = ""

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AllegroOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COOKIE, default=user_input[CONF_COOKIE]): str,
                    vol.Optional(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, cookie):
        """Return true if credentials is valid."""
        try:
            session = async_create_clientsession(self.hass)
            client = AllegroApiClient(cookie, session)
            result = await client.get_user_info()
            return result.get_login
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error while testing credentials %s",
                exception,
            )

            pass
        return False


class AllegroOptionsFlowHandler(config_entries.OptionsFlow):
    """Allegro config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_COOKIE, default=self.config_entry.data[CONF_COOKIE]
                    ): str,
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        self.options[CONF_USERNAME] = self.config_entry.data[CONF_USERNAME]

        return self.async_create_entry(
            title="Allegro " + self.options[CONF_USERNAME], data=self.options
        )
