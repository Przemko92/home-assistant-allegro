"""Service that returns parcel pickup secrets without putting them on entities."""

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.allegro.const import (
    ATTR_SELLER,
    ATTR_WAYBILL,
    DOMAIN,
    SERVICE_GET_PICKUP_CODE,
)
from custom_components.allegro.models import parse_orders

from .test_coordinator import setup, state
from .test_models import SECRET_KEYS, myorder


def orders_with_codes():
    return parse_orders(
        {
            "orderGroups": [
                {
                    "groupId": "g1",
                    "myorders": [
                        myorder(
                            "shop_a",
                            "AVAILABLE_FOR_PICKUP",
                            "W1",
                            "Paczkomat AAA01A",
                            code="111",
                            phone="500100100",
                            qr="qr-a",
                        ),
                        myorder(
                            "shop_b",
                            "IN_TRANSIT",
                            "W2",
                            code="222",
                            phone="500100200",
                            qr="qr-b",
                        ),
                        myorder("shop_d", "PAID", "W4"),
                    ],
                }
            ]
        }
    )


async def _call(hass, data):
    return await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_PICKUP_CODE,
        data,
        blocking=True,
        return_response=True,
    )


async def test_pickup_secrets_come_from_the_service(hass):
    entry, _, patches = await setup(hass, orders_with_codes())
    try:
        for key in ("in_progress", "waiting_for_pickup"):
            details = state(hass, key).attributes["details"]
            assert details
            for row in details:
                assert not set(SECRET_KEYS) & row.keys()
        response = await _call(hass, {})
        by_seller = {row["seller"]: row for row in response["orders"]}
        assert set(by_seller) == {"shop_a", "shop_b"}
        assert by_seller["shop_a"]["pickup_code"] == "111"
        assert by_seller["shop_a"]["receiver_phone_number"] == "500100100"
        assert by_seller["shop_a"]["qr_code"] == "qr-a"
        one = await _call(hass, {ATTR_SELLER: "shop_a", ATTR_WAYBILL: "W1"})
        assert [row["order_id"] for row in one["orders"]] == ["g1"]
        with pytest.raises(ServiceValidationError):
            await _call(hass, {ATTR_WAYBILL: "missing"})
        entry.runtime_data.data = None
        assert await _call(hass, {}) == {"orders": []}
        with pytest.raises(ServiceValidationError):
            await _call(hass, {ATTR_SELLER: "shop_a"})
    finally:
        for patcher in patches:
            patcher.stop()
