"""Adds config flow for Allegro."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from ha_browser_companion import CompanionLoginFlow, CompanionStart, captured_cookie
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import AllegroApiClient
from .const import (
    ALLEGRO_ORDERS_URL,
    ALLEGRO_START_URL,
    COMPANION_WAIT,
    CONF_COOKIE,
    CONF_METHOD,
    CONF_USERNAME,
    DOMAIN,
    METHOD_COMPANION,
    METHOD_COOKIE,
)

_URL_PLACEHOLDERS = {
    "allegro_url": ALLEGRO_START_URL,
    "orders_url": ALLEGRO_ORDERS_URL,
}

_LOGGER: logging.Logger = logging.getLogger(__package__)


class AllegroFlowHandler(CompanionLoginFlow, config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Allegro."""

    VERSION = 1
    companion_client_id = DOMAIN

    def __init__(self):
        """Initialize."""
        self._errors: dict[str, str] = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        if not self.companion_supervisor_present():
            return await self.async_step_cookie()
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_METHOD, default=METHOD_COMPANION
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=[METHOD_COMPANION, METHOD_COOKIE],
                                mode=SelectSelectorMode.LIST,
                                translation_key="method",
                            )
                        ),
                    }
                ),
            )
        if user_input.get(CONF_METHOD) == METHOD_COOKIE:
            return await self.async_step_cookie()
        return await self.async_step_companion()

    async def async_step_cookie(self, user_input=None):
        """Paste QXLSESSID (legacy flow)."""
        self._errors = {}
        if user_input is not None:
            login = await self._test_credentials(user_input[CONF_COOKIE])
            if login:
                return self._create_entry(
                    user_input[CONF_COOKIE],
                    user_input.get(CONF_USERNAME) or login,
                )
            self._errors["base"] = "auth"
            return await self._show_cookie_form(user_input)

        return await self._show_cookie_form({CONF_COOKIE: "", CONF_USERNAME: ""})

    async def async_companion_start(self) -> CompanionStart:
        return CompanionStart(start_url=ALLEGRO_START_URL, wait=COMPANION_WAIT)

    async def async_companion_finish(self, captured: dict[str, Any]):
        cookie = captured_cookie(captured, CONF_COOKIE)
        if not cookie:
            return await self.async_step_companion_failed()
        login = await self._test_credentials(cookie)
        if not login:
            return await self.async_step_companion_failed()
        return self._create_entry(cookie, login)

    def _companion_placeholders(self) -> dict[str, str]:
        """Companion links plus Allegro URLs used in translations."""
        return {**super()._companion_placeholders(), **_URL_PLACEHOLDERS}

    def _create_entry(self, cookie: str, username: str):
        return self.async_create_entry(
            title="Allegro " + username,
            data={CONF_COOKIE: cookie, CONF_USERNAME: username},
        )

    @staticmethod
    @callback
    def async_get_options_flow(_config_entry):
        return AllegroOptionsFlowHandler()

    async def _show_cookie_form(self, user_input):
        """Show the configuration form to paste QXLSESSID."""
        return self.async_show_form(
            step_id="cookie",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COOKIE, default=user_input[CONF_COOKIE]): str,
                    vol.Optional(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                }
            ),
            errors=self._errors,
            description_placeholders=_URL_PLACEHOLDERS,
        )

    async def _test_credentials(self, cookie: str) -> str | None:
        """Return login if credentials are valid."""
        return await _async_test_credentials(self.hass, cookie)


async def _async_test_credentials(hass, cookie: str) -> str | None:
    """Return Allegro login when QXLSESSID is valid."""
    try:
        client = AllegroApiClient(cookie, async_get_clientsession(hass))
        return await client.async_get_login()
    except Exception as exception:  # pylint: disable=broad-except
        _LOGGER.error("Error while testing credentials: %s", exception)
        return None


class AllegroOptionsFlowHandler(config_entries.OptionsFlow):
    """Update the stored QXLSESSID cookie."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            cookie = user_input[CONF_COOKIE].strip()
            login = await _async_test_credentials(self.hass, cookie)
            if login:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, CONF_COOKIE: cookie},
                )
                return self.async_create_entry(title="", data={})
            errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_COOKIE, default=self.config_entry.data[CONF_COOKIE]
                    ): str,
                }
            ),
            errors=errors,
        )
