# Home Assistant Allegro integration

Custom Home Assistant integration for Allegro buyer accounts. It tracks orders and the shopping cart.

<p><font color="red"><strong>Breaking change (0.3.0):</strong> the pickup code, receiver phone number and QR code are no longer sensor attributes. Call <code>allegro.get_pickup_code</code> to read them.</font></p>

See [README.md](README.md) for installation, configuration, entities, and services.

**Allegro buyer** is in the HACS default store. Open **Integrations**, search for **Allegro buyer**, and download it.
