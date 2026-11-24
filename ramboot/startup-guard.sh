# SPDX-License-Identifier: Apache-2.0
# Function library for the guarded PID 1 entrypoint. Never source on a host
# with a real BusyBox unless every privileged operation is safely substituted.

guard_module_sequence() {
    printf '%s\n' amlogic-gkitool.ko amlogic-debug-iotrace.ko amlogic-uart.ko \
        amlogic-hwspinlock.ko amlogic-debug.ko amlogic-secmon.ko amlogic-cpuinfo.ko \
        page_trace.ko amlogic-memory-debug.ko aml_cma.ko clk-scmi.ko amlogic-clk.ko \
        amlogic-clk-soc-s7d.ko amlogic-aoclk-soc-t5w.ko amlogic-gpio.ko \
        amlogic-pinctrl-soc-s7d.ko amlogic-mailbox.ko amlogic-pwm.ko pwm-regulator.ko \
        gpio-regulator.ko amlogic-reset.ko amlogic-power.ko amlogic-cpufreq.ko \
        amlogic-thermal.ko amlogic-usb.ko cqhci.ko amlogic-mmc.ko
}

guard_hardware_sequence() {
    # Remaining stock dependency closure of amlogic-input and aml_drm. Load only
    # after internal MMC is protected; no camera, watchdog or external PHY roots.
    printf '%s\n' amlogic-efuse-unifykey.ko tee.ko amlogic-tee.ko videobuf-core.ko \
        dvb-core.ko amlogic-pm.ko amlogic-input.ko amlogic-dvb.ko aml_media.ko aml_drm.ko
}

guard_load_modules() (
    _sequence=$1
    _manifest=$2
    [ -f "$_manifest" ] && [ ! -L "$_manifest" ] || return 1
    exec 3< "$_manifest" || return 1
    # Validate the complete ordered input set before loading even its first module.
    for _expected in $_sequence; do
        read -r _hash _name _extra <&3 || return 1
        [ "$_name" = "$_expected" ] && [ -z "$_extra" ] || return 1
        [ "${#_hash}" = 64 ] || return 1
        case $_hash in *[!0-9a-f]*) return 1;; esac
        _path=$GUARD_MODULE_DIR/$_expected
        [ -f "$_path" ] && [ ! -L "$_path" ] || return 1
        _actual=$("$GUARD_BB" sha256sum "$_path") || return 1
        [ "${_actual%% *}" = "$_hash" ] || return 1
    done
    if read -r _tail <&3 || [ -n "$_tail" ]; then return 1; fi
    exec 3<&-
    for _name in $_sequence; do
        "$GUARD_BB" insmod "$GUARD_MODULE_DIR/$_name" || return 1
    done
)

guard_load_storage_modules() {
    guard_load_modules "$(guard_module_sequence)" "$GUARD_MODULE_MANIFEST"
}

guard_load_hardware_modules() {
    guard_load_modules "$(guard_hardware_sequence)" "$GUARD_HARDWARE_MANIFEST"
}

guard_prepare_views() {
    for _path in "$GUARD_PROCROOT" "$GUARD_SYSROOT"; do
        [ ! -L "$_path" ] && [ -d "$_path" ] || return 1
        # Reject a previously mounted Android/proc/sys environment.
        case $("$GUARD_BB" stat -f -c '%T' "$_path") in
            tmpfs|ramfs) ;;
            *) return 1;;
        esac
    done
    "$GUARD_BB" mount -t proc -o ro,nosuid,nodev,noexec proc "$GUARD_PROCROOT" || return 1
    "$GUARD_BB" mount -t sysfs -o ro,nosuid,nodev,noexec sysfs "$GUARD_SYSROOT" || return 1
}

guard_validate_boot() (
    _expected=$("$GUARD_BB" cat "$GUARD_RUNTIME/kernel.release") || return 1
    [ -n "$_expected" ] || return 1
    _running=$("$GUARD_BB" uname -r) || return 1
    [ "$_expected" = "$_running" ] || return 1
    printf '%s\0' s7d_s905x5m_bm201-3g > "$GUARD_WORKDIR/expected-board" || return 1
    "$GUARD_BB" cmp -s "$GUARD_WORKDIR/expected-board" \
        "$GUARD_SYSROOT/firmware/devicetree/base/compatible" || return 1
    _cmdline=$("$GUARD_BB" cat "$GUARD_PROCROOT/cmdline") || return 1
    _bootconfig=$("$GUARD_BB" cat "$GUARD_PROCROOT/bootconfig") || return 1
    # Match the pinned Android init's force-normal-boot detection. Do not hand
    # it a command line that would switch into the normal-boot ramdisk.
    case $_cmdline in *androidboot.force_normal_boot=1*) return 1;; esac
    case $_bootconfig in *'androidboot.force_normal_boot = "1"'*) return 1;; esac
    case "$_cmdline $_bootconfig" in *hibernation_resume_device*|*resume=*) return 1;; esac
)

guard_wait_storage() (
    _attempt=0
    while [ "$_attempt" -lt 10 ]; do
        guard_protect_storage && return 0
        _attempt=$((_attempt + 1))
        [ "$_attempt" = 10 ] || "$GUARD_BB" sleep 1 || return 1
    done
    return 1
)

guard_cleanup_views() {
    "$GUARD_BB" umount "$GUARD_SYSROOT" || return 1
    "$GUARD_BB" umount "$GUARD_PROCROOT" || return 1
}

guard_startup() {
    GUARD_STAGE=views
    guard_prepare_views || return 1
    GUARD_STAGE=boot
    guard_validate_boot || return 1
    GUARD_STAGE=modules
    guard_load_storage_modules || return 1
    GUARD_STAGE=storage
    guard_wait_storage || return 1
    GUARD_STAGE=hardware
    guard_load_hardware_modules || return 1
    GUARD_STAGE=storage-recheck
    guard_protect_storage || return 1
    GUARD_STAGE=cleanup
    guard_cleanup_views || return 1
    GUARD_STAGE=ready
}
