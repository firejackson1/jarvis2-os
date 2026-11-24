# Remote shortcut setup

The clean f38 install contains the controls app but leaves its accessibility
service disabled. The owner verified that enabling it restores both side menus.
Users must be able to complete that step through TV Settings without ADB or AI.

Add the current service's enabled/disabled status and a setup button at the top
of Remote & controller buttons. Open the existing Android Accessibility screen;
refresh status when returning. Show the control even without a paired remote.
Use Android's service list for this user, matching the exact Keys component.
Keep consent in Android Settings; never write its service list from the app.

Use the existing screen and Android intent rather than a new wizard or a
privileged automatic enable operation. The shipped TV Settings registers
ACCESSIBILITY_SETTINGS, but not the service-details action. Handle an unavailable
settings activity with a visible explanation. Do not change button mappings,
pairing state, slot B, ROM partitions or the running Bazzite desktop.

This small flow follows the owner's standing instruction to continue release
work without repeated questions. Implement inline; no subagents. App-only live
testing must preserve data and verify the installed signer's match first.
