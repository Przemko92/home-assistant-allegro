from typing import Any


class GetUserInfoResult:
    """Result of get_orders method"""

    def __init__(self, items: dict) -> None:
        """Init method"""
        self._login = items["accounts"]["allegro"]["login"]

    @property
    def get_login(self):
        return self._login
