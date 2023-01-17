"""Adds config flow for home-assistant-allegro."""
import json
import time
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components.http import HomeAssistantView
import aiohttp
from typing import Any
from .api import HomeAssistantAllegroApiClient
from .const import CONF_CLIENT_ID
from .const import CONF_CLIENT_SECRET
from .const import CONF_TOKEN
from .const import DOMAIN
from .const import PLATFORMS


class HomeAssistantAllegroFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for home_assistant_allegro."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._client = None
        self._data = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None and not CONF_TOKEN in user_input:
            return await self.async_step_auth(user_input)

        return await self._show_config_form(user_input)

    async def async_step_auth(self, user_input=None):
        """Handle a flow initialized by the user."""

        if user_input is not None:
            if CONF_TOKEN in user_input:
                self._data = user_input
                return self.async_external_step_done(next_step_id="finish")

            auth_url = await self.get_auth_url(
                user_input[CONF_CLIENT_ID], user_input[CONF_CLIENT_SECRET]
            )

            self.hass.async_create_task(self.get_token(user_input))
            return self.async_external_step(step_id="auth", url=auth_url)

    async def get_token(self, user_input=None):
        if self._client and user_input:
            token = await self._client.await_for_token()

            return await self.hass.config_entries.flow.async_configure(
                flow_id=self.flow_id,
                user_input={
                    CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                    CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                    CONF_TOKEN: token,
                },
            )

    async def async_step_finish(self, user_input=None):
        if self._client and self._data:
            user_info = await self._client.get_user_info()
            return self.async_create_entry(
                title="Allegro " + user_info["login"], data=self._data
            )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HomeAssistantAllegroOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=self._errors,
            last_step=False,
        )

    async def get_auth_url(self, client_id: str, client_secret: str) -> str:
        """Return true if credentials is valid."""

        session = async_create_clientsession(self.hass, verify_ssl=False)
        self._client = HomeAssistantAllegroApiClient(session, client_id, client_secret)
        return await self._client.get_auth_url()


class HomeAssistantAllegroOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for home_assistant_allegro."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self, user_input=None, external_data=None
    ):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None, external_data=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)

        if external_data is not None:
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_CLIENT_ID), data=self.options
        )