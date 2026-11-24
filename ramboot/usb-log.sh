# SPDX-License-Identifier: Apache-2.0
# One-way private RAM diagnostic. No input reader or Android-init handoff.

usb_log_write() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    printf '%s\n' "$2" > "$1"
}

usb_log_require_udc() (
    _controllers=$("$GUARD_BB" ls -A "$GUARD_SYSROOT/class/udc") || return 1
    [ "$_controllers" = fe350000.crgudc ] && return 0
    [ -z "$_controllers" ] || return 1
    _debug=$GUARD_WORKDIR/usb-debug
    [ ! -e "$_debug" ] && [ ! -L "$_debug" ] || return 1
    "$GUARD_BB" mkdir -m 700 "$_debug" || return 1
    _debug_mounted=0
    usb_log_debug_cleanup() {
        if [ "$_debug_mounted" = 1 ]; then
            "$GUARD_BB" umount "$_debug" || return 1
            _debug_mounted=0
        fi
        "$GUARD_BB" rmdir "$_debug"
    }
    trap usb_log_debug_cleanup EXIT
    "$GUARD_BB" mount -t debugfs -o nosuid,nodev,noexec debugfs "$_debug" || return 1
    _debug_mounted=1
    _mode=$_debug/usb/amlogic/crg-drd-otg/mode
    [ -f "$_mode" ] && [ ! -L "$_mode" ] || return 1
    _role=$("$GUARD_BB" cat "$_mode") || return 1
    [ "$_role" = notg-host ] || return 1
    printf '%s\n' 'USB controller absent; requesting device role through vendor control'
    usb_log_write "$_mode" device || return 1
    _role=$("$GUARD_BB" cat "$_mode") || return 1
    [ "$_role" = notg-device ] || return 1
    for _attempt in 1 2 3 4 5; do
        _controllers=$("$GUARD_BB" ls -A "$GUARD_SYSROOT/class/udc") || return 1
        [ "$_controllers" = fe350000.crgudc ] && break
        [ -z "$_controllers" ] && [ "$_attempt" -lt 5 ] || return 1
        "$GUARD_BB" sleep 1 || return 1
    done
    [ "$_controllers" = fe350000.crgudc ] || return 1
    usb_log_debug_cleanup || return 1
    trap - EXIT
)

usb_log_setup() {
    _config=$GUARD_WORKDIR/config
    [ ! -e "$_config" ] && [ ! -L "$_config" ] || return 1
    "$GUARD_BB" mkdir -m 700 "$_config" || return 1
    "$GUARD_BB" mount -t configfs -o nosuid,nodev,noexec configfs "$_config" || return 1
    [ -d "$_config/usb_gadget" ] && [ ! -L "$_config/usb_gadget" ] || return 1
    _existing=$("$GUARD_BB" ls -A "$_config/usb_gadget") || return 1
    [ -z "$_existing" ] || return 1
    usb_log_require_udc || return 1
    _gadget=$_config/usb_gadget/jarvis2_ram_log
    "$GUARD_BB" mkdir "$_gadget" || return 1
    # Conventional Linux development gadget IDs, not an assigned product ID.
    # This image is private and unqualified for public hardware distribution.
    usb_log_write "$_gadget/idVendor" 0x1d6b || return 1
    usb_log_write "$_gadget/idProduct" 0x0104 || return 1
    usb_log_write "$_gadget/bcdUSB" 0x0200 || return 1
    usb_log_write "$_gadget/bcdDevice" 0x0001 || return 1
    usb_log_write "$_gadget/bDeviceClass" 0x02 || return 1
    "$GUARD_BB" mkdir "$_gadget/strings/0x409" || return 1
    usb_log_write "$_gadget/strings/0x409/serialnumber" RAM-DIAGNOSTIC || return 1
    usb_log_write "$_gadget/strings/0x409/manufacturer" 'Jarvis2 OS unofficial' || return 1
    usb_log_write "$_gadget/strings/0x409/product" 'Jarvis2 RAM startup log' || return 1
    "$GUARD_BB" mkdir "$_gadget/configs/c.1" || return 1
    usb_log_write "$_gadget/configs/c.1/bmAttributes" 0xc0 || return 1
    usb_log_write "$_gadget/configs/c.1/MaxPower" 0 || return 1
    "$GUARD_BB" mkdir "$_gadget/functions/acm.usb0" || return 1
    _port=$("$GUARD_BB" cat "$_gadget/functions/acm.usb0/port_num") || return 1
    [ "$_port" = 0 ] || return 1
    _attempt=0
    while [ ! -f "$GUARD_SYSROOT/class/tty/ttyGS0/dev" ]; do
        _attempt=$((_attempt + 1))
        [ "$_attempt" -lt 5 ] || return 1
        "$GUARD_BB" sleep 1 || return 1
    done
    _device=$("$GUARD_BB" cat "$GUARD_SYSROOT/class/tty/ttyGS0/dev") || return 1
    case $_device in *:*:*) return 1;; *:*) ;; *) return 1;; esac
    _major=${_device%%:*}
    _minor=${_device#*:}
    for _number in "$_major" "$_minor"; do
        case $_number in ''|*[!0-9]*|0[0-9]*) return 1;; esac
        [ "${#_number}" -le 7 ] || return 1
    done
    [ "$_major" -gt 0 ] && [ "$_major" -le 4095 ] && [ "$_minor" -le 1048575 ] || return 1
    USB_LOG_TTY=$GUARD_WORKDIR/ttyGS0
    [ ! -e "$USB_LOG_TTY" ] && [ ! -L "$USB_LOG_TTY" ] || return 1
    "$GUARD_BB" mknod "$USB_LOG_TTY" c "$_major" "$_minor" || return 1
    [ ! -e "$GUARD_WORKDIR/null" ] && [ ! -L "$GUARD_WORKDIR/null" ] || return 1
    "$GUARD_BB" mknod "$GUARD_WORKDIR/null" c 1 3 || return 1
    "$GUARD_BB" ln -s "$_gadget/functions/acm.usb0" "$_gadget/configs/c.1/acm.usb0" || return 1
    usb_log_write "$_gadget/UDC" fe350000.crgudc || return 1
    _bound=$("$GUARD_BB" cat "$_gadget/UDC") || return 1
    [ "$_bound" = fe350000.crgudc ]
}

usb_log_start_writer() {
    # Keep one open TTY across configuration and snapshots: the ACM kernel
    # drops carrier on the last close. Periodic writes still detect an idle
    # disconnect without waiting for new log data; failures reopen the port.
    (
        while :; do
            (
                exec 3<> "$USB_LOG_TTY" || exit 1
                "$GUARD_BB" stty raw -echo <&3 || exit 1
                while :; do
                    "$GUARD_BB" cat "$GUARD_WORKDIR/startup.log" >&3 || exit 1
                    "$GUARD_BB" sleep 2 || exit 1
                done
            )
            "$GUARD_BB" sleep 2 || exit 1
        done
    ) < "$GUARD_WORKDIR/null" &
    USB_LOG_WRITER=$!
}
