"""Constants for home-assistant-allegro."""
# Base component constants
NAME = "Home Assistant Allegro"
DOMAIN = "home_assistant_allegro"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"

ATTRIBUTION = "Data provided by https://developer.allegro.pl/"
ISSUE_URL = "https://github.com/Przemko92/home-assistant-allegro/issues"

# Icons
ICON = "mdi:local-shipping"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_TOKEN = "token"

# ALLEGRO_BASE_URL = "https://allegro.pl.allegrosandbox.pl"
# ALLEGRO_API_URL = "https://api.allegro.pl.allegrosandbox.pl"

ALLEGRO_BASE_URL = "https://allegro.pl"
ALLEGRO_API_URL = "https://api.allegro.pl"
# Defaults
DEFAULT_NAME = "allegro"


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
