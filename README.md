# Home assistant Allegro integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]


**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor.allegro_in_progress` | Contains info about orders in OTHER THAN DELIVERED or RETURNED status.
`sensor.allegro_in_delivery` | Contains info about orders in IN_DELIVERY status.
`sensor.allegro_in_transit` | Contains info about orders in IN_TRANSIT status.
`sensor.allegro_waiting_for_pickup` | Contains info about orders in AVAILABLE_FOR_PICKUP status.


## Installation

HACS (recommended)

1. Open HACS
2. Search for Allegro buyer (use integrations tab) and download it
3. In the HA UI go to "Configuration" -> "Integrations" and search for "Allegro buyer"
4. Restart HomeAssistant
5. Open another tab and go to https://allegro.pl and get value of QXLSESSID cookie using browser dev tools (F12)
6. Install Alegro buyer integration and pass QXLSESSID value and your user name (optional - required for more than one instance)

## Configuration is done in the UI

Parameter | Description
-- | --
`QXLSESSID` | Value of QXLSESSID cookie (required)
`user_name` | Optional value for multiple instances

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[home_assistant_allegro]: https://github.com/Przemko92/home-assistant-allegro

[buymecoffee]: https://www.buymeacoffee.com/przemko92
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge

[maintainer]: https://github.com/Przemko92
[maintainer-shield]: https://img.shields.io/badge/maintainer-%40Przemko92-blue.svg?style=for-the-badge

[commits]: https://github.com/Przemko92/home-assistant-allegro/commits/main
[commits-shield]: https://img.shields.io/github/commit-activity/y/Przemko92/home-assistant-allegro.svg?style=for-the-badge

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge

[forum]: https://community.home-assistant.io/
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge

[releases]: https://github.com/Przemko92/home-assistant-allegro/releases
[releases-shield]: https://img.shields.io/github/release/Przemko92/home-assistant-allegro.svg?style=for-the-badge

[license-shield]: https://img.shields.io/github/license/Przemko92/home-assistant-allegro.svg?style=for-the-badge