// Canvas QR renderer where every dark module is a particle:
// - transitionTo(): old pixels scatter away, new code assembles from the edges
// - collapse(): pixels implode into the centre (used before the success check)
// - confettiBurst(): pixel confetti on a separate canvas
import { reducedMotion, clamp, easeOutCubic, easeInBack } from './env.js';

const QUIET = 2;
const INK = '#07090F';
const CONFETTI_COLORS = ['#00E5FF', '#7C5CFF', '#22E39B', '#FFFFFF'];

export class QRParticles {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.particles = [];
    this.ghosts = [];
    this.n = 0;
    this.cell = 0;
    this.mode = 'idle';
    this.modeStart = 0;
    this.raf = null;
    this.size = 0;
    this.resize = this.resize.bind(this);
    this.frame = this.frame.bind(this);
    new ResizeObserver(this.resize).observe(canvas);
    this.resize();
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.size = Math.max(1, Math.round(rect.width));
    this.canvas.width = Math.round(this.size * dpr);
    this.canvas.height = Math.round(this.size * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (this.n) {
      const oldCell = this.cell;
      this.cell = this.size / (this.n + QUIET * 2);
      const k = oldCell ? this.cell / oldCell : 1;
      this.particles.forEach((p) => {
        p.tx = (p.gx + QUIET) * this.cell; p.ty = (p.gy + QUIET) * this.cell;
        p.sx *= k; p.sy *= k;
        if (this.mode === 'idle') { p.x = p.tx; p.y = p.ty; }
      });
    }
    this.draw();
  }

  transitionTo(rows) {
    const n = rows.length;
    this.n = n;
    this.cell = this.size / (n + QUIET * 2);
    const center = this.size / 2;
    // Old pixels become ghosts flying outward.
    this.ghosts = this.particles.map((p) => {
      const ang = Math.atan2(p.y - center, p.x - center) + (Math.random() - 0.5) * 0.8;
      const speed = 160 + Math.random() * 420;
      return { x: p.x, y: p.y, vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed, rot: 0, vr: (Math.random() - 0.5) * 8 };
    });
    const particles = [];
    for (let gy = 0; gy < n; gy += 1) {
      for (let gx = 0; gx < n; gx += 1) {
        if (rows[gy][gx] !== '1') continue;
        const tx = (gx + QUIET) * this.cell;
        const ty = (gy + QUIET) * this.cell;
        const ang = Math.random() * Math.PI * 2;
        const r = this.size * (0.75 + Math.random() * 0.5);
        particles.push({
          gx, gy, tx, ty,
          sx: center + Math.cos(ang) * r, sy: center + Math.sin(ang) * r,
          x: tx, y: ty,
          delay: (Math.hypot(gx - n / 2, gy - n / 2) / n) * 0.45 + Math.random() * 0.15,
        });
      }
    }
    this.particles = particles;
    if (reducedMotion) { this.ghosts = []; this.setMode('idle'); this.draw(); return Promise.resolve(); }
    this.setMode('assemble');
    return new Promise((resolve) => { this.onDone = resolve; });
  }

  collapse() {
    if (reducedMotion || !this.particles.length) { this.particles = []; this.draw(); return Promise.resolve(); }
    this.particles.forEach((p) => { p.sx = p.x; p.sy = p.y; p.delay = Math.random() * 0.25; });
    this.setMode('collapse');
    return new Promise((resolve) => { this.onDone = resolve; });
  }

  setMode(mode) {
    this.mode = mode;
    this.modeStart = performance.now();
    if (!this.raf) this.raf = requestAnimationFrame(this.frame);
  }

  frame(now) {
    this.raf = null;
    const t = (now - this.modeStart) / 1000;
    let busy = false;

    if (this.ghosts.length) {
      const dt = 1 / 60;
      this.ghosts.forEach((g) => { g.x += g.vx * dt; g.y += g.vy * dt; g.vy += 300 * dt; g.rot += g.vr * dt; });
      if (t > 0.7) this.ghosts = []; else busy = true;
    }

    if (this.mode === 'assemble') {
      const DUR = 0.75;
      let done = true;
      this.particles.forEach((p) => {
        const k = clamp((t - 0.15 - p.delay) / DUR);
        const e = easeOutCubic(k);
        p.x = p.sx + (p.tx - p.sx) * e;
        p.y = p.sy + (p.ty - p.sy) * e;
        p.a = k;
        if (k < 1) done = false;
      });
      if (done) { this.mode = 'idle'; this.resolve(); } else busy = true;
    } else if (this.mode === 'collapse') {
      const DUR = 0.55;
      const c = this.size / 2 - this.cell / 2;
      let done = true;
      this.particles.forEach((p) => {
        const k = clamp((t - p.delay) / DUR);
        const e = easeInBack(k);
        p.x = p.sx + (c - p.sx) * e;
        p.y = p.sy + (c - p.sy) * e;
        p.a = 1 - k * k;
        if (k < 1) done = false;
      });
      if (done) { this.particles = []; this.mode = 'idle'; this.resolve(); } else busy = true;
    }

    this.draw(t);
    if (busy) this.raf = requestAnimationFrame(this.frame);
  }

  resolve() {
    const cb = this.onDone;
    this.onDone = null;
    if (cb) cb();
  }

  draw(t = 1) {
    const { ctx, size } = this;
    ctx.clearRect(0, 0, size, size);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, size, size);
    const s = this.cell + 0.6; // slight overlap hides seams between modules
    this.ghosts.forEach((g) => {
      ctx.globalAlpha = Math.max(0, 1 - t / 0.7);
      ctx.fillStyle = '#00B8D4';
      ctx.save();
      ctx.translate(g.x + s / 2, g.y + s / 2);
      ctx.rotate(g.rot);
      ctx.fillRect(-s / 2, -s / 2, s * 0.8, s * 0.8);
      ctx.restore();
    });
    ctx.fillStyle = INK;
    this.particles.forEach((p) => {
      ctx.globalAlpha = p.a === undefined ? 1 : clamp(p.a * 1.4);
      ctx.fillRect(p.x, p.y, s, s);
    });
    ctx.globalAlpha = 1;
  }
}

export function confettiBurst(canvas, { count = 140, duration = 1800 } = {}) {
  if (reducedMotion || !canvas) return Promise.resolve();
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const bits = Array.from({ length: count }, () => {
    const ang = Math.random() * Math.PI * 2;
    const speed = 220 + Math.random() * 520;
    return {
      x: cx, y: cy,
      vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed - 180,
      size: 4 + Math.random() * 7, rot: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 12,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
    };
  });
  const start = performance.now();
  let last = start;
  return new Promise((resolve) => {
    const step = (now) => {
      const dt = Math.min(0.033, (now - last) / 1000);
      last = now;
      const life = (now - start) / duration;
      ctx.clearRect(0, 0, rect.width, rect.height);
      bits.forEach((b) => {
        b.vx *= 0.985; b.vy = b.vy * 0.985 + 900 * dt;
        b.x += b.vx * dt; b.y += b.vy * dt; b.rot += b.vr * dt;
        ctx.globalAlpha = Math.max(0, 1 - life);
        ctx.fillStyle = b.color;
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.rotate(b.rot);
        ctx.fillRect(-b.size / 2, -b.size / 2, b.size, b.size);
        ctx.restore();
      });
      if (life < 1) requestAnimationFrame(step);
      else { ctx.clearRect(0, 0, rect.width, rect.height); resolve(); }
    };
    requestAnimationFrame(step);
  });
}
