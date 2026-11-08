#!/usr/bin/env python3
"""Synthesise sound effects and mix them under a voiceover. Needs numpy + soundfile (the Kokoro venv has both).

  python sfx.py make <outdir>                      -> whoosh.wav whoosh_long.wav impact.wav pop.wav riser.wav tick.wav
  python sfx.py mix <vo.mp3> <cues.json> <out.mp3> [--sfxdir dir] [--sfx-gain 0.55]
      cues.json: [{"t": 3.1, "sfx": "whoosh", "gain": 1.0}, ...]  (t = seconds into the video)
"""
import sys, json, os, subprocess
import numpy as np, soundfile as sf
SR = 44100
rng = np.random.default_rng(7)

def lowpass_sweep(x, f0, f1):
    """One-pole lowpass whose cutoff sweeps f0 -> f1 (log)."""
    n = len(x); fc = np.geomspace(f0, f1, n); a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros(n); acc = 0.0
    for i in range(n):
        acc = (1 - a[i]) * x[i] + a[i] * acc; y[i] = acc
    return y

def env(n, attack, release_shape=2.0):
    t = np.linspace(0, 1, n); k = attack
    return np.where(t < k, (t / k) ** 1.5, ((1 - t) / (1 - k)) ** release_shape)

def stereo(m, pan_from=-0.6, pan_to=0.6):
    p = np.linspace(pan_from, pan_to, len(m)); l = m * np.sqrt((1 - p) / 2); r = m * np.sqrt((1 + p) / 2)
    return np.stack([l, r], 1)

def norm(x, peak=0.9): return x / (np.abs(x).max() + 1e-9) * peak

def whoosh(dur=0.45, f0=300, f1=6000):
    n = int(SR * dur); noise = rng.standard_normal(n)
    up = lowpass_sweep(noise, f0, f1)[: n // 2]; down = lowpass_sweep(noise[n // 2:], f1, f0 * 1.5)
    m = np.concatenate([up, down]) - lowpass_sweep(np.concatenate([up, down]), 120, 120)  # remove rumble
    return stereo(norm(m * env(n, 0.55, 1.6)))

def impact(dur=0.7):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 7) + 38; ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 6)
    click = lowpass_sweep(rng.standard_normal(n), 4000, 300) * np.exp(-t * 40) * .6
    return stereo(norm(np.tanh((body + click) * 2.2)), 0, 0)

def pop(dur=0.12):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 900 * np.exp(-t * 30) + 380; m = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    return stereo(norm(m, .8), 0, 0)

def riser(dur=1.2):
    n = int(SR * dur); m = lowpass_sweep(rng.standard_normal(n), 200, 9000) * np.linspace(0, 1, n) ** 2
    return stereo(norm(m, .7), -0.2, 0.2)

def tick(dur=0.05):
    n = int(SR * dur); t = np.arange(n) / SR
    return stereo(norm(np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 120), .6), 0, 0)

def make(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, x in [('whoosh', whoosh()), ('whoosh_long', whoosh(0.9, 200, 5000)), ('impact', impact()),
                    ('pop', pop()), ('riser', riser()), ('tick', tick())]:
        sf.write(os.path.join(outdir, name + '.wav'), x.astype(np.float32), SR)
    print('sfx written to', outdir)

def mix(vo, cues, out, sfxdir, gain):
    cues = json.load(open(cues))
    args = ['ffmpeg', '-y', '-loglevel', 'error', '-i', vo]
    parts = []
    for i, c in enumerate(cues):
        args += ['-i', os.path.join(sfxdir, c['sfx'] + '.wav')]
        d = int(max(0, c['t']) * 1000); g = gain * c.get('gain', 1.0)
        parts.append(f"[{i+1}:a]volume={g},adelay={d}|{d}[s{i}]")
    ins = '[0:a]' + ''.join(f'[s{i}]' for i in range(len(cues)))
    fc = ';'.join(parts + [f"{ins}amix=inputs={len(cues)+1}:duration=first:normalize=0,alimiter=limit=0.95[a]"])
    args += ['-filter_complex', fc, '-map', '[a]', '-c:a', 'libmp3lame', '-b:a', '192k', out]
    subprocess.run(args, check=True); print('mixed', out)

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'make': make(a[1])
    elif a[0] == 'mix':
        sfxdir = a[a.index('--sfxdir') + 1] if '--sfxdir' in a else os.path.join(os.path.dirname(a[3]) or '.', 'sfx')
        gain = float(a[a.index('--sfx-gain') + 1]) if '--sfx-gain' in a else 0.55
        mix(a[1], a[2], a[3], sfxdir, gain)
