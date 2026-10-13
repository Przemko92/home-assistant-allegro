"""Coordinator behaviour: sensors, session expiry and the re-authentication prompt."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.allegro.api import AllegroAuthError
from custom_components.allegro.messages import Messages
from custom_components.allegro.models import Cart, Package, parse_orders

from .test_models import myorder

TARGET = "custom_components.allegro.api.AllegroApiClient"


def two_parcel_checkout():
    return parse_orders(
        {
            "orderGroups": [
                {
                    "groupId": "g1",
                    "myorders": [
                        myorder(
                            "shop_a", "AVAILABLE_FOR_PICKUP", "W1", "Paczkomat AAA01A"
                        ),
                        myorder(
                            "shop_b", "AVAILABLE_FOR_PICKUP", "W2", "Paczkomat BBB02B"
                        ),
                    ],
                }
            ]
        }
    )


async def setup(hass, orders=None, packages=()):
    entry = MockConfigEntry(domain="allegro", data={"QXLSESSID": "x", "user_name": "u"})
    entry.add_to_hass(hass)
    mocks = {
        "async_get_orders": AsyncMock(
            return_value=orders if orders is not None else two_parcel_checkout()
        ),
        "async_get_cart": AsyncMock(return_value=Cart.empty()),
        "async_get_messages": AsyncMock(return_value=Messages()),
        "async_get_packages": AsyncMock(return_value=list(packages)),
    }
    patches = [patch(f"{TARGET}.{name}", mock) for name, mock in mocks.items()]
    for p in patches:
        p.start()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, mocks, patches


def state(hass, key):
    ent = er.async_get(hass).async_get_entity_id("sensor", "allegro", f"u_{key}")
    return hass.states.get(ent)


async def test_both_parcels_of_one_checkout_are_counted(hass):
    _entry, _, patches = await setup(hass)
    try:
        assert state(hass, "waiting_for_pickup").state == "2"
        sellers = [
            d["Seller"] for d in state(hass, "waiting_for_pickup").attributes["details"]
        ]
        assert sellers == ["shop_a", "shop_b"]
    finally:
        [p.stop() for p in patches]


async def test_pickup_deadline_and_unmatched_parcel(hass):
    soon = datetime.now(UTC) + timedelta(days=1)
    _entry, _, patches = await setup(
        hass,
        packages=[
            Package("W1", None, None, soon + timedelta(days=2), None, None),
            Package("WX", None, None, soon, "Do odbioru", None),
        ],
    )
    try:
        sensor = state(hass, "pickup_deadline")
        assert datetime.fromisoformat(sensor.state) == soon.replace(microsecond=0)
        rows = sensor.attributes["details"]
        # nearest first: the unmatched parcel, then shop_a, then shop_b (no tracking data)
        assert [r["seller"] for r in rows] == ["przesyłka WX", "shop_a", "shop_b"]
        assert rows[0]["unmatched"] is True and "unmatched" not in rows[1]
        assert rows[1]["pickup_deadline"] and rows[2]["pickup_deadline"] is None
    finally:
        [p.stop() for p in patches]


async def test_last_successful_update_sensor(hass):
    _entry, _, patches = await setup(hass)
    try:
        stamp = datetime.fromisoformat(state(hass, "last_update").state)
        assert abs((datetime.now(UTC) - stamp).total_seconds()) < 60
    finally:
        [p.stop() for p in patches]


def reauth_flows(hass):
    return [
        f
        for f in hass.config_entries.flow.async_progress_by_handler("allegro")
        if f["context"]["source"] == "reauth"
    ]


async def test_dead_session_at_startup_asks_for_a_new_login_at_once(hass):
    entry = MockConfigEntry(domain="allegro", data={"QXLSESSID": "x", "user_name": "u"})
    entry.add_to_hass(hass)
    with (
        patch(
            f"{TARGET}.async_get_orders",
            AsyncMock(side_effect=AllegroAuthError("HTTP 401")),
        ),
        patch(f"{TARGET}.async_get_cart", AsyncMock(return_value=Cart.empty())),
        patch(f"{TARGET}.async_get_messages", AsyncMock(return_value=Messages())),
        patch(f"{TARGET}.async_get_packages", AsyncMock(return_value=[])),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert len(reauth_flows(hass)) == 1


async def test_running_integration_tolerates_two_auth_errors_but_not_three(hass):
    entry, mocks, patches = await setup(hass)
    coordinator = entry.runtime_data
    try:
        mocks["async_get_orders"].side_effect = AllegroAuthError("HTTP 403")
        for _ in range(2):
            await coordinator.async_refresh()
            assert not coordinator.last_update_success and not reauth_flows(hass)
        assert (
            state(hass, "waiting_for_pickup") is not None
        )  # entities stay, only unavailable
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert len(reauth_flows(hass)) == 1
    finally:
        [p.stop() for p in patches]


async def test_a_good_refresh_resets_the_auth_failure_count(hass):
    entry, mocks, patches = await setup(hass)
    coordinator = entry.runtime_data
    try:
        good = mocks["async_get_orders"].return_value
        for _ in range(2):
            mocks["async_get_orders"].side_effect = AllegroAuthError("HTTP 403")
            await coordinator.async_refresh()
            mocks["async_get_orders"].side_effect = None
            mocks["async_get_orders"].return_value = good
            await coordinator.async_refresh()
        assert coordinator.last_update_success and not reauth_flows(hass)
    finally:
        [p.stop() for p in patches]
