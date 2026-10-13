"""Re-authentication replaces the cookie of the existing entry."""

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_reauth_with_a_new_cookie(hass):
    entry = MockConfigEntry(
        domain="allegro", data={"QXLSESSID": "old", "user_name": "u"}
    )
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.allegro.async_setup_entry", AsyncMock(return_value=True)
        ),
        patch(
            "custom_components.allegro.config_flow._async_test_credentials",
            AsyncMock(return_value="u"),
        ),
    ):
        entry.async_start_reauth(hass)
        await hass.async_block_till_done()
        flow = hass.config_entries.flow.async_progress_by_handler("allegro")[0]
        assert flow["context"]["source"] == "reauth" and flow["step_id"] == "cookie"
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], {"QXLSESSID": "new", "user_name": ""}
        )
        await hass.async_block_till_done()
    assert result["type"] == "abort" and result["reason"] == "reauth_successful"
    assert entry.data["QXLSESSID"] == "new" and entry.data["user_name"] == "u"
    assert not hass.config_entries.flow.async_progress_by_handler("allegro")
