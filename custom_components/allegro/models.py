"""Parsed Allegro order and cart models."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

STATUS_DELIVERED = "DELIVERED"
STATUS_RETURNED = "RETURNED"
STATUS_AVAILABLE_FOR_PICKUP = "AVAILABLE_FOR_PICKUP"
STATUS_IN_DELIVERY = "IN_DELIVERY"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_CANCELLED = "ORDER_CANCELLED"
COMPLETED_STATUSES = frozenset({STATUS_DELIVERED, STATUS_RETURNED, STATUS_CANCELLED})


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _money(value: Any) -> tuple[float, str]:
    payload = _as_dict(value)
    try:
        amount = float(payload.get("amount") or 0)
    except TypeError, ValueError:
        amount = 0.0
    return amount, str(payload.get("currency") or "")


@dataclass(frozen=True, slots=True)
class Offer:
    """Single offer inside an order."""

    id: str
    title: str
    unit_price: float
    price_currency: str
    friendly_url: str | None
    quantity: int
    image_url: str | None

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> Offer:
        """Create an offer from an Allegro payload."""
        price = _as_dict(item.get("unitPrice"))
        try:
            amount = float(price.get("amount") or 0)
        except TypeError, ValueError:
            amount = 0.0
        try:
            quantity = int(item.get("quantity") or 0)
        except TypeError, ValueError:
            quantity = 0
        return cls(
            id=str(item.get("id") or ""),
            title=str(item.get("title") or ""),
            unit_price=amount,
            price_currency=str(price.get("currency") or ""),
            friendly_url=item.get("friendlyUrl"),
            quantity=quantity,
            image_url=item.get("imageUrl"),
        )


@dataclass(frozen=True, slots=True)
class Delivery:
    """Delivery / tracking info for an order."""

    name: str | None
    url: str | None
    pickup_code: str | None
    receiver_phone_number: str | None
    qr_code: str | None

    @classmethod
    def from_api(cls, delivery: Any) -> Delivery:
        """Create delivery info from optional Allegro fields."""
        payload = _as_dict(delivery)
        waybills = _as_dict(payload.get("waybillsData")).get("waybills") or []
        waybill = _as_dict(waybills[0] if waybills else None)
        carrier = _as_dict(waybill.get("carrier"))
        pickup = _as_dict(waybill.get("pickupCode"))
        return cls(
            name=payload.get("name"),
            url=carrier.get("url"),
            pickup_code=pickup.get("code"),
            receiver_phone_number=pickup.get("receiverPhoneNumber"),
            qr_code=pickup.get("qrCode"),
        )


@dataclass(frozen=True, slots=True)
class Order:
    """Single Allegro order group."""

    order_id: str
    seller: str
    offers: tuple[Offer, ...]
    order_date: str | None
    status: str
    delivery: Delivery

    @classmethod
    def from_api(cls, group_id: str, item: dict[str, Any]) -> Order:
        """Create an order from a myorders item."""
        seller = _as_dict(item.get("seller"))
        status = _as_dict(_as_dict(item.get("status")).get("primary"))
        return cls(
            order_id=group_id,
            seller=str(seller.get("login") or ""),
            offers=tuple(
                Offer.from_api(_as_dict(offer)) for offer in item.get("offers") or []
            ),
            order_date=item.get("orderDate"),
            status=str(status.get("status") or ""),
            delivery=Delivery.from_api(item.get("delivery")),
        )

    def as_attributes(self, *, include_pickup: bool = False) -> dict[str, Any]:
        """State attributes kept compatible with existing dashboards."""
        attributes: dict[str, Any] = {
            "Seller": self.seller,
            "Status": self.status,
            "Offers": [offer.title for offer in self.offers],
            "tracing_url": self.delivery.url,
            "delivery_name": self.delivery.name,
        }
        if include_pickup:
            attributes["pickup_code"] = self.delivery.pickup_code
            attributes["receiver_phone_number"] = self.delivery.receiver_phone_number
            attributes["qr_code"] = self.delivery.qr_code
        return attributes


@dataclass(frozen=True, slots=True)
class CartItem:
    """Single line in the Allegro cart."""

    offer_id: str
    name: str
    url: str | None
    photo_url: str | None
    quantity: int
    unit_price: float
    price: float
    currency: str
    seller: str
    selected: bool

    @classmethod
    def from_api(cls, item: dict[str, Any], seller: str) -> CartItem:
        """Create a cart line from an Allegro cart item payload."""
        offers = item.get("offers") or []
        primary: dict[str, Any] | None = None
        for offer in offers:
            offer = _as_dict(offer)
            if offer.get("primary"):
                primary = offer
                break
        if primary is None and offers:
            primary = _as_dict(offers[0])
        offer = primary or {}
        unit_price, unit_currency = _money(offer.get("price") or item.get("unitPrice"))
        price, currency = _money(item.get("price"))
        quantity = _as_dict(item.get("quantity"))
        try:
            selected_qty = int(quantity.get("selected") or 0)
        except TypeError, ValueError:
            selected_qty = 0
        photo = _as_dict(_as_dict(offer.get("photo")).get("small")).get("url")
        return cls(
            offer_id=str(offer.get("id") or ""),
            name=str(offer.get("name") or ""),
            url=offer.get("url"),
            photo_url=photo if isinstance(photo, str) else None,
            quantity=selected_qty,
            unit_price=unit_price,
            price=price,
            currency=currency or unit_currency,
            seller=seller,
            selected=bool(item.get("selected", True)),
        )

    def as_attributes(self) -> dict[str, Any]:
        """State attributes for dashboards."""
        return {
            "offer_id": self.offer_id,
            "name": self.name,
            "quantity": self.quantity,
            "price": self.price,
            "unit_price": self.unit_price,
            "currency": self.currency,
            "seller": self.seller,
            "url": self.url,
            "photo_url": self.photo_url,
            "selected": self.selected,
        }


@dataclass(frozen=True, slots=True)
class Cart:
    """Shopping cart snapshot."""

    id: str | None
    items: tuple[CartItem, ...]
    total: float
    currency: str

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    @classmethod
    def empty(cls) -> Cart:
        """Empty cart used when the cart endpoint is unavailable."""
        return cls(id=None, items=(), total=0.0, currency="")

    def as_attributes(self) -> dict[str, Any]:
        """State attributes kept compatible with existing dashboards."""
        return {
            "total": self.total,
            "currency": self.currency,
            "details": [item.as_attributes() for item in self.items],
        }


@dataclass(frozen=True, slots=True)
class AllegroData:
    """Cached order lists and cart for sensors."""

    orders: list[Order]
    cart: Cart

    def by_status(self, *statuses: str) -> list[Order]:
        """Orders whose primary status is one of the given values."""
        wanted = set(statuses)
        return [order for order in self.orders if order.status in wanted]

    @property
    def not_delivered(self) -> list[Order]:
        return [
            order for order in self.orders if order.status not in COMPLETED_STATUSES
        ]

    @property
    def waiting_for_pickup(self) -> list[Order]:
        return self.by_status(STATUS_AVAILABLE_FOR_PICKUP)

    @property
    def in_transit(self) -> list[Order]:
        return self.by_status(STATUS_IN_TRANSIT)

    @property
    def in_delivery(self) -> list[Order]:
        return self.by_status(STATUS_IN_DELIVERY)


def parse_cart(payload: dict[str, Any]) -> Cart:
    """Parse `/cart` JSON into a cart model."""
    cart = _as_dict(payload.get("cart"))
    items: list[CartItem] = []
    for group in cart.get("groups") or []:
        group = _as_dict(group)
        seller = str(_as_dict(group.get("seller")).get("login") or "")
        for raw_item in group.get("items") or []:
            try:
                items.append(CartItem.from_api(_as_dict(raw_item), seller))
            except (KeyError, TypeError, ValueError) as err:
                _LOGGER.warning("Skipping Allegro cart item: %s", err)
    total, currency = _money(_as_dict(cart.get("prices")).get("total"))
    return Cart(
        id=str(cart.get("id") or "") or None,
        items=tuple(items),
        total=total,
        currency=currency,
    )


def parse_orders(payload: dict[str, Any]) -> list[Order]:
    """Parse `/myorders` JSON into order models."""
    orders: list[Order] = []
    for group in payload.get("orderGroups") or []:
        group = _as_dict(group)
        myorders = group.get("myorders") or []
        if not myorders:
            continue
        group_id = str(group.get("groupId") or "")
        try:
            orders.append(Order.from_api(group_id, _as_dict(myorders[0])))
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Skipping Allegro order group %s: %s", group_id, err)
    return orders
