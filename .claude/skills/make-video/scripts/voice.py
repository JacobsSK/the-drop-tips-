#!/usr/bin/env python3
"""Generate a voiceover phrase by phrase with Kokoro TTS and record each phrase's timing.

  python voice.py <script.json> <outdir> --models <dir with kokoro.onnx + voices.bin> [--voice af_heart] [--speed 1.08]

script.json: [["id", "Text to say.", gap_before_seconds], ...]  (write numbers as words)
Writes <outdir>/vo.mp3 (polished, -14 LUFS) and <outdir>/vo_marks.json: {"total": s, "marks": {id: [start, end]}}.
"""
import sys, json, os, subprocess
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
a = sys.argv[1:]
script, out = a[0], a[1]
opt = lambda k, d: a[a.index(k) + 1] if k in a else d
models = opt('--models', '.'); voice = opt('--voice', 'af_heart'); speed = float(opt('--speed', '1.08'))
k = Kokoro(os.path.join(models, 'kokoro.onnx'), os.path.join(models, 'voices.bin'))
segs = json.load(open(script))
sr = 24000; parts = [np.zeros(int(.25 * sr), np.float32)]; t = .25; marks = {}
for sid, text, gap in segs:
    parts.append(np.zeros(int(gap * sr), np.float32)); t += gap
    x, sr = k.create(text, voice=voice, speed=speed, lang='en-us')
    idx = np.where(np.abs(x) > 0.01)[0]
    x = x[max(0, idx[0] - 240): idx[-1] + 480] if len(idx) else x
    marks[sid] = [round(t, 2), round(t + len(x) / sr, 2)]; parts.append(x.astype(np.float32)); t += len(x) / sr
parts.append(np.zeros(int(1.2 * sr), np.float32)); t += 1.2
raw = os.path.join(out, 'vo_raw.wav'); sf.write(raw, np.concatenate(parts), sr)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
  'highpass=f=80,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7',
  '-ar', '44100', '-c:a', 'libmp3lame', '-b:a', '192k', os.path.join(out, 'vo.mp3')], check=True)
os.remove(raw)
json.dump({'total': round(t, 2), 'marks': marks}, open(os.path.join(out, 'vo_marks.json'), 'w'), indent=1)
print(json.dumps(marks)); print('total', round(t, 2))
