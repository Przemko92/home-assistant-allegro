import logging
from .types.get_order_result import Order
from .api import AllegroApiClient

_LOGGER: logging.Logger = logging.getLogger(__package__)


class AllegroData:
    def __init__(
        self,
        all_orders: list[Order],
        not_delivered: list[Order],
        waiting_for_pickup: list[Order],
        in_transit: list[Order],
        in_delivery: list[Order],
    ) -> None:
        self._all_orders = all_orders
        self._not_delivered = not_delivered
        self._waiting_for_pickup = waiting_for_pickup
        self._in_transit = in_transit
        self._in_delivery = in_delivery

    @staticmethod
    async def get_data(api: AllegroApiClient):

        try:
            get_orders_response = await api.get_orders()

            not_delivered = list[Order](
                filter(
                    lambda order: order.get_status.get_current_status != "DELIVERED"
                    and order.get_status.get_current_status != "RETURNED",
                    get_orders_response.get_orders,
                )
            )

            waiting_for_pickup = list[Order](
                filter(
                    lambda order: order.get_status.get_current_status
                    == "AVAILABLE_FOR_PICKUP",
                    get_orders_response.get_orders,
                )
            )

            in_delivery = list[Order](
                filter(
                    lambda order: order.get_status.get_current_status == "IN_DELIVERY",
                    get_orders_response.get_orders,
                )
            )

            in_transit = list[Order](
                filter(
                    lambda order: order.get_status.get_current_status == "IN_TRANSIT",
                    get_orders_response.get_orders,
                )
            )

            return AllegroData(
                get_orders_response.get_orders,
                not_delivered,
                waiting_for_pickup,
                in_transit,
                in_delivery,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error while testing credentials %s",
                exception,
            )

            pass

    @property
    def get_all_orders(self):
        return self._all_orders

    @property
    def get_not_delivered_orders(self):
        return self._not_delivered

    @property
    def get_waiting_for_pickup(self):
        return self._waiting_for_pickup

    @property
    def get_in_transit(self):
        return self._in_transit

    @property
    def get_in_delivery(self):
        return self._in_delivery
