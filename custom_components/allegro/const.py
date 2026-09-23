"""Constants for the Allegro integration."""

NAME = "Allegro buyer"
DOMAIN = "allegro"
VERSION = "0.1.2"
ATTRIBUTION = "Data provided by http://api.allegro.pl"
ISSUE_URL = "https://github.com/Przemko92/home-assistant-allegro"

ICON_WAITING = "mdi:package-variant"
ICON_TRANSIT = "mdi:truck-delivery"
ICON_DELIVERY = "mdi:map-marker-radius-outline"
ICON_READY = "mdi:archive-check"
ICON_CART = "mdi:cart"

SERVICE_ADD_TO_CART = "add_to_cart"
ATTR_ITEM_ID = "item_id"
ATTR_QUANTITY = "quantity"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"

PLATFORMS = ["sensor"]

CONF_COOKIE = "QXLSESSID"
CONF_USERNAME = "user_name"
CONF_METHOD = "method"
METHOD_COMPANION = "companion"
METHOD_COOKIE = "cookie"

ALLEGRO_API_URL = "https://api.allegro.pl"
ALLEGRO_EDGE_URL = "https://edge.allegro.pl"
ALLEGRO_START_URL = "https://allegro.pl/logowanie?origin_url=%2Fmoje-allegro%2Fzakupy%2Fkupione%3Fdd_referrer%3D"
ALLEGRO_ORDERS_URL = "https://allegro.pl/moje-allegro/zakupy/kupione"
COMPANION_WAIT = {
    "event": "navigation",
    "url_prefixes": [
        ALLEGRO_ORDERS_URL,
        "https://www.allegro.pl/moje-allegro/zakupy/kupione",
    ],
    "cookies": [CONF_COOKIE],
}

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
