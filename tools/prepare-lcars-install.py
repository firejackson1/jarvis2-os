#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify an LCARS archive and prepare local image sets for installation review."""

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'manifests/avb-stock-15640252-profile.json'
RECIPE_FILES = (
    'fixture-tool-pins.json', 'tools/audit-ramdisk.py', 'tools/build_stock_lcars.py',
    'tools/materialize_stock_lcars.py', 'tools/prepare_ramdisk.py', 'tools/repack.py',
)


def load_tool(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACK = load_tool('lcars_package', ROOT / 'tools/package-candidate.py')
AUDIT = load_tool('lcars_chain_audit', ROOT / 'tools/audit-avb-chain.py')


def read_manifest(archive, allow_rehearsal):
    infos = archive.infolist()
    members = {info.filename: info for info in infos}
    expected = {*PACK.METADATA_NAMES, PACK.RECOVERY_PLUGIN, 'manifest.json',
                *('images/' + name for name in PACK.IMAGE_NAMES)}
    has_notices = PACK.RECOVERY_NOTICES in members
    if has_notices:
        expected.add(PACK.RECOVERY_NOTICES)
    if len(infos) != len(expected) or set(members) != expected:
        raise ValueError('Unexpected, duplicate or missing LCARS ZIP entries')
    for info in infos:
        if not stat.S_ISREG(info.external_attr >> 16) or info.flag_bits & 1:
            raise ValueError(f'Archive entry must be an unencrypted regular file: {info.filename}')
    if members['manifest.json'].file_size > 1048576:
        raise ValueError('Archive manifest exceeds its size limit')
    manifest = json.loads(archive.read('manifest.json'), object_pairs_hook=PACK.unique_object)
    if (not isinstance(manifest, dict) or type(manifest.get('format')) is not int or
        manifest['format'] != (3 if has_notices else 2)):
        raise ValueError('Expected an LCARS manifest matching its Recovery notice members')
    if (manifest.get('kind') != 'unofficial-offline-developer-preview' or
        any(manifest.get(key) is not False for key in ('google_payload_included',
            'stock_firmware_included', 'installable_ota', 'installer_included'))):
        raise ValueError('Archive cannot be used as a vanilla LCARS candidate')
    if type(manifest.get('rehearsal_only')) is not bool:
        raise ValueError('Missing or invalid rehearsal class')
    if manifest['rehearsal_only'] and not allow_rehearsal:
        raise ValueError('Temporary-key archive is limited to offline rehearsal')
    revision = manifest.get('source_revision')
    if not isinstance(revision, str) or not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Missing or invalid ROM source revision')
    recovery = manifest.get('recovery')
    if not isinstance(recovery, dict) or recovery.get('plugin_member') != PACK.RECOVERY_PLUGIN:
        raise ValueError('Missing LCARS plug-in binding')
    PACK.reviewed_recovery({'recovery': {key: value for key, value in recovery.items()
                                        if key != 'plugin_member'}})
    if has_notices != ('notices_sha256' in recovery):
        raise ValueError('Missing or unexpected Recovery notice archive binding')
    PACK.sha256_value(manifest.get('image_proof_sha256'))
    records = manifest.get('files')
    if not isinstance(records, dict) or set(records) != expected - {'manifest.json'}:
        raise ValueError('Missing or unexpected manifest file records')
    for name, record in records.items():
        if (not isinstance(record, dict) or set(record) != {'bytes', 'sha256'} or
            type(record['bytes']) is not int or record['bytes'] <= 0 or
            record['bytes'] != members[name].file_size or
            (not name.startswith('images/') and record['bytes'] > 8 * 1024 * 1024)):
            raise ValueError(f'Invalid manifest size or record: {name}')
        PACK.sha256_value(record['sha256'])
    if records[PACK.RECOVERY_PLUGIN]['sha256'] != recovery['plugin_sha256']:
        raise ValueError('Plug-in record disagrees with the Recovery manifest')
    if has_notices and records[PACK.RECOVERY_NOTICES]['sha256'] != recovery['notices_sha256']:
        raise ValueError('Notice archive record disagrees with the Recovery manifest')
    return manifest


def process_members(archive, manifest, work):
    keep = {PACK.RECOVERY_PLUGIN, PACK.RECOVERY_NOTICES, PROFILE,
            *('images/' + name for name in PACK.IMAGE_NAMES)}
    for name, record in manifest['files'].items():
        hasher = hashlib.sha256()
        with archive.open(name) as source:
            if name in keep:
                destination = work / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as target:
                    for chunk in iter(lambda: source.read(1048576), b''):
                        hasher.update(chunk)
                        target.write(chunk)
            else:
                for chunk in iter(lambda: source.read(1048576), b''):
                    hasher.update(chunk)
        if hasher.hexdigest() != record['sha256']:
            raise ValueError(f'ZIP member differs from the reviewed manifest: {name}')


def export_recipe(checkout, revision, output):
    data = subprocess.check_output(['git', '-C', checkout, 'archive', revision, *RECIPE_FILES])
    with tarfile.open(fileobj=io.BytesIO(data)) as snapshot:
        files = [member for member in snapshot if not member.isdir()]
        if len(files) != len(RECIPE_FILES) or {member.name for member in files} != set(RECIPE_FILES):
            raise ValueError('Recovery commit lacks the exact recipe files')
        for member in files:
            if not member.isfile() or member.size > 1048576:
                raise ValueError('Recovery recipe must consist of regular source files')
            target = output / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with snapshot.extractfile(member) as source, target.open('xb') as destination:
                shutil.copyfileobj(source, destination)


def checked_stock_files(directory, profile):
    files = {}
    for partition, record in profile['references'].items():
        path = PACK.regular(directory / (partition + '.img'))
        if path.stat().st_size != record['bytes'] or PACK.digest(path) != record['sha256']:
            raise ValueError(f'Stock input differs from the supported profile: {partition}')
        files[partition] = path
    return files


def require_stock_bindings(avbtool, images, chain, profile):
    expected_nodes = {'vbmeta': {'boot', 'oem', 'vbmeta_system'},
                      'boot': set(), 'oem': set(), 'vbmeta_system': set()}
    nodes = chain['nodes']
    if set(nodes) != set(expected_nodes) or any(
            node['flags'] != 0 or set(node['children']) != expected_nodes[name]
            for name, node in nodes.items()):
        raise ValueError('AVB flags or parent and child layout differ from the stock profile')

    avb = avbtool.Avb()
    bindings = []
    root_has_recovery = False
    for node in nodes:
        image = avbtool.ImageHandler(str(images / (node + '.img')), read_only=True)
        try:
            _, _, descriptors, _ = avb._parse_image(image)
        finally:
            image._image.close()
        for descriptor in descriptors:
            if isinstance(descriptor, (avbtool.AvbHashDescriptor, avbtool.AvbHashtreeDescriptor)):
                bindings.append(descriptor.partition_name)
                if (node == 'vbmeta' and descriptor.partition_name == 'vendor_boot' and
                    isinstance(descriptor, avbtool.AvbHashDescriptor)):
                    root_has_recovery = True
    expected = (set(profile['references']) - set(profile['unbound_references']) |
                {'system', 'system_ext', 'product'})
    if set(bindings) != expected or len(bindings) != len(expected) or not root_has_recovery:
        raise ValueError('AVB image coverage or the root Recovery binding is incomplete')
    return sorted(bindings)


def verify_chain(work, tool_kit, stock, root_pin, profile):
    avb_pin = json.loads((ROOT / 'manifests/avb-test-tool.json').read_text())
    avbtool = PACK.regular(tool_kit / 'external/avb/avbtool.py')
    if PACK.digest(avbtool) != avb_pin['sha256']:
        raise ValueError('Tool kit AVB script differs from its pin')
    tools = work / 'audit-tools'
    for relative in ('external/avb/avbtool.py', 'out/host/linux-x86/bin/avbtool'):
        path = tools / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(avbtool, path)
        path.chmod(0o755)

    images = work / 'chain-images'
    images.mkdir()
    references = {**stock, **{name: work / 'transition-images' / (name + '.img')
                             for name in ('init_boot', 'vendor_boot')}}
    for name, path in references.items():
        (images / (name + '.img')).symlink_to(path)
    for name in PACK.IMAGE_NAMES:
        (images / name).symlink_to(work / 'images' / name)
    chain = AUDIT.audit(images, tools, work / 'avb-audit', root_pin)
    tool = load_tool('lcars_avb', tools / 'external/avb/avbtool.py')
    bindings = require_stock_bindings(tool, images, chain, profile)
    return {**chain, 'verified_image_bindings': bindings}


def prepare(archive, archive_sha256, stock_images, recovery_source, tool_kit, root_pin,
            output, *, allow_rehearsal=False):
    PACK.sha256_value(archive_sha256)
    PACK.sha256_value(root_pin)
    archive = PACK.regular(archive)
    output = Path(os.path.abspath(output))
    if (output.exists() or any(path.is_symlink() for path in (output, *output.parents)) or
        any(output.is_relative_to(path.resolve()) for path in
            (ROOT, stock_images, recovery_source, tool_kit))):
        raise ValueError('Choose a fresh output directory outside the inputs and source tree')
    if PACK.digest(archive) != archive_sha256:
        raise ValueError('Archive SHA-256 differs from the reviewed pin')

    with TemporaryDirectory(prefix='jarvis2-lcars-preflight-', dir=output.parent) as staging:
        work = Path(staging)
        with zipfile.ZipFile(archive) as package:
            manifest = read_manifest(package, allow_rehearsal)
            profile_bytes = (ROOT / PROFILE).read_bytes()
            profile = json.loads(profile_bytes)
            for name in PACK.IMAGE_NAMES:
                if manifest['files']['images/' + name]['bytes'] != profile['output_bytes'][name[:-4]]:
                    raise ValueError(f'Image length differs from the supported profile: {name}')
            process_members(package, manifest, work)
        if (work / PROFILE).read_bytes() != profile_bytes:
            raise ValueError('Archived stock profile differs from the supported profile')
        stock = checked_stock_files(stock_images, profile)
        recovery = manifest['recovery']
        if recovery['stock_vendor_boot_sha256'] != profile['references']['vendor_boot']['sha256']:
            raise ValueError('Manifest Recovery and stock profile disagree')
        recipe = work / 'recovery-source'
        export_recipe(recovery_source, recovery['source_revision'], recipe)
        materialized = work / 'materialized'
        subprocess.run([sys.executable, recipe / 'tools/materialize_stock_lcars.py',
                        '--tool-kit', tool_kit, '--stock-vendor-boot', stock['vendor_boot'],
                        '--plugin', work / PACK.RECOVERY_PLUGIN,
                        '--plugin-sha256', recovery['plugin_sha256'],
                        '--expected-image-sha256', recovery['vendor_boot_sha256'],
                        '--output', materialized], check=True, stdout=subprocess.DEVNULL)
        transition = work / 'transition-images'
        transition.mkdir()
        shutil.copyfile(stock['init_boot'], transition / 'init_boot.img')
        (materialized / 'vendor_boot.img').rename(transition / 'vendor_boot.img')
        chain = verify_chain(work, tool_kit, stock, root_pin, profile)
        checked_stock_files(stock_images, profile)
        if PACK.digest(archive) != archive_sha256:
            raise ValueError('Archive changed during preflight')
        receipt = {
            'format': 1, 'archive_sha256': archive_sha256,
            'root_public_key_sha256': root_pin, 'source_revision': manifest['source_revision'],
            'recovery_source_revision': recovery['source_revision'],
            'rehearsal_only': manifest['rehearsal_only'], 'avb_chain_verified': True,
            'stock_profile_sha256': hashlib.sha256(profile_bytes).hexdigest(),
            'stock_reference_bytes_verified': True, 'device_contacted': False,
            'installation_authorized': False,
            'files': {str(path.relative_to(work)): {'bytes': path.stat().st_size,
                       'sha256': PACK.digest(path)} for directory in (work / 'images', transition)
                       for path in sorted(directory.iterdir())},
        }
        output.mkdir(mode=0o700)
        for name in ('images', 'transition-images'):
            (work / name).rename(output / name)
        if 'notices_sha256' in recovery:
            notice = Path(PACK.RECOVERY_NOTICES).name
            (work / PACK.RECOVERY_NOTICES).rename(output / notice)
            receipt['recovery_notices_sha256'] = recovery['notices_sha256']
        (output / 'avb-chain-report.json').write_text(json.dumps(chain, indent=2) + '\n')
        (output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('archive', 'stock-images', 'recovery-source', 'tool-kit', 'output'):
        parser.add_argument('--' + option, type=Path, required=True)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--root-public-key-sha256', required=True)
    parser.add_argument('--allow-offline-rehearsal', action='store_true')
    args = parser.parse_args()
    try:
        result = prepare(args.archive, args.archive_sha256, args.stock_images, args.recovery_source,
                         args.tool_kit, args.root_public_key_sha256, args.output,
                         allow_rehearsal=args.allow_offline_rehearsal)
    except (OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError, zipfile.BadZipFile) as error:
        parser.exit(1, f'LCARS preflight failed: {error}\n')
    print(json.dumps(result, indent=2))
