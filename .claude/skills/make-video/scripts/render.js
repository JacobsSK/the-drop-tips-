#!/usr/bin/env node
// Render an HTML "video page" to MP4: open it in headless Chromium, step a
// virtual clock frame by frame, screenshot every frame, pipe frames to ffmpeg.
//
// Usage:
//   node render.js <scene.html> <out.mp4> [--fps 30] [--width 1080] [--height 1920]
//        [--duration <sec>] [--audio <file>] [--audio-volume 1.0] [--from <sec>] [--crf 18]
//
// The page controls itself through two optional hooks:
//   window.VIDEO = { duration: 15, width: 1080, height: 1920, fps: 30 }   // defaults
//   window.renderFrame = (t) => { ... }   // t = seconds; draw the frame for time t (may be async)
// CSS animations / Web Animations are also paused and seeked to t automatically,
// so plain @keyframes work too.

const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function parseArgs(argv) {
  const pos = [];
  const opt = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) opt[a.slice(2)] = argv[++i];
    else pos.push(a);
  }
  return { pos, opt };
}

(async () => {
  const { pos, opt } = parseArgs(process.argv.slice(2));
  if (pos.length < 2) {
    console.error('usage: node render.js <scene.html> <out.mp4> [--fps 30] [--duration sec] [--audio file]');
    process.exit(2);
  }
  const input = path.resolve(pos[0]);
  const output = path.resolve(pos[1]);
  if (!fs.existsSync(input)) { console.error('no such file: ' + input); process.exit(2); }

  const browser = await chromium.launch();
  // First load at a probe size to read window.VIDEO.
  let page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + input + '?render=1', { waitUntil: 'load' });
  const cfg = await page.evaluate(() => window.VIDEO || {});
  const fps = Number(opt.fps || cfg.fps || 30);
  const width = Number(opt.width || cfg.width || 1080);
  const height = Number(opt.height || cfg.height || 1920);
  const duration = Number(opt.duration || cfg.duration || 10);
  const from = Number(opt.from || 0);
  const crf = String(opt.crf || 18);
  await page.close();

  page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + input + '?render=1', { waitUntil: 'load' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  // Wait for every <img> to finish loading.
  await page.evaluate(() => Promise.all([...document.images].map((img) =>
    img.complete ? null : new Promise((r) => { img.onload = img.onerror = r; }))));

  const frames = Math.round((duration - from) * fps);
  const ffArgs = ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'];
  if (opt.audio) ffArgs.push('-ss', String(from), '-i', path.resolve(opt.audio));
  ffArgs.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', crf, '-preset', 'medium',
    '-r', String(fps), '-movflags', '+faststart');
  if (opt.audio) {
    const vol = opt['audio-volume'] || '1.0';
    ffArgs.push('-filter:a', `volume=${vol},afade=t=out:st=${Math.max(0, duration - from - 0.6)}:d=0.6`,
      '-c:a', 'aac', '-b:a', '192k', '-shortest');
  }
  ffArgs.push(output);
  const ff = spawn('ffmpeg', ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
  const ffDone = new Promise((res, rej) => ff.on('close', (c) => c === 0 ? res() : rej(new Error('ffmpeg exited ' + c))));

  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    const t = from + i / fps;
    await page.evaluate(async (t) => {
      for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
      if (typeof window.renderFrame === 'function') await window.renderFrame(t);
    }, t);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % fps === 0) process.stdout.write(`\rframe ${i}/${frames}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  ff.stdin.end();
  await ffDone;
  await browser.close();
  process.stdout.write(`\rrendered ${frames} frames (${width}x${height} @ ${fps}fps, ${duration - from}s) in ${((Date.now() - t0) / 1000).toFixed(0)}s\n`);
  console.log('wrote ' + output);
  if (errors.length) {
    console.error('PAGE ERRORS (fix these):\n  ' + [...new Set(errors)].join('\n  '));
    process.exit(1);
  }
})().catch((e) => { console.error(e); process.exit(1); });
