# SPDX-License-Identifier: Apache-2.0
# Function library, not a PID 1 launcher. The launcher must first validate the
# board/RAM root and create private RAM-backed work and device directories.

guard_collect_nodes() (
    _base= _count=0
    for _entry in "$GUARD_SYSFS"/mmcblk*; do
        [ -d "$_entry" ] || continue
        _name=${_entry##*/}
        case ${_name#mmcblk} in ''|*[!0-9]*) continue;; esac
        [ "$("$GUARD_BB" cat "$_entry/device/type" 2>/dev/null)" = MMC ] || continue
        [ "$("$GUARD_BB" cat "$_entry/removable" 2>/dev/null)" = 0 ] || continue
        _base=$_name
        _count=$((_count + 1))
    done
    [ "$_count" = 1 ] || { echo 'guard: internal MMC absent or ambiguous' >&2; return 1; }

    _boot0=0 _boot1=0 _partitions=0 _seen='|'
    for _entry in "$GUARD_SYSFS/$_base"*; do
        [ -d "$_entry" ] || continue
        _name=${_entry##*/}
        case $_name in
            "$_base") ;;
            "${_base}boot0") _boot0=1;;
            "${_base}boot1") _boot1=1;;
            *)
                _suffix=${_name#"${_base}p"}
                [ "$_suffix" != "$_name" ] || continue
                case $_suffix in ''|*[!0-9]*) continue;; esac
                _partitions=$((_partitions + 1))
                ;;
        esac
        _dev=$("$GUARD_BB" cat "$_entry/dev") || return 1
        case $_dev in *:*) ;; *) return 1;; esac
        _major=${_dev%%:*} _minor=${_dev#*:}
        case $_major in ''|*[!0-9]*) return 1;; esac
        case $_minor in ''|*[!0-9]*) return 1;; esac
        [ "${#_major}" -le 10 ] && [ "${#_minor}" -le 10 ] || return 1
        while [ "${_major#0}" != "$_major" ]; do _major=${_major#0}; done
        while [ "${_minor#0}" != "$_minor" ]; do _minor=${_minor#0}; done
        _major=${_major:-0} _minor=${_minor:-0}
        [ "$_major" -le 4095 ] && [ "$_minor" -le 1048575 ] || return 1
        _dev=$_major:$_minor
        case $_seen in *"|$_dev|"*) echo 'guard: duplicate block identity' >&2; return 1;; esac
        _seen="$_seen$_dev|"
        printf '%s %s %s\n' "$_name" "$_major" "$_minor"
    done
    [ "$_boot0" = 1 ] && [ "$_boot1" = 1 ] && [ "$_partitions" -gt 0 ] || {
        echo 'guard: MMC boot devices or partitions not ready' >&2
        return 1
    }
)

guard_set_readonly() (
    "$GUARD_BB" blockdev --setro "$1" || return 1
    _ro=$("$GUARD_BB" blockdev --getro "$1") || return 1
    [ "$_ro" = 1 ]
)

guard_protect_node() (
    _path=$GUARD_DEVROOT/$1
    if [ -e "$_path" ] || [ -L "$_path" ]; then
        [ ! -L "$_path" ] && [ -b "$_path" ] || return 1
    else
        "$GUARD_BB" mknod "$_path" b "$2" "$3" || return 1
    fi
    [ ! -L "$_path" ] && [ -b "$_path" ] || return 1
    _expected=$(printf '%x:%x' "$2" "$3") || return 1
    _actual=$("$GUARD_BB" stat -c '%t:%T' "$_path") || return 1
    [ "$_actual" = "$_expected" ] || return 1
    guard_set_readonly "$_path"
)

guard_protect_storage() (
    umask 077
    LC_ALL=C
    export LC_ALL
    [ -n "$GUARD_SYSFS" ] && [ -d "$GUARD_SYSFS" ] || return 1
    [ -n "$GUARD_DEVROOT" ] && [ -d "$GUARD_DEVROOT" ] || return 1
    [ -n "$GUARD_WORKDIR" ] && [ -d "$GUARD_WORKDIR" ] || return 1
    [ -n "$GUARD_BB" ] && [ -x "$GUARD_BB" ] || return 1
    _before=$GUARD_WORKDIR/mmc-before
    _after=$GUARD_WORKDIR/mmc-after
    [ ! -L "$_before" ] && [ ! -L "$_after" ] || return 1
    guard_collect_nodes > "$_before" || return 1
    "$GUARD_BB" sort "$_before" > "$_after" || return 1
    while read -r _name _major _minor; do
        guard_protect_node "$_name" "$_major" "$_minor" || return 1
    done < "$_after"
    guard_collect_nodes > "$_before" || return 1
    # Enumeration uses the same deterministic pathname order both times. A new,
    # removed or renumbered device invalidates the attempted handoff.
    "$GUARD_BB" cmp -s "$_before" "$_after"
)
