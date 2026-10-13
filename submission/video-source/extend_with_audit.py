"""Rebuild the original six chapters and prepend an actual full-cohort audit.

New opening uses saved CUA browser screenshots, not fabricated UI or interaction.
English narration is the bundled locally generated Kokoro recording.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
with wave.open(str(ROOT/'assets/voice-audit.wav')) as audio:
    voice_duration=audio.getnframes()/audio.getframerate()
duration=round(voice_duration+2,3)
for name in ['cohort-stable-lcx-miss.png','arbitrary-case-anatomy.png']:
    shutil.copyfile(PROJECT/'output/cohort-browser-review'/name,ROOT/'assets'/name)
subprocess.run([sys.executable,str(ROOT/'build_video.py')],cwd=ROOT,check=True)

cuts=[(0,24,'All 242 development records. All five folds.','Outcome-aware filters expose missed positives and false alarms.'),
      (24,39,'Five profiles agree. This recorded positive is missed.','UCI411-020 · full LCX estimate 22.2% · research cutoff 33.0%'),
      (39,duration,'Open the same record in the anatomy and explanation.','4,840 actual-SHAP checks · development audit · final 61 unchanged')]
scenes=''.join(f'<section id="audit-title-{i}" class="clip audit-copy" data-start="{start}" data-duration="{end-start}" data-track-index="3"><h1>{title}</h1><p>{note}</p></section>' for i,(start,end,title,note) in enumerate(cuts))
chapter=f'''<!doctype html><html><head><meta charset="utf-8"/></head><body><template>
<style>#audit-opening{{position:absolute;inset:0;width:100%;height:100%;background:#0b141d;color:#edf5f6;font-family:sans-serif}}
#audit-opening .audit-copy{{position:absolute;left:70px;top:56px;width:1780px;height:122px}}#audit-opening h1{{font-size:43px;line-height:1.15;letter-spacing:-1px;margin:0 0 14px}}#audit-opening p{{font-size:24px;line-height:1.4;color:#bcd7de}}
#audit-opening .audit-capture{{position:absolute;left:235px;top:210px;width:1450px;height:816px;object-fit:contain;border:1px solid #375565}}
#audit-opening .audit-source{{position:absolute;left:235px;top:181px;font:18px monospace;color:#98c5bd}}#audit-opening .audit-footer{{position:absolute;left:70px;bottom:17px;font:18px sans-serif;color:#bdd0d8}}
</style><div id="audit-opening" data-composition-id="audit-opening" data-width="1920" data-height="1080" data-duration="{duration}">
{scenes}<div class="audit-source">ACTUAL APPLICATION SCREENSHOTS · STATIC CAPTURES</div>
<img id="audit-roster-capture" class="clip audit-capture" src="assets/cohort-stable-lcx-miss.png" data-start="0" data-duration="39" data-track-index="1"/>
<img id="audit-anatomy-capture" class="clip audit-capture" src="assets/arbitrary-case-anatomy.png" data-start="39" data-duration="{duration-39}" data-track-index="1"/>
<div class="audit-footer">Educational research · recorded development outcomes used for selection · not clinical validation</div></div>
<script>window.__timelines['audit-opening']=gsap.timeline({{paused:true}});</script></template></body></html>'''
(ROOT/'compositions/audit-opening.html').write_text(chapter)
html=(ROOT/'index.html').read_text()
html=re.sub(r'data-start="([0-9.]+)"',lambda m:f'data-start="{float(m.group(1))+duration:.3f}"',html)
timeline=json.loads((ROOT/'timeline-manifest.json').read_text())
total=round(timeline['duration']+duration,3)
html=html.replace(f'data-duration="{timeline["duration"]:.3f}"',f'data-duration="{total:.3f}"',1)
mount=f'<div id="mount-audit" class="clip" data-composition-id="audit-opening" data-composition-src="compositions/audit-opening.html" data-start="0" data-duration="{duration}" data-track-index="0" data-width="1920" data-height="1080"></div><audio id="voice-audit" src="assets/voice-audit.wav" data-start=".8" data-duration="{voice_duration:.3f}" data-track-index="2"></audio>'
html=html.replace('<div id="mount-01"',mount+'<div id="mount-01"',1)
(ROOT/'index.html').write_text(html)
timeline['duration']=total
for chapter in timeline['chapters']:chapter['start']=round(chapter['start']+duration,3)
timeline['chapters'].insert(0,{'id':'audit','start':0,'duration':duration,'title':'Challenge the complete development cohort'})
timeline['audit_opening']={'media':'Actual CUA static screenshots, explicitly labelled; no simulated interaction',
    'narration':'Bundled local Kokoro ONNX af_heart, speed .93, en-us',
    'sources':{name:{'sha256':hashlib.sha256((ROOT/'assets'/name).read_bytes()).hexdigest(),'bytes':(ROOT/'assets'/name).stat().st_size}
               for name in ['cohort-stable-lcx-miss.png','arbitrary-case-anatomy.png','voice-audit.wav','audit-opening.txt']}}
(ROOT/'timeline-manifest.json').write_text(json.dumps(timeline,indent=2)+'\n')
with (ROOT/'storyboard.md').open('a') as document:document.write('\nOpening: complete development audit, 242 records/5 folds; actual static application screenshots and locally generated English narration. All-five agreement counterexample, arbitrary record/excluding-fold explanation, 4840 actualSHAP checks. Final61 unchanged.\n')
print(json.dumps({'opening_seconds':duration,'total_seconds':total},indent=2))
