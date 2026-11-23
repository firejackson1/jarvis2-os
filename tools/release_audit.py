#!/usr/bin/env python3
"""Check source candidates without printing sensitive matching content."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DENIED_SUFFIXES = {'.pem','.pk8','.p12','.pfx','.jks','.keystore','.pub','.apk','.apex','.img','.so','.ko'}
PATTERNS = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'device-address': re.compile(rb'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b'),
    'device-serial': re.compile(rb'\bJUSA[0-9]{6,}\b'),
    'private-address': re.compile(rb'\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b'),
    'owner-path': re.compile(rb'/home/' + rb'jedi(?:/|\b)'),
    'trusted-adb-key': re.compile(rb'(?m)^\s*PRODUCT_ADB_KEYS\s*[:+?]?='),
}

def check_file(path, data):
    issues=[]
    if path.suffix.lower() in DENIED_SUFFIXES or path.name.startswith(('adbkey','.env')):
        issues.append('forbidden-artifact')
    if b'\0' in data: issues.append('binary-content')
    for name, pattern in PATTERNS.items():
        if pattern.search(data): issues.append(name)
    return issues

def audit(root, staged=False):
    if staged:
        result=subprocess.run(['git','-C',str(root),'ls-files','--stage','-z'],check=True,stdout=subprocess.PIPE)
        problems=[]
        for entry in result.stdout.split(b'\0'):
            if not entry:continue
            metadata,name=entry.split(b'\t',1);mode,oid,stage=metadata.split()
            relative=Path(name.decode())
            if mode not in (b'100644',b'100755') or stage!=b'0':
                problems.append((str(relative),'unsupported-index-entry'));continue
            data=subprocess.check_output(['git','-C',str(root),'cat-file','blob',oid.decode()])
            for issue in check_file(relative,data):problems.append((str(relative),issue))
        return problems
    result=subprocess.run(['git','-C',str(root),'ls-files','--cached','--others','--exclude-standard','-z'],check=True,stdout=subprocess.PIPE)
    problems=[]
    for raw in sorted(set(result.stdout.split(b'\0'))):
        if not raw:continue
        relative=Path(raw.decode());p=root/relative
        if p.is_symlink():problems.append((str(relative),'symlink'));continue
        if not p.exists():continue
        for issue in check_file(relative,p.read_bytes()):problems.append((str(relative),issue))
    return problems

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',nargs='?',type=Path,default=ROOT);parser.add_argument('--staged',action='store_true')
    args=parser.parse_args();problems=audit(args.root.resolve(),staged=args.staged)
    for name,issue in problems:print(f'{name}: {issue}')
    if problems:raise SystemExit(1)
    print('Source audit passed: no matching private identities, keys or forbidden binary artifacts.')
