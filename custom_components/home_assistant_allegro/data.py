from .api import HomeAssistantAllegroApiClient
from typing import Any


class AllegroData:
    def __init__(self, orders: Any) -> None:
        self._orders = orders

    @staticmethod
    async def get_data(api: HomeAssistantAllegroApiClient):
        orders = await api.get_orders()

        return AllegroData(orders)