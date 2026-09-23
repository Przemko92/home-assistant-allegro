# Home Assistant Allegro integration

<img src="custom_components/allegro/brand/icon.png" alt="Allegro buyer" width="80">

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Validate][validate-shield]][validate]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

Custom Home Assistant integration for [Allegro](https://allegro.pl) buyer accounts. It tracks orders and the shopping cart, and can add offers to the cart.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Przemko92&repository=home-assistant-allegro&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=allegro)

## Features

| Entity | Description |
| -- | -- |
| `sensor.allegro_in_progress` | Orders in a status other than delivered or returned |
| `sensor.allegro_in_delivery` | Orders in `IN_DELIVERY` status |
| `sensor.allegro_in_transit` | Orders in `IN_TRANSIT` status |
| `sensor.allegro_waiting_for_pickup` | Orders in `AVAILABLE_FOR_PICKUP` status |
| `sensor.allegro_cart` | Number of items in the shopping cart (details in attributes) |

## Services

### `allegro.add_to_cart`

Add an offer to the Allegro shopping cart. On success the cart sensor is refreshed.

| Parameter | Description |
| -- | -- |
| `item_id` | Allegro offer ID (required). This is `offerId` from the offer URL. |
| `quantity` | Pieces to add (default: 1) |
| `config_entry_id` | Account to use when multiple Allegro accounts are configured |

Example URL (`item_id` is the bold `offerId`):

https://allegro.pl/produkt/kawa-ziarnista-100-arabica-west-caffee-brazil-monte-carmelo-1000-g-c7e0acba-5b98-4f99-969d-5e85580b95c6?offerId=**15070058532**

```yaml
service: allegro.add_to_cart
data:
  item_id: "15070058532"
  quantity: 1
```

## Installation

### HACS (recommended)

1. Open HACS
2. Use the [My Home Assistant](https://my.home-assistant.io/redirect/hacs_repository/?owner=Przemko92&repository=home-assistant-allegro&category=integration) button above, **or** add this repository as a custom repository (`https://github.com/Przemko92/home-assistant-allegro`, category **Integration**)
3. Search for **Allegro buyer** and download it
4. Restart Home Assistant
5. Optionally install the [Browser Companion](https://github.com/Przemko92/homeassistant-browser-companion) add-on (Home Assistant OS / Supervised) for in-UI sign-in
6. [Add the integration](https://my.home-assistant.io/redirect/config_flow_start/?domain=allegro): Settings → Devices & services → **Allegro buyer**
   - **Browser Companion** (optional): sign in at allegro.pl in the sidebar browser, then open **Moje Allegro → Zakupy → Kupione**. `QXLSESSID` is captured there
   - **Paste QXLSESSID**: browser dev tools (F12)

### Manual

1. Copy `custom_components/allegro` into `<config>/custom_components/allegro`
2. Restart Home Assistant
3. Add **Allegro buyer** from Settings → Devices & services

## Configuration is done in the UI

| Parameter | Description |
| -- | -- |
| `QXLSESSID` | Session cookie (pasted, or captured by optional Companion) |
| `user_name` | Optional value for multiple instances |

[Browser Companion](https://github.com/Przemko92/homeassistant-browser-companion) is optional. Without it, paste `QXLSESSID` from the browser.

Minimum Home Assistant version: **2026.8.0**.

To test against Supervisor + Companion, keep this repo next to `homeassistant-browser-companion`, rebuild that devcontainer, then run the task **Link Allegro custom component**. Details: `homeassistant-browser-companion/.devcontainer/README.md`.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.allegro: debug
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[home_assistant_allegro]: https://github.com/Przemko92/home-assistant-allegro

[buymecoffee]: https://www.buymeacoffee.com/przemko92
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge

[commits]: https://github.com/Przemko92/home-assistant-allegro/commits/main
[commits-shield]: https://img.shields.io/github/commit-activity/y/Przemko92/home-assistant-allegro.svg?style=for-the-badge

[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge

[validate]: https://github.com/Przemko92/home-assistant-allegro/actions/workflows/validate.yml
[validate-shield]: https://github.com/Przemko92/home-assistant-allegro/actions/workflows/validate.yml/badge.svg

[releases]: https://github.com/Przemko92/home-assistant-allegro/releases
[releases-shield]: https://img.shields.io/github/release/Przemko92/home-assistant-allegro.svg?style=for-the-badge

[license-shield]: https://img.shields.io/github/license/Przemko92/home-assistant-allegro.svg?style=for-the-badge
