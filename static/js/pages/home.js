// Hero: a QR code assembled from glowing particles (Three.js, lazy-loaded).
import { reducedMotion, readJSONScript, onVisible, clamp } from '../lib/env.js';

const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const AMBIENT = 700;

const VERTEX = /* glsl */ `
  attribute vec3 aStart;
  attribute float aDelay;
  attribute float aSize;
  attribute vec3 aColor;
  attribute float aKind;
  uniform float uProgress;
  uniform float uTime;
  uniform float uScale;
  varying vec3 vColor;
  varying float vKind;
  varying float vAlpha;

  float easeOutExpo(float t) { return t >= 1.0 ? 1.0 : 1.0 - pow(2.0, -10.0 * t); }

  void main() {
    float t = clamp((uProgress - aDelay) / 0.55, 0.0, 1.0);
    float e = easeOutExpo(t);
    vec3 pos = mix(aStart, position, e);
    if (aKind > 0.5) {
      // ambient dust drifts slowly
      pos += vec3(sin(uTime * 0.3 + aDelay * 40.0), cos(uTime * 0.25 + aDelay * 30.0), sin(uTime * 0.2 + aDelay * 20.0)) * 0.8;
    } else {
      // tiny breathing on QR modules once assembled
      pos.z += sin(uTime * 1.5 + position.x * 0.4 + position.y * 0.3) * 0.18 * e;
    }
    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mv;
    // one QR module = one world unit -> size the sprite to exactly one module on screen
    gl_PointSize = aSize * uScale / -mv.z;
    vKind = aKind;
    vColor = aColor;
    vAlpha = aKind > 0.5 ? 0.35 : mix(0.15, 1.0, e);
  }
`;

const FRAGMENT = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;
  varying float vKind;
  void main() {
    vec2 uv = gl_PointCoord - 0.5;
    // QR modules: near-full square so the code reads as a solid matrix; dust: soft dot
    float half_ = vKind > 0.5 ? 0.12 : 0.36;
    vec2 q = abs(uv) - vec2(half_);
    float box = length(max(q, 0.0)) - 0.06;
    float core = 1.0 - smoothstep(0.0, 0.04, box);
    float glow = exp(-length(uv) * 7.0) * (vKind > 0.5 ? 0.8 : 0.25);
    float a = (core + glow) * vAlpha;
    if (a < 0.01) discard;
    gl_FragColor = vec4(vColor * (0.6 + core), a);
  }
