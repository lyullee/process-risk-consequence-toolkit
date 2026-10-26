# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Scan allowlisted source/build contents without collecting local secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
IGNORE={'.git','.venv','.pytest_cache','__pycache__','build','dist','artifacts'}
DENIED={'.pdf','.docx','.xlsx','.sqlite','.db','.pem','.key','.pfx'}
patterns=[re.compile(r'gh[pousr]_[A-Za-z0-9]{25,}'),re.compile(r'pypi-[A-Za-z0-9_-]{40,}'),re.compile(r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----'),re.compile(r'[A-Z]:[\\/]Users[\\/]',re.I)]


def inspect(name,data,findings):
    path=Path(name)
    if path.suffix.lower() in DENIED or path.name in {'.pypirc','.env'} or any(p in {'private','source_materials'} for p in path.parts):
        findings.append({'file':name,'reason':'excluded material category'})
    if path.suffix.lower() in {'.py','.md','.json','.yml','.yaml','.toml','.cff','.txt'} or path.name in {'NOTICE','LICENSE'}:
        text=data.decode('utf-8',errors='replace')
        for index,pattern in enumerate(patterns):
            if pattern.search(text):findings.append({'file':name,'reason':f'sensitive-content pattern {index}; content withheld'})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dist',action='store_true')
    args=parser.parse_args()
    findings=[]
    manifest=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or any(p in IGNORE or p.endswith('.egg-info') for p in path.relative_to(ROOT).parts):continue
        if path.name in {'source-manifest.json','release-audit.json'}:continue
        relative=path.relative_to(ROOT).as_posix()
        data=path.read_bytes()
        inspect(relative,data,findings)
        manifest.append({'path':relative,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    archives=[]
    if args.dist:
        for path in sorted((ROOT/'dist').glob('*')):
            if path.suffix=='.whl':
                with zipfile.ZipFile(path) as z:
                    for name in z.namelist():inspect(name,z.read(name),findings)
            elif path.name.endswith('.tar.gz'):
                with tarfile.open(path) as z:
                    for member in z.getmembers():
                        if member.isfile():inspect(member.name,z.extractfile(member).read(),findings)
            else:continue
            archives.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    report={'status':'passed' if not findings else 'failed','scope':'source and selected wheel/sdist contents' if args.dist else 'source',
        'files_scanned':len(manifest),'findings':findings,'archives':archives,'legal_guarantee':False,
        'review_boundary':'Automated exclusions/pattern scan plus documented provenance review; not a judicial opinion or exhaustive IP clearance.'}
    folder=ROOT/'verification'
    folder.mkdir(exist_ok=True)
    (folder/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (folder/'release-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if findings:raise SystemExit(1)


if __name__=='__main__':main()
