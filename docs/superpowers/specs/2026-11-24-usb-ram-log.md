# USB RAM startup logger

The first full recovery RAM boot stalled with no ADB or UART log. The exact
kernel enables configfs ACM. Build a separate one-way CDC ACM diagnostic image
using the same BusyBox/musl, kernel, DTB and the reviewed USB dependency prefix.
It must never start Android init or load the eMMC driver. No recovery UI or
interactive shell is part of this diagnostic image.

Validate PID 1, RAM root, board and kernel before loading modules. Preserve the
ordinary recovery guard's force-normal/hibernation checks. This diagnostic may
report those flags because it never hands off to Android. Use the first 25
reviewed modules through amlogic-usb; exclude cqhci/amlogic-mmc and all later
hardware modules. Check all hashes/dependencies before any load.

Mount a private RAM-owned configfs view, refuse any existing gadget or an
unexpected UDC, create only an ACM function, derive ttyGS0's major/minor from
sysfs and make its node in RAM. Use the conventional Linux gadget development
identity only for this private diagnostic, with generic strings and no owner
serial. No storage function, network listener, shell, ADB or input processing.

A background log writer may block waiting for host DTR; PID 1 must not. Preserve
the RAM log and wait without rebooting on success or error. A disconnect may
restart only the owned writer; it must not start additional gadget instances.
Do not modify a preexisting gadget or hide setup failures.

The packaging mode must be explicit, reported and byte-bound to source inputs.
Default recovery assembly keeps its original safety/handoff behavior. Build
private images only; no flash, slot switch, reboot or VM interruption. Physical
validation is a separate gate, including a verified return/power-control path.

Alternatives: UART requires unavailable physical wiring; normal recovery ADB
starts too late; weakening the storage guard would lose its protection. The
owner delegated continued debugging and opted out of routine design questions.
