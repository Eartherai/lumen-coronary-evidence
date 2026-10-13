"""Assemble the reviewable source package with a SHA-256 manifest.

No network publication; exclude caches, installed dependencies and scratch media.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ['.gitignore','.gitattributes','.github','README.md','REPRODUCIBILITY.md','THIRD_PARTY_NOTICES.md','LICENSE',
    'requirements-training.txt','package.json','package-lock.json','server.py','inference.py',
    'browser-checks.json','artifacts','public','scripts','tests','training','submission','docs','output/pdf','output/video','output/cohort-browser-review',
    'research/ui-redesign-2026-10-11/DESIGN.md','research/ui-redesign-2026-10-11/font-provenance.json']
EXCLUDED = {'node_modules','__pycache__','.git','.venv','.hyperframes','.media','.thumbnails','.waveform-cache','tmp','dist','screenshots'}


def eligible(path):
    return not any(part in EXCLUDED or part.startswith('work-') for part in path.relative_to(ROOT).parts) and path.suffix not in {'.pyc','.joblib','.tmp'} and not path.name.startswith('.env')


def build():
    parser=argparse.ArgumentParser(); parser.add_argument('--require-complete',action='store_true'); parser.add_argument('--output',type=Path,default=ROOT/'dist',help='Output directory; use a dated directory to preserve older releases'); args=parser.parse_args()
    status_path=ROOT/'submission/release-status.json'
    status=json.loads(status_path.read_text()) if status_path.exists() else {'complete':False}
    if args.require_complete and not status.get('complete'):
        raise SystemExit('Submission is not marked complete. Read submission/release-status.json.')
    paths=[]
    for name in INCLUDE:
        item=ROOT/name
        if item.is_file(): paths.append(item)
        elif item.is_dir(): paths.extend(p for p in item.rglob('*') if p.is_file() and eligible(p))
    # Selected dated audit evidence is portable; raw external participant workbooks
    # and live-server metadata are never part of the submission source package.
    selected_research = {
        'research/browser-compatibility-2026-10-12': {'.json', '.png', '.md', '.txt'},
        'research/independent-ai-review-2026-10-11': None,
        'research/runtime-2026-10-11': {'.json', '.png', '.md'},
        'research/runtime-hardening-2026-10-11': {'.json', '.png', '.md'},
        'research/runtime-hardening-r2-2026-10-11': {'.json', '.png', '.md', '.py'},
        'research/lumen-remaining-hardening-2026-10-11': {'.json', '.md'},
        'research/lumen-external-cohort-2026-10-11': {'.json', '.md', '.txt'},
    }
    for name, suffixes in selected_research.items():
        folder=ROOT/name
        if folder.exists():
            paths.extend(p for p in folder.rglob('*') if p.is_file() and eligible(p)
                         and (suffixes is None or p.suffix in suffixes)
                         and 'control' not in p.relative_to(folder).parts
                         and not p.name.startswith(('server.', 'api-server.')) and p.name != 'neu475-primary-paper.txt')
    paths=sorted(set(paths)); manifest={'schema_version':1,'status':status,'files':{}}
    for path in paths:
        if not eligible(path): continue
        relative=str(path.relative_to(ROOT)); raw=path.read_bytes()
        manifest['files'][relative]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    encoded=json.dumps(manifest,indent=2,sort_keys=True).encode()+b'\n'
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'manifest.json').write_bytes(encoded)
    archive=out/'lumen-submission-source.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in manifest['files']: z.write(ROOT/name,'lumen/'+name)
        z.writestr('lumen/release-manifest.json',encoded)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,meta in manifest['files'].items():
            assert hashlib.sha256(z.read('lumen/'+name)).hexdigest()==meta['sha256']
    print(json.dumps({'archive':str(archive),'files':len(manifest['files']),'bytes':archive.stat().st_size,'complete':bool(status.get('complete'))},indent=2))


if __name__=='__main__': build()
