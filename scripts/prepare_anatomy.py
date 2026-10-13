"""Convert the verified OBJ subset into indexed browser geometry; no invented anatomy."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent/'research/track-a-feasibility/anatomy'
manifest = json.loads((SOURCE/'manifest.json').read_text())
vessels = {part: group for group in ['LAD','LCX','RCA'] for part in manifest['groups'][group]}
groups = {key: {'positions': [], 'indices': [], 'parts': []} for key in ['heart','LAD','LCX','RCA']}
for part in manifest['groups']['heart']:
    group = groups[vessels.get(part,'heart')]
    offset = len(group['positions'])//3
    count = 0
    for line in (SOURCE/'meshes'/f'{part}.obj').read_text().splitlines():
        words = line.split()
        if not words: continue
        if words[0] == 'v':
            group['positions'].extend(round(float(v),4) for v in words[1:4]); count+=1
        elif words[0] == 'f':
            ids = [int(v.split('/')[0]) for v in words[1:]]
            ids = [offset + (n-1 if n>0 else count+n) for n in ids]
            for k in range(1,len(ids)-1): group['indices'].extend([ids[0],ids[k],ids[k+1]])
    group['parts'].append(part)
target = ROOT/'public/assets'
target.mkdir(parents=True,exist_ok=True)
(target/'anatomy.json').write_text(json.dumps({'groups':groups,'attribution':manifest['attribution'],
    'concepts':manifest['concepts'],'license_url':manifest['license_url'],
    'changes':'OBJ triangulated and grouped by official PART-OF membership; no anatomical deformation.'},separators=(',',':')))
shutil.copyfile(SOURCE/'manifest.json',target/'anatomy-provenance.json')
print({k:{'vertices':len(g['positions'])//3,'triangles':len(g['indices'])//3} for k,g in groups.items()})
