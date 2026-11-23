#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply TV Settings patches to copies and compile changed Java; no source/device writes."""
import argparse
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
def run(command,**kwargs):return subprocess.check_output(list(map(str,command)),stderr=subprocess.STDOUT,**kwargs)
def verify(source,out):
    source=source.resolve();out=out.resolve()
    if any(out==base or base in out.parents for base in (source,ROOT.resolve())):
        raise ValueError('Output must be outside source directories')
    project=source/'packages/apps/TvSettings'
    manifest=ET.parse(ROOT/'manifests/lineage21-pinned.xml').getroot()
    expected=next(n.get('revision') for n in manifest.findall('project') if n.get('path')=='packages/apps/TvSettings')
    git=['git','-c','safe.directory='+str(project),'-C',str(project)]
    actual=run(git+['rev-parse','HEAD'],text=True).strip()
    if actual!=expected:raise ValueError('TV Settings HEAD differs from pinned manifest')
    out.mkdir(parents=True,exist_ok=False);work=out/'tree';work.mkdir()
    patch_dir=ROOT/'patches/TvSettings'
    patches=[patch_dir/name for name in (patch_dir/'series').read_text().splitlines() if name]
    paths=set()
    for patch in patches:
        for line in patch.read_text().splitlines():
            if line.startswith('--- a/'):
                relative=PurePosixPath(line[6:])
                if relative.is_absolute() or '..' in relative.parts:raise ValueError('Invalid patch path')
                paths.add(str(relative))
    for name in sorted(paths):
        p=work/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(run(git+['show','HEAD:'+name]))
    run(['git','init','-q',work])
    for patch in patches:
        run(['git','-C',work,'apply','--check',patch])
        run(['git','-C',work,'apply',patch])
    flags={};active=False
    with (source/'out/soong/build.lineage_jarvis2.ninja').open() as f:
        for line in f:
            if 'tags = module_name=TvSettingsStaticLibs;' in line and 'rule_name=javac' in line:active=True
            elif active:
                if not line.strip():break
                if '=' in line:
                    key,value=line.strip().split('=',1);flags[key.strip()]=value.strip()
    cp=shlex.split(flags['classpath']);system=shlex.split(flags['bootClasspath'])
    if cp[0]!='-classpath' or len(cp)!=2 or len(system)!=1 or not system[0].startswith('--system='):
        raise ValueError('Unrecognized javac build inputs')
    jars=[str(source/p) for p in cp[1].split(':')]
    combined=list((source/'out/soong/.intermediates/packages/apps/TvSettings/TvSettingsTwoPanel/android_common').glob('*/combined/TvSettingsTwoPanel.jar'))
    if len(combined)!=1:raise ValueError('Expected one matching Settings combined jar')
    jars.append(str(combined[0]));classes=out/'classes';classes.mkdir()
    java=[str(work/p) for p in sorted(paths) if p.endswith('.java')]
    javac=source/'prebuilts/jdk/jdk17/linux-x86/bin/javac'
    command=[javac,'-J-Xmx512m','-proc:none','-source',flags['javaVersion'],'-target',flags['javaVersion'],
             '--system='+str(source/system[0].split('=',1)[1]),'-classpath',':'.join(jars),'-d',classes]+java
    log=run(command,text=True);(out/'javac.log').write_text(log)
    summary={'tvsettings_revision':actual,'patches':[p.name for p in patches], 'compiled_sources':java and [p for p in sorted(paths) if p.endswith('.java')],
             'classes':len(list(classes.rglob('*.class'))),'source_tree_modified':False,'installed':False}
    (out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('android_tree',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    try:verify(args.android_tree.resolve(),args.output.resolve())
    except subprocess.CalledProcessError as e:
        print(e.output.decode() if isinstance(e.output,bytes) else e.output)
        raise SystemExit(e.returncode)
