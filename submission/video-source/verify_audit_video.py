"""Check encoding and all seven narration alignments; extract real final frames.

Visual review is separately recorded after inspection, never assumed by this script.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'output/video'
video=OUT/'lumen-demo.mp4'
metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
timeline=json.loads((ROOT/'timeline-manifest.json').read_text())
check=json.loads((ROOT/'check-audit.json').read_text())
vs=next(s for s in metadata['streams'] if s['codec_type']=='video')
aus=next(s for s in metadata['streams'] if s['codec_type']=='audio')
segments=[]
for chapter in timeline['chapters']:
    source_path=ROOT/f'assets/voice-{chapter["id"]}.wav'
    source,sr=sf.read(source_path,dtype='float32')
    start=chapter['start']+.8+2
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-i',str(video),'-t','5','-map','0:a:0','-ac','1','-ar',str(sr),'-f','f32le','-'])
    actual=np.frombuffer(raw,dtype='<f4');wanted=source[2*sr:7*sr];n=min(len(actual),len(wanted))
    corr=float(np.dot(actual[:n],wanted[:n])/(np.linalg.norm(actual[:n])*np.linalg.norm(wanted[:n])))
    segments.append({'chapter':chapter['id'],'source_voice':source_path.name,'correlation':corr,'seconds_checked':n/sr,'passed':corr>.9})
duration=float(metadata['format']['duration'])
encoding_ok=vs['width']==1920 and vs['height']==1080 and vs['codec_name']=='h264' and aus['codec_name']=='aac' and abs(duration-timeline['duration'])<.1
frames=OUT/'encoded-audit-frames';frames.mkdir(exist_ok=True)
times=[15,46,*[round(c['start']+min(24,c['duration']/2),3) for c in timeline['chapters'][1:]]]
for i,at in enumerate(times):
    subprocess.run(['ffmpeg','-v','error','-ss',str(at),'-i',str(video),'-frames:v','1','-q:v','2','-y',str(frames/f'frame-{i+1:02d}.jpg')],check=True)
qa={'status':'technical_checks_passed_visual_review_pending' if encoding_ok and check['ok'] and all(s['passed'] for s in segments) else 'failed',
    'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'bytes':video.stat().st_size,'duration_seconds':duration,
    'expected_duration_seconds':timeline['duration'],'width':vs['width'],'height':vs['height'],'fps':vs['avg_frame_rate'],
    'video_codec':vs['codec_name'],'audio_codec':aus['codec_name'],'encoding_checks_passed':encoding_ok,
    'english_audio':True,'narration_generated':'Local Kokoro ONNX af_heart speed .93; synthetic, not human voice',
    'audit_opening':'Actual CUA static screenshots explicitly labelled; recorded development outcomes used for selection',
    'remaining_footage':'Existing actual CUA interaction clips at original speed, then final captured still',
    'composition_checks':{k:{n:v.get(n) for n in ['ok','errorCount','warningCount']} for k,v in check.items() if isinstance(v,dict) and k in ['lint','runtime','layout','motion','contrast']},
    'chapter_audio_alignment':segments,'visual_review':'pending','visual_review_frames_seconds':times,
    'training_gpu_used':False,'cloud_rendering_used':False,'render':'HyperFrames0.8.143 local Apple M5 hardware graphics;24fps2workers',
    'sources':{'timeline-manifest.json':hashlib.sha256((ROOT/'timeline-manifest.json').read_bytes()).hexdigest(),'check-audit.json':hashlib.sha256((ROOT/'check-audit.json').read_bytes()).hexdigest()}}
(OUT/'video-qa.json').write_text(json.dumps(qa,indent=2)+'\n')
(ROOT/'video-qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps({k:qa[k] for k in ['status','duration_seconds','fps','video_sha256','chapter_audio_alignment']},indent=2))
if qa['status']=='failed':raise SystemExit(1)
