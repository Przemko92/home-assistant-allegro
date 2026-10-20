"""Constants for the Allegro integration."""

NAME = "Allegro buyer"
DOMAIN = "allegro"
VERSION = "0.3.0"
ATTRIBUTION = "Data provided by http://api.allegro.pl"
ISSUE_URL = "https://github.com/Przemko92/home-assistant-allegro"

ICON_WAITING = "mdi:package-variant"
ICON_TRANSIT = "mdi:truck-delivery"
ICON_DELIVERY = "mdi:map-marker-radius-outline"
ICON_READY = "mdi:archive-check"
ICON_CART = "mdi:cart"
ICON_MESSAGES = "mdi:email-alert"
ICON_INVOICE = "mdi:file-document-outline"
ICON_OTHER_POINT = "mdi:map-marker-alert"
ICON_MARK_READ = "mdi:email-open-multiple"
ICON_MARK_OLDER_READ = "mdi:email-sync-outline"

SERVICE_ADD_TO_CART = "add_to_cart"
ATTR_ITEM_ID = "item_id"
ATTR_QUANTITY = "quantity"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"

SERVICE_MARK_MESSAGE_READ = "mark_message_read"
SERVICE_MARK_MESSAGES_READ = "mark_messages_read"
SERVICE_DOWNLOAD_INVOICE = "download_invoice"
SERVICE_GET_PICKUP_CODE = "get_pickup_code"
ATTR_THREAD_ID = "thread_id"
ATTR_CATEGORY = "category"
ATTR_DIRECTORY = "directory"
ATTR_SELLER = "seller"
ATTR_WAYBILL = "waybill"

PLATFORMS = ["sensor", "button", "todo"]

CONF_DEFAULT_PICKUP_POINT = "default_pickup_point"
CONF_AUTO_READ = "auto_read_messages"
CONF_AUTO_READ_DAYS = "auto_read_days"
DEFAULT_AUTO_READ_DAYS = 7

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
