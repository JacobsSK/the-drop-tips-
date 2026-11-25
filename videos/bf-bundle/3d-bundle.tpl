<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8" /><title>3D bundle shot</title>
<style>html,body{margin:0;background:#000;overflow:hidden}#stage{position:relative;width:1080px;height:1920px;overflow:hidden}canvas{position:absolute;inset:0}</style>
<script>window.VIDEO_READY = false;</script>
<script type="importmap">{ "imports": { "three": "/.claude/skills/make-video/vendor/three.module.min.js" } }</script>
</head><body><div id="stage"></div>
<script type="module">
import * as THREE from 'three';
// Four books stand in a fan on a dark Black Friday set. FIRST lands at 0.2s, the other three cascade in from 1.3s.
const FIRST = '__FIRST__';
const ORDER = ['br', 'pp', 'bl', 'dc'];
const SPINE = { br: '#8b1050', pp: '#1f4d3a', bl: '#1f8a77', dc: '#26375e' };
window.VIDEO = { width: 1080, height: 1920, fps: 30, duration: 10 };
const W = 1080, H = 1920;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.35;
document.getElementById('stage').prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color('#0a0809'); scene.fog = new THREE.Fog('#0a0809', 9, 19);
const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 100);
scene.add(new THREE.HemisphereLight('#fff3dc', '#120c08', 0.75));
const key = new THREE.DirectionalLight('#ffffff', 2.3); key.position.set(2.5, 7, 6); key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5 }); key.shadow.radius = 5; scene.add(key);
const rimL = new THREE.PointLight('#f5c542', 30, 12); rimL.position.set(-4, 3, -2.5); scene.add(rimL);
const rimR = new THREE.PointLight('#f5c542', 30, 12); rimR.position.set(4, 3, -2.5); scene.add(rimR);
const spot = new THREE.SpotLight('#ffe7b0', 60, 20, 0.5, 0.6); spot.position.set(0, 9, 3); spot.target.position.set(0, 1.4, 0); scene.add(spot, spot.target);
const floor = new THREE.Mesh(new THREE.CircleGeometry(40, 64), new THREE.MeshStandardMaterial({ color: '#16110d', roughness: 0.38, metalness: 0.35 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
const glow = new THREE.Mesh(new THREE.CircleGeometry(2.6, 64), new THREE.MeshBasicMaterial({ color: '#f5c542', transparent: true, opacity: 0.10 }));
glow.rotation.x = -Math.PI / 2; glow.position.y = 0.005; scene.add(glow);
function pagesTexture(vertical) { const c = document.createElement('canvas'); c.width = 256; c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#f6efe9'; g.fillRect(0, 0, 256, 256); g.strokeStyle = 'rgba(120,90,80,.18)';
  for (let i = 0; i < 256; i += 3) { g.beginPath(); vertical ? (g.moveTo(i, 0), g.lineTo(i, 256)) : (g.moveTo(0, i), g.lineTo(256, i)); g.stroke(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; }
const loader = new THREE.TextureLoader();
const bw = 1.3, bh = 1.68, bd = 0.16;
// 2x2 display: br + pp on a glossy riser at the back, bl + dc in front
const X = [-0.72, 0.72, -0.8, 0.8], Z = [-0.95, -0.95, 0.4, 0.4], RY = [0.1, -0.1, 0.16, -0.16], Y0 = [1.3, 1.3, 0, 0];
const riser = new THREE.Mesh(new THREE.BoxGeometry(3.3, 1.3, 1.0), new THREE.MeshStandardMaterial({ color: '#0d0b0c', roughness: 0.25, metalness: 0.5 }));
riser.position.set(0, 0.65, -0.95); riser.receiveShadow = riser.castShadow = true; scene.add(riser);
const edge = new THREE.Mesh(new THREE.BoxGeometry(3.3, 0.04, 0.04), new THREE.MeshBasicMaterial({ color: '#f5c542' }));
edge.position.set(0, 1.3, -0.45); scene.add(edge);
const books = [];
for (const [i, id] of ORDER.entries()) {
  const tex = await loader.loadAsync(`assets/cover-${id}.png`); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const m = (o) => new THREE.MeshStandardMaterial({ roughness: 0.42, ...o });
  const b = new THREE.Mesh(new THREE.BoxGeometry(bw, bh, bd), [m({ map: pagesTexture(false) }), m({ color: SPINE[id] }), m({ map: pagesTexture(true) }),
    m({ map: pagesTexture(true) }), m({ map: tex, roughness: 0.3 }), m({ color: SPINE[id] })]);
  b.castShadow = true; scene.add(b);
  const rank = id === FIRST ? -1 : ORDER.filter((o) => o !== FIRST).indexOf(id);
  books.push({ b, i, t0: rank < 0 ? 0.2 : 1.3 + rank * 0.2 });
}
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), easeOut = (p) => 1 - Math.pow(1 - p, 3);
const bounce = (p) => { const n = 7.5625, d = 2.75; if (p < 1 / d) return n * p * p; if (p < 2 / d) return n * (p -= 1.5 / d) * p + .75;
  if (p < 2.5 / d) return n * (p -= 2.25 / d) * p + .9375; return n * (p -= 2.625 / d) * p + .984375; };
window.renderFrame = (t) => {
  for (const { b, i, t0 } of books) {
    const p = clamp((t - t0) / 0.9), d = bounce(p);
    b.visible = t >= t0 - 0.01;
    b.position.set(X[i], Y0[i] + bh / 2 + (1 - d) * 7, Z[i]);
    b.rotation.set(-(1 - d) * 0.25, RY[i] + (1 - easeOut(p)) * (i < 2 ? -0.9 : 0.9), (1 - d) * (i < 2 ? 0.3 : -0.3));
  }
  // featured book alone at first: camera starts close on it, then pulls back to reveal all four
  const fi = ORDER.indexOf(FIRST), reveal = easeOut(clamp((t - 1.0) / 1.6));
  const fx = X[fi] * (1 - reveal), fy = (Y0[fi] + bh / 2) * (1 - reveal) + 0.72 * reveal, fz = Z[fi] * (1 - reveal);
  const dist = 4.6 + 6.6 * reveal - 0.6 * clamp((t - 2.6) / 7.4), sway = Math.sin(t * 0.45) * 0.12 * reveal;
  camera.position.set(fx + Math.sin(sway) * dist, fy + 0.35, fz + Math.cos(sway) * dist);
  camera.lookAt(fx, fy, fz);
  rimL.intensity = rimR.intensity = 26 + 8 * Math.sin(t * 2.2);
  renderer.render(scene, camera);
};
if (location.search.includes('render=1')) window.renderFrame(0);
window.VIDEO_READY = true;
</script></body></html>
