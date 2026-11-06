// Interactive QR anatomy (version 2, 25×25) + animated error-correction bars.
import { getGsap, onVisible, reducedMotion } from '../lib/env.js';

const N = 25;
const SVG_NS = 'http://www.w3.org/2000/svg';

function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildModules() {
  const rand = mulberry32(2026);
  const cells = []; // {x, y, group}
  const taken = new Set();
  const mark = (x, y, group, dark) => {
    taken.add(`${x},${y}`);
    if (dark) cells.push({ x, y, group });
  };
  // Finder patterns + separators
  [[0, 0], [N - 7, 0], [0, N - 7]].forEach(([fx, fy]) => {
    for (let y = -1; y <= 7; y += 1) {
      for (let x = -1; x <= 7; x += 1) {
        const ax = fx + x; const ay = fy + y;
        if (ax < 0 || ay < 0 || ax >= N || ay >= N) continue;
        const ring = x >= 0 && x <= 6 && y >= 0 && y <= 6 && (x === 0 || x === 6 || y === 0 || y === 6);
        const core = x >= 2 && x <= 4 && y >= 2 && y <= 4;
        mark(ax, ay, 'finder', ring || core);
      }
    }
  });
  // Alignment pattern centred at (18, 18)
  for (let y = -2; y <= 2; y += 1) {
    for (let x = -2; x <= 2; x += 1) {
      const dark = Math.max(Math.abs(x), Math.abs(y)) !== 1;
      mark(18 + x, 18 + y, 'align', dark);
    }
  }
  // Timing patterns
  for (let i = 8; i < N - 8; i += 1) {
    mark(i, 6, 'timing', i % 2 === 0);
    mark(6, i, 'timing', i % 2 === 0);
  }
  // Format information
  const fmt = [];
  for (let i = 0; i <= 8; i += 1) { if (i !== 6) { fmt.push([i, 8], [8, i]); } }
  for (let i = N - 8; i < N; i += 1) { fmt.push([i, 8], [8, i]); }
  fmt.forEach(([x, y]) => { if (!taken.has(`${x},${y}`)) mark(x, y, 'format', rand() > 0.45); });
  mark(8, N - 8, 'format', true); // dark module
  // Data
  for (let y = 0; y < N; y += 1) {
    for (let x = 0; x < N; x += 1) {
      if (!taken.has(`${x},${y}`)) mark(x, y, 'data', rand() > 0.5);
    }
  }
  return cells;
}

function initAnatomy() {
  const host = document.querySelector('[data-anatomy]');
  const legend = document.querySelector('[data-legend]');
  if (!host || !legend) return;
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${N} ${N}`);
  svg.setAttribute('shape-rendering', 'crispEdges');
  const byGroup = {};
  buildModules().forEach(({ x, y, group }) => {
    const r = document.createElementNS(SVG_NS, 'rect');
    r.setAttribute('x', x); r.setAttribute('y', y); r.setAttribute('width', 1.02); r.setAttribute('height', 1.02);
    r.setAttribute('class', `m g-${group}`);
    svg.appendChild(r);
    (byGroup[group] = byGroup[group] || []).push(r);
  });
  host.appendChild(svg);

  const items = Array.from(legend.querySelectorAll('[data-group]'));
  let auto = null;
  let index = 0;
  const focus = (group) => {
    host.classList.toggle('has-focus', Boolean(group));
    Object.entries(byGroup).forEach(([g, rects]) => rects.forEach((r) => r.classList.toggle('is-on', g === group)));
    items.forEach((it) => it.classList.toggle('is-active', it.dataset.group === group));
  };
  const stopAuto = () => { if (auto) { clearInterval(auto); auto = null; } };
  items.forEach((item) => {
    const g = item.dataset.group;
    item.addEventListener('pointerenter', () => { stopAuto(); focus(g); });
    item.addEventListener('focus', () => { stopAuto(); focus(g); });
    item.addEventListener('click', () => { stopAuto(); focus(g); });
  });
  legend.addEventListener('pointerleave', () => focus(null));

  onVisible(host, () => {
    const gsap = getGsap();
    if (gsap) {
      const rects = svg.querySelectorAll('rect');
      gsap.from(rects, { opacity: 0, scale: 0, transformOrigin: '50% 50%', duration: 0.5, ease: 'back.out(2)', stagger: { amount: 1.1, from: 'random' } });
    }
    if (!reducedMotion) {
      auto = setInterval(() => { focus(items[index % items.length].dataset.group); index += 1; }, 2200);
    }
  });
}

function initEcBars() {
  const gsap = getGsap();
  const host = document.querySelector('[data-ec]');
  if (!gsap || !host) return;
  const fills = host.querySelectorAll('.ec__fill');
  gsap.from(fills, { scaleX: 0, duration: 1.4, ease: 'expo.out', stagger: 0.12, scrollTrigger: { trigger: host, start: 'top 85%', once: true } });
}

export function init() {
  initAnatomy();
  initEcBars();
}
