// SPDX-License-Identifier: Apache-2.0
// Host-only equivalents of Bionic annotations; no recovery interfaces are mocked.
#pragma once
#ifndef __printflike
#define __printflike(fmt, args) __attribute__((format(printf, fmt, args)))
#endif
#ifndef __unused
#define __unused __attribute__((unused))
#endif
