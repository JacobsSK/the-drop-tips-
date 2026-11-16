#!/usr/bin/env python3
"""Royalty-free background music bed, synthesised locally (no samples, no licences), plus a ducked final mix.

  python music.py make <out.wav> --duration 25 [--bpm 96] [--mood warm|bright|calm] [--seed 1]
  python music.py duck <voice_and_sfx.mp3> <music.wav> <out.mp3> [--level 0]
      Mixes the music under the voice, ducking it whenever the voice speaks (sidechain compression),
      and fades it in and out. --level is extra gain in dB on top of the -26 LUFS music (default 0).

Moods: warm  (I–V–vi–IV in A major, soft pad + light beat)      — default, friendly/coaching
       bright (I–vi–IV–V in C major, plucky arps + beat)          — upbeat lists, recipes
       calm  (vi–IV–I–V in D major, pad only, no drums)          — reassuring / honest angles
Needs numpy + soundfile (the Kokoro venv has both) and ffmpeg.
"""
import sys, subprocess
import numpy as np, soundfile as sf

SR = 44100
A = sys.argv[1:]
opt = lambda k, d: A[A.index(k) + 1] if k in A else d

def note(m):  # midi -> Hz
    return 440.0 * 2 ** ((m - 69) / 12)

MOODS = {
    'warm':   dict(root=57, prog=[[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]], drums=True, arp=False),
    'bright': dict(root=60, prog=[[0, 4, 7], [9, 12, 16], [5, 9, 12], [7, 11, 14]], drums=True, arp=True),
    'calm':   dict(root=62, prog=[[9, 12, 16], [5, 9, 12], [0, 4, 7], [7, 11, 14]], drums=False, arp=False),
}

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

def make(out, dur, bpm, mood, seed):
    rng = np.random.default_rng(seed); M = MOODS[mood]
    n = int(dur * SR); t = np.arange(n) / SR
    beat = 60 / bpm; bar = beat * 4
    L = np.zeros(n); R = np.zeros(n)
    # --- pad: detuned saws -> lowpass, one chord per bar, slow swell
    for b in range(int(np.ceil(dur / bar))):
        s, e = int(b * bar * SR), min(n, int((b + 1) * bar * SR) + int(.3 * SR))
        if s >= n: break
        tt = np.arange(e - s) / SR; chord = M['prog'][b % 4]
        env = np.minimum(1, tt / .6) * np.minimum(1, (len(tt) / SR - tt) / .5 + .001)
        for k, iv in enumerate(chord):
            f = note(M['root'] + iv)
            for det, pan in [(-0.12, -0.6), (0.12, 0.6)]:
                ph = 2 * np.pi * f * (1 + det / 100) * tt
                w = (2 * ((ph / (2 * np.pi)) % 1) - 1) * .5 + np.sin(ph) * .5
                g = .06 * env
                L[s:e] += w * g * (1 - pan) / 2; R[s:e] += w * g * (1 + pan) / 2
        # sub bass on the chord root
        fb = note(M['root'] + chord[0] - 24); bass = np.sin(2 * np.pi * fb * tt) * .16 * env
        L[s:e] += bass; R[s:e] += bass
    L = lowpass(L, 1800); R = lowpass(R, 1800)
    # --- plucky arpeggio (bright mood): 8th notes over the chord
    if M['arp']:
        step = beat / 2
        for i in range(int(dur / step)):
            s = int(i * step * SR); chord = M['prog'][int(i * step / bar) % 4]
            f = note(M['root'] + 12 + chord[i % 3] + (12 if i % 8 == 7 else 0))
            tt = np.arange(int(.35 * SR)) / SR; e = min(n, s + len(tt))
            p = (np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 9) * .07
            pan = .4 if i % 2 else -.4
            L[s:e] += p[:e - s] * (1 - pan) / 2; R[s:e] += p[:e - s] * (1 + pan) / 2
    # --- light drums: soft kick on 1 and 3, closed hat on off-beats, rim on 2 and 4
    if M['drums']:
        for i in range(int(dur / beat * 2)):
            s = int(i * beat / 2 * SR)
            if s >= n: break
            if i % 4 == 0:  # kick
                tt = np.arange(int(.35 * SR)) / SR; f = 50 + 70 * np.exp(-tt * 28)
                k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * .45
            elif i % 2 == 1:  # hat
                tt = np.arange(int(.06 * SR)) / SR; hh = rng.standard_normal(len(tt))
                k = (hh - lowpass(hh, 6000)) * np.exp(-tt * 70) * .07
            elif i % 4 == 2:  # soft rim/clap
                tt = np.arange(int(.12 * SR)) / SR; c = rng.standard_normal(len(tt))
                k = (c - lowpass(c, 1500)) * np.exp(-tt * 35) * .1
            else:
                continue
            e = min(n, s + len(k)); L[s:e] += k[:e - s]; R[s:e] += k[:e - s]
    x = np.stack([L, R], 1)
    fade = np.minimum(1, np.minimum(t / 1.0, (dur - t) / 1.5))[:, None]
    x = x * fade; x = x / (np.abs(x).max() + 1e-9) * .89
    raw = out + '.raw.wav'; sf.write(raw, x.astype(np.float32), SR)
    # normalise every mood to the same loudness (-26 LUFS ≈ 12 LU under a -14 LUFS voice)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'loudnorm=I=-26:TP=-3:LRA=11', '-ar', str(SR), out], check=True)
    import os; os.remove(raw); print('music', out, f'{dur:.1f}s', mood, bpm, 'bpm, -26 LUFS')

def duck(voice, music, out, level):
    fc = (f"[1:a]volume={level}dB,aformat=channel_layouts=stereo[m];"
          f"[0:a]aformat=channel_layouts=stereo,asplit=2[v][sc];"
          f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350:makeup=1[md];"
          f"[v][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', voice, '-i', music, '-filter_complex', fc,
                    '-map', '[a]', '-c:a', 'libmp3lame', '-b:a', '192k', out], check=True)
    print('ducked mix', out)

if __name__ == '__main__':
    if A[0] == 'make':
        make(A[1], float(opt('--duration', '25')), float(opt('--bpm', '96')), opt('--mood', 'warm'), int(opt('--seed', '1')))
    elif A[0] == 'duck':
        duck(A[1], A[2], A[3], float(opt('--level', '0')))
