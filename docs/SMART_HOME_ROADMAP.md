# Smart Home: Matter and Thread

Requested 2026-11-23. These are proposed features, not advertised working support.

## Evidence

A read-only check of the development build found vendor.hardware.threadnetwork
IThreadChip/chip0 registered. The vendor service configuration selects
`spinel+hdlc+uart:///dev/ttyS3?uart-baudrate=921600`, under user thread_network.
Vendor Thread reset/update hooks also exist; they were not exercised. This is
hardware-interface evidence, not a verified Thread network or border router.
Do not open that UART behind the existing HAL, reset the radio, read stored
Thread datasets or flash firmware just to probe it.

The internal temperature sensor measures SoC temperature, not ambient room
conditions. Room-temperature widgets would need an external/user-provided sensor.

## Separate deliverables

- [ ] Inventory Thread HAL interface/firmware licensing and inspect its capabilities without changing current network state.
- [ ] Determine whether the Android14 vendor-specific interface can feed an open-source OpenThread/OTBR implementation or needs a shim.
- [ ] Prove read-only radio health and packet transport before starting a new Thread network.
- [ ] Add an explicitly opt-in border-router service, IPv6/mDNS/SRP routing and safe lifecycle handling.
- [ ] Add a Matter controller/provider using a user's own Home Assistant account or a licensed open-source controller stack.
- [ ] Keep Wi-Fi/Ethernet Matter control separate from Thread border-router readiness.
- [ ] Implement consent-driven commissioning, credentials storage, fabric/network isolation and clear reset/forget behavior.
- [ ] Validate with real test Matter/Thread devices without joining or reconfiguring the owner's production fabric automatically.
- [ ] Verify interaction with Bluetooth, Wi-Fi, sleep and software updates.

No Google Home/GMS functionality is assumed available in the public ROM. The
current Smart Home page selects an installed assistant provider and opens setup;
it does not implement Matter commissioning or border-router operation yet.

References:
- https://www.home-assistant.io/integrations/matter/
- https://openthread.io/guides/border-router
- https://github.com/project-chip/connectedhomeip
