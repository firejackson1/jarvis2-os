#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Rehearse the actual Android build-property rules with Kati and Ninja."""

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


MAKEFILE = """\
BUILD_NUMBER_FILE := build_number.txt
BUILD_DATETIME_FILE := build_date.txt
BUILD_NUMBER_FROM_FILE := $$(cat $(BUILD_NUMBER_FILE))
DATE_FROM_FILE := date -u -d @$$(cat $(BUILD_DATETIME_FILE))
BUILD_FINGERPRINT_FROM_FILE := $$(cat build_fingerprint.txt)
BUILDINFO_SH := buildinfo.sh
API_FINGERPRINT := api_fingerprint.txt
BUILD_HOSTNAME_FILE := build_hostname.txt
BUILD_HOSTNAME_FROM_FILE := $$(cat $(BUILD_HOSTNAME_FILE))
POST_PROCESS_PROPS := /usr/bin/true
PLATFORM_SDK_VERSION := 34
PLATFORM_VERSION_LAST_STABLE := 14
PLATFORM_VERSION := 14
PLATFORM_VERSION_CODENAME := REL
BUILD_VERSION_TAGS := test-keys
intermediates-dir-for = .
to-lower = $(1)
.PHONY: all
all: system/build.prop system_ext/build.prop product/build.prop
"""

TARGETS = """\
$(eval $(call build-properties,system,system/build.prop,$(gen_from_buildinfo_sh),,,,))
$(eval $(call build-properties,system_ext,system_ext/build.prop,,,,,))
$(eval $(call build-properties,product,product/build.prop,,,,,))
"""


def build_properties_rules(source):
    snippets = []
    for name in ('generate-common-build-props', 'build-properties'):
        match = re.search(rf'^define {name}\n.*?^endef$', source, re.MULTILINE | re.DOTALL)
        if match is None:
            raise ValueError(f'Missing upstream Make macro: {name}')
        snippets.append(match[0])
    start = source.index('gen_from_buildinfo_sh :=')
    end = source.index('\nifdef TARGET_SYSTEM_PROP', start)
    snippets.append(source[start:end])
    return '\n'.join(snippets) + '\n'


def replay(build_make, host_bin, numbered):
    rules = build_properties_rules((build_make / 'core/sysprop.mk').read_text())
    with tempfile.TemporaryDirectory(prefix='jarvis2-build-props-') as directory:
        work = Path(directory)
        (work / 'Makefile').write_text(MAKEFILE + f'HAS_BUILD_NUMBER := {str(numbered).lower()}\n'
                                      + rules + TARGETS)
        shutil.copyfile(build_make / 'tools/buildinfo.sh', work / 'buildinfo.sh')
        (work / 'api_fingerprint.txt').write_text('REL\n')
        (work / 'build_hostname.txt').write_text('builder\n')

        def build():
            subprocess.run([host_bin / 'ninja', '-f', 'build.ninja', 'all'],
                           cwd=work, stdout=subprocess.PIPE, check=True)

        def set_build_number(number):
            (work / 'build_number.txt').write_text(number + '\n')
            (work / 'build_fingerprint.txt').write_text(
                f'onn/lineage_jarvis2/jarvis2:14/AP2A.240905.003/{number}:userdebug/test-keys\n')

        def assert_identity(number, epoch):
            failures = []
            for partition in ('system', 'system_ext', 'product'):
                properties = (work / partition / 'build.prop').read_text().splitlines()
                prefix = f'ro.{partition}.build'
                for expected in (f'{prefix}.version.incremental={number}',
                                 f'{prefix}.date.utc={epoch}'):
                    if expected not in properties:
                        failures.append(expected)
                fingerprints = [line for line in properties if line.startswith(prefix + '.fingerprint?=')]
                if len(fingerprints) != 1 or f'/{number}:userdebug/test-keys' not in fingerprints[0]:
                    failures.append(prefix + '.fingerprint')
            system = (work / 'system/build.prop').read_text().splitlines()
            for expected in (f'ro.build.version.incremental={number}', f'ro.build.date.utc={epoch}'):
                if expected not in system:
                    failures.append(expected)
            if failures:
                raise RuntimeError('Incremental build properties are stale: ' + ', '.join(failures))

        set_build_number('jarvis2.first')
        date = work / 'build_date.txt'
        date.write_text('1795517392\n')
        subprocess.run([host_bin / 'ckati', '--ninja', '-f', 'Makefile', 'all'],
                       cwd=work, stdout=subprocess.PIPE, check=True)
        build()
        assert_identity('jarvis2.first', '1795517392')
        outputs = [work / part / 'build.prop' for part in ('system', 'system_ext', 'product')]
        initial = [hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs]
        print('Fresh fixture SHA-256 (system, system_ext, product):', *initial, flush=True)
        if not numbered:
            set_build_number('jarvis2.second')
            date.write_text('1795575971\n')
            build()
            assert_identity('jarvis2.first', '1795517392')
            return
        set_build_number('jarvis2.second')
        build()
        assert_identity('jarvis2.second', '1795517392')
        date.write_text('1795575971\n')
        build()
        assert_identity('jarvis2.second', '1795575971')
        mtimes = [path.stat().st_mtime_ns for path in outputs]
        build()
        if mtimes != [path.stat().st_mtime_ns for path in outputs]:
            raise RuntimeError('An unchanged numbered build reran partition property generation')
        print('Native Kati/Ninja refreshed all partition build numbers and dates.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_make', type=Path)
    parser.add_argument('host_bin', type=Path)
    args = parser.parse_args()
    replay(args.build_make.resolve(), args.host_bin.resolve(), numbered=True)
    replay(args.build_make.resolve(), args.host_bin.resolve(), numbered=False)
