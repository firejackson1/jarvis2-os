#!/usr/bin/env python3
"""Assemble an explicit, pinned source whitelist; never fetch or execute inputs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import tarfile
import zipfile


def safe_path(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError(f'unsafe path: {value!r}')
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or '..' in path.parts or str(path) != value or ':' in value:
        raise ValueError(f'unsafe path: {value!r}')
    return path


def member_path(name):
    # Upstream tarballs commonly use a harmless ./ prefix and trailing slash.
    while name.startswith('./'):
        name = name[2:]
    name = name.rstrip('/')
    return str(safe_path(name)) if name and name != '.' else None


def check_archive(path, kind, external_source_links=None):
    seen = set()
    external_source_links = external_source_links or {}
    used_links = set()

    def check(name):
        name = member_path(name)
        if name is not None:
            if name in seen:
                raise ValueError(f'duplicate archive member: {name}')
            seen.add(name)
        return name

    if kind == 'zip':
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                check(item.filename)
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('ZIP symlink not permitted')
    elif kind == 'tar':
        with tarfile.open(path, 'r:*') as archive:
            for item in archive:
                name = check(item.name)
                if item.issym() or item.islnk():
                    target = item.linkname
                    if not name or target.startswith('/') or '\\' in target:
                        raise ValueError('unsafe archive link')
                    target = posixpath.normpath(posixpath.join(
                        posixpath.dirname(name) if item.issym() else '', target))
                    try:
                        safe_path(target)
                    except ValueError:
                        if not item.issym() or external_source_links.get(name) != item.linkname:
                            raise ValueError(f'unsafe source link in {path.name}: {name} -> {item.linkname}')
                        # Preserve exact upstream metadata, never extract or follow it.
                        used_links.add(name)
                elif not (item.isfile() or item.isdir()):
                    raise ValueError('special archive member not permitted')
    else:
        raise ValueError(f'unknown archive type: {kind}')
    if used_links != set(external_source_links):
        raise ValueError('unused or mismatched external source link declaration')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def assemble(manifest, roots, output):
    if manifest.get('format') != 1 or not isinstance(manifest.get('files'), list):
        raise ValueError('unsupported manifest')
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    entries = []
    destinations = {'SOURCE-BUNDLE.json'}
    for item in manifest['files']:
        relative = safe_path(item['path'])
        destination = str(safe_path(item['destination']))
        if destination in destinations:
            raise ValueError(f'duplicate destination: {destination}')
        if any(destination.startswith(prior + '/') or prior.startswith(destination + '/')
               for prior in destinations):
            raise ValueError(f'file/directory destination collision: {destination}')
        destinations.add(destination)
        root = Path(roots[item['root']]).resolve(strict=True)
        path = root.joinpath(*relative.parts)
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root) or not path.is_file():
            raise ValueError(f'unsafe input: {relative}')
        if not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError('invalid SHA256')
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError(f'input hash/size mismatch: {relative}')
        if item.get('archive'):
            check_archive(path, item['archive'], item.get('external_source_links'))
        entries.append((destination, path, item))
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    # Exclusive creation, normalized tar metadata, and no gzip filename/time fields.
    created = False
    try:
        with output.open('xb') as raw:
            created = True
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0, compresslevel=6) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.PAX_FORMAT) as archive:
                    import io
                    info = tarfile.TarInfo('SOURCE-BUNDLE.json')
                    info.mode = 0o644
                    info.size = len(encoded)
                    archive.addfile(info, io.BytesIO(encoded))
                    for destination, path, item in sorted(entries):
                        info = tarfile.TarInfo(destination)
                        info.mode = 0o644
                        info.size = item['bytes']
                        # Hash the bytes actually written, including concurrent changes.
                        class CheckedReader:
                            def __init__(self, stream):
                                self.stream = stream
                                self.hash = hashlib.sha256()

                            def read(self, size):
                                data = self.stream.read(size)
                                self.hash.update(data)
                                return data

                        with path.open('rb') as stream:
                            checked = CheckedReader(stream)
                            archive.addfile(info, checked)
                            if stream.read(1) or checked.hash.hexdigest() != item['sha256']:
                                raise ValueError(f'input changed during assembly: {destination}')
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise
    return digest(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--root', action='append', default=[], metavar='NAME=DIR')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    roots = {}
    for value in args.root:
        name, path = value.split('=', 1)
        if name in roots:
            parser.error(f'duplicate root: {name}')
        roots[name] = Path(path)
    result = assemble(json.loads(args.manifest.read_text()), roots, args.output)
    print(json.dumps({'file': args.output.name, 'bytes': args.output.stat().st_size, 'sha256': result}))


if __name__ == '__main__':
    main()
