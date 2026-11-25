#!/usr/bin/env bash
# Finishing pass for a video rendered at 60 fps (render.js ... --fps 60):
#   - motion blur: blends each pair of 60 fps frames into one 30 fps frame (a 180° film shutter),
#     so fast moves (whips, drops, punches) smear naturally instead of strobing
#   - light film grain (luma only) and a soft vignette, which make flat vector frames feel shot, not exported
# Usage: polish.sh <in_60fps.mp4> <out.mp4> [grain=4] [vignette=0.35]
set -euo pipefail
in=$1; out=$2; grain=${3:-4}; vig=${4:-0.35}
ffmpeg -y -loglevel error -i "$in" \
  -vf "tmix=frames=2:weights='1 1',fps=30,vignette=angle=${vig}:mode=forward,noise=c0s=${grain}:c0f=t" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -movflags +faststart -c:a copy "$out"
echo "polished $out"
