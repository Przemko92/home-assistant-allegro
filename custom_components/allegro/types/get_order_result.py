from typing import Any


class GetOrdersResult:
    """Result of get_orders method"""

    def __init__(self, items: dict) -> None:
        """Init method"""
        iterator = map(self.get_order, items["orderGroups"])
        self._orders = list(iterator)

    def get_order(self, item: Any):
        """Returns single order"""
        return Order(item["groupId"], item["myorders"][0])

    @property
    def get_orders(self):
        return self._orders


class Order:
    """Single order item"""

    def __init__(self, order_id: str, items: dict) -> None:
        """Init method"""
        self._order_id = order_id
        self._seller = items["seller"]["login"]
        iterator = map(self.get_offer, items["offers"])
        self._offers = list(iterator)
        self._order_date = items["orderDate"]
        self._status = Status(items["status"]["primary"]["status"])
        delivery = items["delivery"]
        waybills_data = delivery["waybillsData"]

        if "waybills" in waybills_data:
            if "pickupCode" in waybills_data["waybills"][0]:
                pickup = waybills_data["waybills"][0]["pickupCode"]

                self._delivery = Delivery(
                    delivery["name"],
                    waybills_data["waybills"][0]["carrier"]["url"],
                    pickup.get("code"),
                    pickup.get("receiverPhoneNumber"),
                    pickup.get("qrCode"),
                )
            else:
                self._delivery = Delivery(
                    delivery["name"],
                    waybills_data["waybills"][0]["carrier"]["url"],
                    None,
                    None,
                    None,
                )
        else:
            self._delivery = Delivery(delivery["name"], None, None, None, None)

    def get_formatted_address(self, items: dict):
        """Returns formatted delivery address"""
        return f"{items['street']} {items['code']} {items['city']}"

    def get_offer(self, item: Any):
        """Returns single order"""
        return Offer(
            item["id"],
            item["title"],
            item["unitPrice"],
            item["friendlyUrl"],
            int(item["quantity"]),
            item["imageUrl"],
        )

    @property
    def get_order_id(self):
        return self._order_id

    @property
    def get_seller(self):
        return self._seller

    @property
    def get_offers(self):
        return self._offers

    @property
    def get_orde_date(self):
        return self._order_date

    @property
    def get_status(self):
        return self._status

    @property
    def get_delivery(self):
        return self._delivery


class Status:
    """Order status"""

    def __init__(self, current_status: str) -> None:
        """Init method"""
        self._current_status = current_status

    @property
    def get_current_status(self):
        return self._current_status


class Delivery:
    """Delivery info"""

    def __init__(
        self,
        name: str,
        url: str,
        pickup_code: str,
        receiver_phone_number: str,
        qr_code: str,
    ) -> None:
        """Init method"""
        self._name = name
        self._url = url
        self._pickup_code = pickup_code
        self._receiver_phone_number = receiver_phone_number
        self._qr_code = qr_code

    @property
    def get_name(self):
        return self._name

    @property
    def get_url(self):
        return self._url

    @property
    def get_pickup_code(self):
        return self._pickup_code

    @property
    def get_receiver_phone_number(self):
        return self._receiver_phone_number

    @property
    def get_qr_code(self):
        return self._qr_code


class Offer:
    """Single offer item"""

    def __init__(
        self,
        offer_id: str,
        title: str,
        unit_urice: dict,
        friendly_url: str,
        quantity: int,
        image_url: str,
    ) -> None:
        """Init method"""
        self._offer_id = offer_id
        self._title = title
        self._unit_price = float(unit_urice["amount"])
        self._price_currency = unit_urice["currency"]
        self._friendly_url = friendly_url
        self._quantity = quantity
        self._image_url = image_url

    @property
    def get_id(self):
        return self._offer_id

    @property
    def get_title(self):
        return self._title

    @property
    def get_unit_price(self):
        return self._unit_price

    @property
    def get_price_currency(self):
        return self._price_currency

    @property
    def get_friendly_url(self):
        return self._friendly_url

    @property
    def get_quantity(self):
        return self._quantity

    @property
    def get_image_url(self):
        return self._image_url
