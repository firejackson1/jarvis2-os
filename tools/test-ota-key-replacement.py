#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exercise actual pinned releasetools functions without signing or private keys."""
import argparse
import ast
import io
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import zipfile


def verify(source):
    tree = ast.parse(Path(source).read_text())
    wanted = {'WriteOtacerts', 'ReplaceOtaKeys'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    if {n.name for n in nodes} != wanted:
        raise ValueError('Missing native OTA replacement functions')
    # Only exercise these actual functions. Stub transport helpers, not their logic.
    common = SimpleNamespace(
        ExternalError=RuntimeError,
        ZipWrite=lambda z, filename, arcname=None: z.write(filename, arcname=arcname),
        ZipClose=lambda z: z.close(),
        ZipWriteStr=lambda z, name, data: z.writestr(name, data))
    options = SimpleNamespace(key_map={})
    ns = dict(io=io, os=os, re=re, zipfile=zipfile, common=common, OPTIONS=options)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
    with tempfile.TemporaryDirectory() as tmp:
        key = Path(tmp) / 'private-host-path' / 'releasekey'
        key.parent.mkdir()
        # Public-only synthetic bytes: neither a real key nor a signing operation.
        cert = b'PUBLIC CERTIFICATE FIXTURE\n'
        key.with_suffix('.x509.pem').write_bytes(cert)
        options.key_map['build/make/target/product/security/testkey'] = str(key)
        for keys in ('build/make/target/product/security/testkey.x509.pem\n', ''):
            incoming, outgoing = io.BytesIO(), io.BytesIO()
            with zipfile.ZipFile(incoming, 'w') as z:
                z.writestr('META/otakeys.txt', keys)
                z.writestr('SYSTEM/system/etc/security/otacerts.zip', b'old trust')
                z.writestr('RECOVERY/RAMDISK/system/etc/security/otacerts.zip', b'old trust')
            incoming.seek(0)
            with zipfile.ZipFile(incoming) as original, zipfile.ZipFile(outgoing, 'w') as result:
                ns['ReplaceOtaKeys'](original, result, {})
            outgoing.seek(0)
            with zipfile.ZipFile(outgoing) as result:
                for name in result.namelist():
                    with zipfile.ZipFile(io.BytesIO(result.read(name))) as certs:
                        if certs.namelist() != ['releasekey.x509.pem']:
                            raise ValueError('OTA trust archive retains host paths or wrong keys')
                        if certs.read('releasekey.x509.pem') != cert:
                            raise ValueError('OTA public certificate bytes changed')
    return {'passed': True, 'explicit_and_empty_key_lists': True,
            'system_and_recovery_certificates': True, 'host_paths_excluded': True,
            'real_certificate_validation': False, 'signing_performed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.source), indent=2))
