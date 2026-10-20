"""Order and package parsing, built from synthetic Allegro payloads."""

from datetime import UTC, datetime, timedelta

from custom_components.allegro.models import (
    STATUS_DELIVERED,
    AllegroData,
    Cart,
    Package,
    parse_deadline,
    parse_orders,
    parse_packages,
)

SECRET_KEYS = ("pickup_code", "receiver_phone_number", "qr_code")


def myorder(seller, status, waybill=None, point=None, code=None, phone=None, qr=None):
    delivery = {}
    bill = {}
    if waybill:
        bill["waybillId"] = waybill
        bill["carrier"] = {"url": "https://t/x"}
    if any(value is not None for value in (code, phone, qr)):
        bill["pickupCode"] = {
            "code": code,
            "receiverPhoneNumber": phone,
            "qrCode": qr,
        }
    if bill:
        delivery["waybillsData"] = {"waybills": [bill]}
    if point:
        delivery["generalDelivery"] = {
            "id": "1",
            "name": point,
            "address": {"street": "Polna 1", "code": "00-001", "city": "Warszawa"},
        }
    return {
        "seller": {"login": seller},
        "offers": [{"id": "1", "title": f"Item from {seller}", "quantity": 1}],
        "status": {"primary": {"status": status}},
        "delivery": delivery,
    }


def test_every_order_of_a_checkout_is_parsed():
    payload = {
        "orderGroups": [
            {
                "groupId": "g1",
                "myorders": [
                    myorder("shop_a", "AVAILABLE_FOR_PICKUP", "W1", "Paczkomat AAA01A"),
                    myorder("shop_b", "IN_TRANSIT", "W2"),
                ],
            },
            {"groupId": "g2", "myorders": [myorder("shop_c", "DELIVERED", "W3")]},
            {"groupId": "g3", "myorders": []},
        ]
    }
    orders = parse_orders(payload)
    assert [(o.seller, o.status, o.order_id) for o in orders] == [
        ("shop_a", "AVAILABLE_FOR_PICKUP", "g1"),
        ("shop_b", "IN_TRANSIT", "g1"),
        ("shop_c", "DELIVERED", "g2"),
    ]
    data = AllegroData(orders=orders, cart=Cart.empty())
    assert [o.seller for o in data.waiting_for_pickup] == ["shop_a"]
    assert [o.seller for o in data.in_transit] == ["shop_b"]
    assert orders[0].delivery.waybill_ids == ("W1",)


def test_broken_order_is_skipped_not_the_whole_checkout():
    payload = {
        "orderGroups": [
            {
                "groupId": "g1",
                "myorders": [myorder("ok", "PAID"), "junk", myorder("ok2", "PAID")],
            }
        ]
    }
    assert [o.seller for o in parse_orders(payload)] == ["ok", "ok2"]


def test_parcels_without_an_order_still_set_the_pickup_deadline():
    soon = datetime.now(UTC) + timedelta(days=2)
    later = datetime.now(UTC) + timedelta(days=4)
    orders = parse_orders(
        {
            "orderGroups": [
                {
                    "groupId": "g",
                    "myorders": [myorder("a", "AVAILABLE_FOR_PICKUP", "W1")],
                }
            ]
        }
    )
    data = AllegroData(
        orders=orders,
        cart=Cart.empty(),
        packages=(
            Package("W1", None, None, later, None, None),
            Package("WX", None, None, soon, "Do odbioru", None),  # no order owns it
            Package(
                "WR", None, "FAILED", None, "Odesłano", None
            ),  # returned: no deadline
        ),
    )
    assert [p.waybill for p in data.unmatched_packages] == ["WX", "WR"]
    assert [p.waybill for p in data.pending_unmatched] == ["WX"]
    assert data.next_pickup_deadline == soon


def test_old_unmatched_deadlines_are_ignored():
    past = datetime.now(UTC) - timedelta(days=3)
    data = AllegroData(
        orders=[],
        cart=Cart.empty(),
        packages=(Package("WX", None, None, past, None, None),),
    )
    assert data.next_pickup_deadline is None


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
                        myorder(
                            "shop_c",
                            STATUS_DELIVERED,
                            "W3",
                            code="333",
                            phone="500100300",
                            qr="qr-c",
                        ),
                        myorder("shop_d", "PAID", "W4"),
                    ],
                }
            ]
        }
    )


def test_pickup_secrets_stay_out_of_state_attributes():
    order = orders_with_codes()[0]
    assert order.delivery.pickup_code == "111"
    assert order.delivery.receiver_phone_number == "500100100"
    assert order.delivery.qr_code == "qr-a"
    assert order.delivery.has_pickup_secret
    attrs = order.as_attributes()
    assert not set(SECRET_KEYS) & attrs.keys()
    pickup = order.as_pickup()
    assert pickup["pickup_code"] == "111"
    assert pickup["receiver_phone_number"] == "500100100"
    assert pickup["qr_code"] == "qr-a"
    assert pickup["seller"] == "shop_a"
    assert pickup["waybills"] == ["W1"]
    assert pickup["pickup_point_name"] == "Paczkomat AAA01A"


def test_pickup_details_filter():
    data = AllegroData(orders=orders_with_codes(), cart=Cart.empty())
    assert [row["seller"] for row in data.pickup_details()] == ["shop_a", "shop_b"]
    assert [row["seller"] for row in data.pickup_details(seller=" Shop_A ")] == [
        "shop_a"
    ]
    assert data.pickup_details(waybill=" W3 ")[0]["pickup_code"] == "333"
    assert data.pickup_details(seller="shop_a", waybill="W1")[0]["qr_code"] == "qr-a"
    assert data.pickup_details(seller="shop_a", waybill="W2") == []
    assert data.pickup_details(seller="shop_d")[0]["pickup_code"] is None
    assert data.pickup_details(seller="missing") == []
    assert data.pickup_details(waybill="missing") == []


def test_deadline_formats_and_package_list():
    assert parse_deadline("2026-10-13T15:00:00Z") == datetime(
        2026, 10, 13, 15, tzinfo=UTC
    )
    assert parse_deadline("2026-10-13").hour == 23
    assert parse_deadline(1791900000000).year == 2026
    assert all(parse_deadline(x) is None for x in (None, "", 0, "garbage", True))
    packages = parse_packages(
        {
            "packages": [
                {
                    "delivery": {
                        "waybill": "W1",
                        "carrierId": "X",
                        "status": "READY",
                        "pickup": {"validTo": "2026-10-13T15:00:00Z"},
                        "description": {"title": "t", "subtitle": "s"},
                    }
                },
                {"delivery": {"carrierId": "X"}},
                "junk",
            ]
        }
    )
    assert [p.waybill for p in packages] == ["W1"] and packages[0].valid_to.day == 13