`;

function isFinder(x, y, n) {
  const inBox = (bx, by) => x >= bx && x < bx + 7 && y >= by && y < by + 7;
  return inBox(0, 0) || inBox(n - 7, 0) || inBox(0, n - 7);
}

async function buildScene(container, stage, matrix) {
  const THREE = await import(/* webpackIgnore: true */ THREE_URL);
  const n = matrix.length;
  const cyan = new THREE.Color('#00E5FF');
  const violet = new THREE.Color('#7C5CFF');
  const green = new THREE.Color('#22E39B');

  const targets = [];
  matrix.forEach((row, y) => {
    for (let x = 0; x < row.length; x += 1) {
      if (row[x] === '1') targets.push([x, y]);
    }
  });

  const count = targets.length + AMBIENT;
  const position = new Float32Array(count * 3);
  const start = new Float32Array(count * 3);
  const delay = new Float32Array(count);
  const size = new Float32Array(count);
  const color = new Float32Array(count * 3);
  const kind = new Float32Array(count);

  const randomSphere = (radius) => {
    const u = Math.random() * 2 - 1;
    const phi = Math.random() * Math.PI * 2;
    const r = radius * Math.cbrt(Math.random());
    const s = Math.sqrt(1 - u * u);
    return [r * s * Math.cos(phi), r * s * Math.sin(phi), r * u];
  };

  targets.forEach(([x, y], i) => {
    const px = x - n / 2 + 0.5;
    const py = -(y - n / 2 + 0.5);
    position.set([px, py, 0], i * 3);
    start.set(randomSphere(n * 1.4), i * 3);
    const dist = Math.hypot(px, py) / n;
    delay[i] = dist * 0.35 + Math.random() * 0.12;
    size[i] = 1.0;
    const c = isFinder(x, y, n) ? cyan.clone() : cyan.clone().lerp(violet, clamp((px + py) / n + 0.5));
    color.set([c.r, c.g, c.b], i * 3);
    kind[i] = 0;
  });
  for (let j = 0; j < AMBIENT; j += 1) {
    const i = targets.length + j;
    const p = randomSphere(n * 1.6);
    position.set(p, i * 3);
    start.set(p, i * 3);
    delay[i] = 0;
    size[i] = 0.3 + Math.random() * 0.5;
    const c = Math.random() < 0.15 ? green : Math.random() < 0.5 ? violet : cyan;
    color.set([c.r, c.g, c.b], i * 3);
    kind[i] = 1;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(position, 3));
  geometry.setAttribute('aStart', new THREE.BufferAttribute(start, 3));
  geometry.setAttribute('aDelay', new THREE.BufferAttribute(delay, 1));
  geometry.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
  geometry.setAttribute('aColor', new THREE.BufferAttribute(color, 3));
  geometry.setAttribute('aKind', new THREE.BufferAttribute(kind, 1));

  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const material = new THREE.ShaderMaterial({
    vertexShader: VERTEX,
    fragmentShader: FRAGMENT,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: { uProgress: { value: 0 }, uTime: { value: 0 }, uScale: { value: 100 } },
  });

  const scene = new THREE.Scene();
  const group = new THREE.Group();
  const points = new THREE.Points(geometry, material);
  group.add(points);

  // Laser scan plane sweeping across the code.
  const laser = new THREE.Mesh(
    new THREE.PlaneGeometry(n * 1.15, 0.22),
    new THREE.MeshBasicMaterial({ color: cyan, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  laser.position.z = 0.4;
  group.add(laser);
  scene.add(group);

  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 500);
  camera.position.set(0, 0, n * 2.4);

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(pixelRatio);
  renderer.setClearColor(0x000000, 0);
  container.appendChild(renderer.domElement);

  const resize = () => {
    const w = container.clientWidth || 1;
    const h = container.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    material.uniforms.uScale.value = (h * pixelRatio / 2) / Math.tan((camera.fov * Math.PI) / 360);
  };
  resize();
  new ResizeObserver(resize).observe(container);

  const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
  window.addEventListener('pointermove', (e) => {
    mouse.tx = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.ty = (e.clientY / window.innerHeight) * 2 - 1;
  }, { passive: true });

  let running = true;
  let visible = true;
  new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; }).observe(container);
  document.addEventListener('visibilitychange', () => { running = !document.hidden; });

  const clock = new THREE.Clock();
  const ASSEMBLE = 2.8;
  stage.classList.add('is-3d');

  const frame = () => {
    requestAnimationFrame(frame);
    if (!running || !visible) { clock.getDelta(); return; }
    const t = clock.getElapsedTime();
    material.uniforms.uTime.value = t;
    material.uniforms.uProgress.value = Math.min(1.6, t / ASSEMBLE);
    mouse.x += (mouse.tx - mouse.x) * 0.05;
    mouse.y += (mouse.ty - mouse.y) * 0.05;
    // gentle sway only: a strongly rotated code is unreadable
    group.rotation.y = Math.sin(t * 0.25) * 0.12 + mouse.x * 0.14;
    group.rotation.x = Math.cos(t * 0.2) * 0.05 + mouse.y * 0.1;
    camera.position.x = mouse.x * 1.2;
    camera.position.y = -mouse.y * 1.2;
    camera.lookAt(0, 0, 0);
    // Laser sweeps only after the code has assembled.
    const sweep = (t % 3.2) / 3.2;
    laser.position.y = (0.5 - sweep) * n;
    laser.material.opacity = t > ASSEMBLE * 0.8 ? Math.sin(sweep * Math.PI) * 0.85 : 0;
    renderer.render(scene, camera);
  };
  frame();
}

export function init() {
  const stage = document.querySelector('[data-hero-stage]');
  const container = document.querySelector('[data-hero-canvas]');
  const matrix = readJSONScript('hero-matrix');
  if (!stage || !container || !matrix || reducedMotion) return;
  const canvasTest = document.createElement('canvas');
  if (!(canvasTest.getContext('webgl2') || canvasTest.getContext('webgl'))) return;
  // The CSS laser is replaced by the in-scene laser once 3D is up.
  const load = () => buildScene(container, stage, matrix)
    .then(() => { stage.querySelector('.laser-box')?.remove(); })
    .catch((err) => console.warn('[qrauth] 3D hero unavailable, using SVG fallback', err));
  onVisible(stage, () => {
    if ('requestIdleCallback' in window) window.requestIdleCallback(load, { timeout: 1200 });
    else setTimeout(load, 300);
  });
}
