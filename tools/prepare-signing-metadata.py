#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare a separate target-files ZIP with signing metadata for shipped files only.

No signing, key reads, image generation or device operations. Native deapexer
must inspect every shipped APEX, including PRESIGNED packages. Only APK/APEX
signing metadata and a missing avb_avbtool default in META/misc_info.txt may
change. Package bytes stay unchanged; this does not enable image AVB or verify
signatures or release trust.
"""
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile

APK_FIELDS = ('name', 'certificate', 'private_key', 'compressed', 'partition')
APEX_FIELDS = ('name', 'public_key', 'private_key', 'container_certificate',
               'container_private_key', 'partition', 'sign_tool')
PARTITIONS = {'SYSTEM', 'SYSTEM_EXT', 'PRODUCT', 'VENDOR', 'ODM', 'OEM',
              'SYSTEM_OTHER', 'SYSTEM_DLKM', 'VENDOR_DLKM', 'ODM_DLKM'}
FIELD = re.compile(r'([a-z_]+)="([^"\r\n]*)"')


def safe_path(name, directory=False):
    value = name[:-1] if directory and name.endswith('/') else name
    if (not value or value.startswith('/') or '\\' in value or
            any(p in ('', '.', '..') for p in value.split('/'))):
        raise ValueError('Unsafe archive or payload path: ' + name)
    return value


def parse_metadata(data, apex=False):
    fields = APEX_FIELDS if apex else APK_FIELDS
    required = set(fields) - ({'sign_tool'} if apex else {'compressed'})
    rows = {}
    for line in data.decode('utf-8').splitlines():
        if not line.strip():
            continue
        row = {}
        end = 0
        for match in FIELD.finditer(line):
            if line[end:match.start()].strip() or (end and match.start() == end):
                raise ValueError('Malformed signing metadata')
            key, value = match.groups()
            if key not in fields or key in row:
                raise ValueError('Unknown or duplicate signing metadata field: ' + key)
            row[key] = value
            end = match.end()
        if line[end:].strip() or not required.issubset(row):
            raise ValueError('Incomplete or malformed signing metadata')
        name = row['name']
        if '/' in name or '\\' in name or not name.endswith('.apex' if apex else '.apk'):
            raise ValueError('Invalid signing metadata package name: ' + name)
        if not re.fullmatch(r'[a-z][a-z0-9_]*', row['partition']):
            raise ValueError('Invalid signing metadata partition')
        if apex:
            if row['container_certificate'] == 'PRESIGNED':
                if any(row[key] != 'PRESIGNED' for key in ('public_key', 'private_key', 'container_private_key')):
                    raise ValueError('Inconsistent PRESIGNED APEX metadata')
            elif (not row['private_key'] or not row['public_key'] or
                  not certificate_pair(row['container_certificate'], row['container_private_key'])):
                raise ValueError('Invalid APEX key metadata')
        elif row['certificate'] in ('PRESIGNED', 'EXTERNAL'):
            if row['private_key']:
                raise ValueError('Special APK certificate must not name a private key')
        elif not certificate_pair(row['certificate'], row['private_key']):
            raise ValueError('Invalid APK key metadata')
        identity = (row['partition'], name)
        if identity in rows and rows[identity] != row:
            raise ValueError('Signing metadata conflict: ' + str(identity))
        rows[identity] = row
    return rows


def certificate_pair(certificate, private_key):
    return (certificate.endswith('.x509.pem') and private_key.endswith('.pk8') and
            certificate[:-9] == private_key[:-4] and bool(private_key[:-4]))


def prepare_misc_info(data):
    """Supply the APEX signer's tool lookup without enabling image AVB."""
    values = {}
    for line in data.decode('utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if (not separator or not re.fullmatch(r'[A-Za-z0-9_]+', key) or
                key in values or any(ord(char) < 32 and char != '\t' for char in value)):
            raise ValueError('Malformed or duplicate misc_info key: ' + key)
        values[key] = value
    if 'avb_avbtool' in values:
        # One bare executable name or POSIX path, with no arguments or controls.
        if not re.fullmatch(r'/?[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*', values['avb_avbtool']):
            raise ValueError('Malformed avb_avbtool executable path in misc_info')
        return data, False
    separator = b'' if not data or data.endswith(b'\n') else b'\n'
    return data + separator + b'avb_avbtool=avbtool\n', True


def inspect_apex(data, compressed, tools):
    """List actual payload entries; never accept a caller-supplied inventory."""
    with tempfile.TemporaryDirectory(prefix='signing-metadata-') as temp:
        if compressed:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                validate_archive(z)
                data = z.read('original_apex')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            validate_archive(z)
            for required in ('apex_payload.img', 'apex_manifest.pb', 'apex_pubkey'):
                if required not in z.namelist():
                    raise ValueError('APEX is missing ' + required)
        path = Path(temp) / 'package.apex'
        path.write_bytes(data)
        deapexer, debugfs, fsckerofs = map(str, tools)
        listing = subprocess.check_output(
            [deapexer, '--debugfs_path', debugfs, '--fsckerofs_path', fsckerofs,
             'list', str(path)], text=True)
        entries = set()
        apks = []
        for entry in listing.split():
            # Native deapexer includes the payload root and directory entries.
            if entry in ('.', './'):
                continue
            entry = entry.removeprefix('./')
            name = safe_path(entry, directory=entry.endswith('/'))
            if name in entries:
                raise ValueError('Duplicate APEX payload path: ' + name)
            entries.add(name)
            if name.endswith('.apk'):
                apks.append(name)
            elif '.apk.' in PurePosixPath(name).name:
                raise ValueError('Unsupported compressed embedded APK: ' + name)
        return apks


