"""Constants for allegro_integration."""
# Base component constants
NAME = "Allegro buyer"
DOMAIN = "allegro"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.2"
ATTRIBUTION = "Data provided by http://api.allegro.pl"
ISSUE_URL = "https://github.com/Przemko92/home-assistant-allegro"

# Icons
ICON_WAITING = "mdi:package-variant"
ICON_TRANSIT = "mdi:truck-delivery"
ICON_DELIVERY = "mdi:map-marker-radius-outline"
ICON_READY = "mdi:archive-check"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]


# Configuration and options
CONF_COOKIE = "QXLSESSID"
CONF_USERNAME = "user_name"

ALLEGRO_API_URL = "https://api.allegro.pl"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
