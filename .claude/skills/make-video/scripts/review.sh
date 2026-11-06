#!/usr/bin/env bash
# Make a contact sheet (grid of stills) from a rendered video so Claude can LOOK at it.
# Usage: review.sh <video.mp4> [out.png] [every_n_seconds=1]
set -euo pipefail
in="$1"; out="${2:-${1%.*}-sheet.png}"; step="${3:-1}"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
n=$(python3 -c "import math;print(max(1,math.ceil($dur/$step)))")
cols=5; rows=$(( (n + cols - 1) / cols ))
ffmpeg -y -loglevel error -i "$in" \
  -vf "fps=1/$step,scale=270:-2,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%{pts\:hms}':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,tile=${cols}x${rows}:padding=6:color=black" \
  -frames:v 1 "$out"
echo "duration ${dur}s -> $out"