def validate_archive(z):
    names = set()
    for info in z.infolist():
        safe_path(info.filename, directory=info.is_dir())
        if info.filename in names:
            raise ValueError('Archive contains duplicate entry: ' + info.filename)
        names.add(info.filename)
        if info.flag_bits & 1:
            raise ValueError('Encrypted archive entries are unsupported')
        if (info.filename in ('META/apkcerts.txt', 'META/apexkeys.txt', 'META/misc_info.txt') or
                info.filename.endswith(('.apk', '.apk.gz', '.apex', '.capex'))):
            mode = info.external_attr >> 16
            if info.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError('Package must be a regular archive entry: ' + info.filename)


def prepare(input_path, output_path, tools):
    input_path, output_path = Path(input_path), Path(output_path)
    if input_path.is_symlink() or not input_path.is_file():
        raise ValueError('Input archive must be a regular file, not a symlink')
    if output_path.exists():
        raise FileExistsError(output_path)
    selected_apks, selected_apexes, basename_keys = {}, {}, {}
    counts = {'standalone_apks': 0, 'embedded_apks': 0, 'apexes': 0}
    with zipfile.ZipFile(input_path) as source:
        validate_archive(source)
        apk_rows = parse_metadata(source.read('META/apkcerts.txt'))
        apex_rows = parse_metadata(source.read('META/apexkeys.txt'), apex=True)
        if 'META/misc_info.txt' not in source.namelist():
            raise ValueError('Required META/misc_info.txt is missing')
        misc_info, avbtool_defaulted = prepare_misc_info(source.read('META/misc_info.txt'))

        def select_apk(partition, name, compressed=None):
            identity = (partition, name)
            row = apk_rows.get(identity)
            if row is None:
                raise ValueError('Missing APK metadata: ' + str(identity))
            if row.get('compressed') != compressed:
                raise ValueError('APK compression metadata differs from archive: ' + name)
            effective = (row['certificate'], row['private_key'])
            if name in basename_keys and basename_keys[name] != effective:
                raise ValueError('Conflicting basename signing keys: ' + name)
            basename_keys[name] = effective
            selected_apks[identity] = row

        apex_names = {}
        for info in source.infolist():
            path = info.filename
            if not path.endswith(('.apk', '.apk.gz', '.apex', '.capex')):
                continue
            partition = path.split('/')[0]
            if partition not in PARTITIONS or '/' not in path:
                raise ValueError('Unsupported package partition: ' + path)
            partition = partition.lower()
            name = PurePosixPath(path).name
            if path.endswith(('.apk', '.apk.gz')):
                compressed = 'gz' if name.endswith('.gz') else None
                select_apk(partition, name.removesuffix('.gz'), compressed)
                counts['standalone_apks'] += 1
            else:
                name = name.removesuffix('.capex') + '.apex' if name.endswith('.capex') else name
                identity = (partition, name)
                row = apex_rows.get(identity)
                if row is None:
                    raise ValueError('Missing APEX metadata: ' + str(identity))
                if name in apex_names:
                    raise ValueError('Ambiguous APEX basename: ' + name)
                apex_names[name] = path
                selected_apexes[identity] = row
                for embedded in inspect_apex(source.read(info), path.endswith('.capex'), tools):
                    select_apk(partition, PurePosixPath(embedded).name)
                    counts['embedded_apks'] += 1
                counts['apexes'] += 1
        # AOSP uses one global APK compression extension and basename key map.
        extensions = {row['compressed'] for row in selected_apks.values() if row.get('compressed')}
        if len(extensions) > 1:
            raise ValueError('Multiple APK compression extensions are unsupported')
        replacements = {'META/misc_info.txt': misc_info}
        for path, rows, fields in [('META/apkcerts.txt', selected_apks, APK_FIELDS),
                                   ('META/apexkeys.txt', selected_apexes, APEX_FIELDS)]:
            replacements[path] = ''.join(' '.join(f'{key}="{row[key]}"' for key in fields if key in row) + '\n'
                                         for _, row in sorted(rows.items())).encode()
        changed_metadata = [path for path, data in replacements.items() if data != source.read(path)]
        # Publish atomically without replacing an existing output, including races.
        with tempfile.TemporaryDirectory(prefix='.signing-metadata-', dir=output_path.parent) as temp:
            staged = Path(temp) / 'prepared.zip'
            with staged.open('xb') as stream:
                os.fchmod(stream.fileno(), 0o600)
                with zipfile.ZipFile(stream, 'w') as dest:
                    dest.comment = source.comment
                    for info in source.infolist():
                        if info.filename in replacements:
                            dest.writestr(info, replacements[info.filename])
                        else:
                            with source.open(info) as reader, dest.open(info, 'w') as writer:
                                shutil.copyfileobj(reader, writer, length=1024 * 1024)
            os.link(staged, output_path)
    return dict(counts, apk_metadata_rows=len(selected_apks), apex_metadata_rows=len(selected_apexes),
                signed=False, package_bytes_changed=False,
                avb_avbtool_defaulted=avbtool_defaulted, metadata_entries_changed=sorted(changed_metadata))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deapexer', type=Path, required=True)
    parser.add_argument('--debugfs', type=Path, required=True)
    parser.add_argument('--fsckerofs', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output, (args.deapexer, args.debugfs, args.fsckerofs)), indent=2))
