// Animated SVG charts (bars grow via scaleY, line draws via dashoffset) and suite rings.
import { getGsap, readJSONScript, onVisible, formatNumber } from '../lib/env.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
let uid = 0;

function el(name, attrs = {}, parent) {
  const node = document.createElementNS(SVG_NS, name);
  Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
  if (parent) parent.appendChild(node);
  return node;
}

function niceMax(value) {
  if (value <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(value)));
  const n = value / pow;
  const step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
  return step * pow;
}

function baseSvg(container, height) {
  const width = 640;
  const svg = el('svg', { viewBox: `0 0 ${width} ${height}`, class: 'chart__svg', role: 'img' });
  const id = ++uid;
  const defs = el('defs', {}, svg);
  const g1 = el('linearGradient', { id: `gradBar${id}`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  el('stop', { offset: '0', 'stop-color': '#00E5FF' }, g1);
  el('stop', { offset: '1', 'stop-color': '#00E5FF', 'stop-opacity': '0.15' }, g1);
  const g2 = el('linearGradient', { id: `gradBarAlt${id}`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  el('stop', { offset: '0', 'stop-color': '#7C5CFF' }, g2);
  el('stop', { offset: '1', 'stop-color': '#7C5CFF', 'stop-opacity': '0.15' }, g2);
  const g3 = el('linearGradient', { id: `gradArea${id}`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  el('stop', { offset: '0', 'stop-color': '#00E5FF', 'stop-opacity': '0.28' }, g3);
  el('stop', { offset: '1', 'stop-color': '#00E5FF', 'stop-opacity': '0' }, g3);
  container.appendChild(svg);
  return { svg, width, id };
}

function grid(svg, { left, right, top, bottom, width, height, max, min = 0, ticks = 4, unit }) {
  for (let i = 0; i <= ticks; i += 1) {
    const v = min + ((max - min) * i) / ticks;
    const y = bottom - ((bottom - top) * i) / ticks;
    el('line', { x1: left, x2: width - right, y1: y, y2: y, class: i === 0 ? 'chart__axis' : 'chart__grid' }, svg);
    const t = el('text', { x: left - 10, y: y + 4, 'text-anchor': 'end', class: 'chart__tick' }, svg);
    t.textContent = `${formatNumber(v, v % 1 ? 1 : 0)}`;
  }
  const u = el('text', { x: left - 10, y: top - 14, 'text-anchor': 'end', class: 'chart__tick' }, svg);
  u.textContent = unit || '';
  return height;
}

function barChart(container, data, { unit, alt }) {
  const height = 300;
  const { svg, width, id } = baseSvg(container, height);
  svg.setAttribute('aria-label', data.map((d) => `${d.label}: ${d.value}${unit}`).join(', '));
  const pad = { left: 56, right: 16, top: 32, bottom: 252 };
  const max = niceMax(Math.max(...data.map((d) => d.value)) * 1.1);
  grid(svg, { ...pad, width, height, max, unit });
  const slot = (width - pad.left - pad.right) / data.length;
  const bw = Math.min(64, slot * 0.6);
  const bars = []; const vals = [];
  data.forEach((d, i) => {
    const h = ((pad.bottom - pad.top) * d.value) / max;
    const x = pad.left + slot * i + (slot - bw) / 2;
    const bar = el('rect', { x, y: pad.bottom - h, width: bw, height: Math.max(h, 1), rx: 8, class: 'chart__bar', fill: `url(#${alt ? 'gradBarAlt' : 'gradBar'}${id})` }, svg);
    bars.push(bar);
    const v = el('text', { x: x + bw / 2, y: pad.bottom - h - 10, class: 'chart__val' }, svg);
    v.textContent = formatNumber(d.value, d.value % 1 ? 1 : 0);
    vals.push(v);
    const t = el('text', { x: x + bw / 2, y: pad.bottom + 24, 'text-anchor': 'middle', class: 'chart__tick' }, svg);
    t.textContent = d.label;
  });
  return () => {
    const gsap = getGsap();
    if (!gsap) return;
    gsap.from(bars, { scaleY: 0, duration: 1.2, ease: 'expo.out', stagger: 0.08, transformOrigin: '50% 100%' });
    gsap.from(vals, { opacity: 0, y: 10, duration: 0.6, delay: 0.5, stagger: 0.08 });
  };
}

function lineChart(container, data, { unit }) {
  const height = 300;
  const { svg, width, id } = baseSvg(container, height);
  svg.setAttribute('aria-label', data.map((d) => `${d.label}: ${d.value}${unit}`).join(', '));
  const pad = { left: 56, right: 16, top: 32, bottom: 252 };
  const values = data.map((d) => d.value);
  const min = Math.max(0, Math.floor(Math.min(...values) - 1));
  const max = Math.ceil(Math.max(...values) + 1);
  grid(svg, { ...pad, width, height, max, min, unit });
  const x = (i) => pad.left + ((width - pad.left - pad.right) * i) / (data.length - 1);
  const y = (v) => pad.bottom - ((pad.bottom - pad.top) * (v - min)) / (max - min);
  const pts = data.map((d, i) => [x(i), y(d.value)]);
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
  const area = el('path', { d: `${d} L${pts[pts.length - 1][0]} ${pad.bottom} L${pts[0][0]} ${pad.bottom} Z`, class: 'chart__area', fill: `url(#gradArea${id})` }, svg);
  const line = el('path', { d, class: 'chart__line' }, svg);
  const dots = pts.map((p) => el('circle', { cx: p[0], cy: p[1], r: 4, class: 'chart__dot' }, svg));
  data.forEach((item, i) => {
    if (i % 2) return;
    const t = el('text', { x: x(i), y: pad.bottom + 24, 'text-anchor': 'middle', class: 'chart__tick' }, svg);
    t.textContent = item.label;
  });
  return () => {
    const gsap = getGsap();
    if (!gsap) return;
    const len = line.getTotalLength();
    gsap.fromTo(line, { strokeDasharray: len, strokeDashoffset: len }, { strokeDashoffset: 0, duration: 1.8, ease: 'power2.inOut' });
    gsap.from(area, { opacity: 0, duration: 1.2, delay: 0.8 });
    gsap.from(dots, { scale: 0, transformOrigin: '50% 50%', duration: 0.5, ease: 'back.out(3)', stagger: 0.08, delay: 0.3 });
  };
}

function initCharts() {
  document.querySelectorAll('[data-chart]').forEach((container) => {
    const data = readJSONScript(container.dataset.source);
    if (!data || !data.length) return;
    const opts = { unit: container.dataset.unit || '', alt: container.dataset.alt === '1' };
    const play = container.dataset.chart === 'line' ? lineChart(container, data, opts) : barChart(container, data, opts);
    onVisible(container, play, { threshold: 0.35 });
  });
}

function initRings() {
  const gsap = getGsap();
  document.querySelectorAll('[data-ring]').forEach((ring) => {
    const bar = ring.querySelector('.ring__bar');
    if (!gsap || !bar) return;
    gsap.set(bar, { attr: { 'stroke-dashoffset': 1 } });
    onVisible(ring, () => gsap.to(bar, { attr: { 'stroke-dashoffset': 0 }, duration: 1.6, ease: 'power3.out' }));
  });
}

export function init() {
  initCharts();
  initRings();
}
