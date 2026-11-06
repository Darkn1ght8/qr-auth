// Shared environment helpers.

const mq = (query) => (window.matchMedia ? window.matchMedia(query).matches : false);

export const reducedMotion = mq('(prefers-reduced-motion: reduce)');
export const finePointer = mq('(hover: hover) and (pointer: fine)');

export const getGsap = () => (window.gsap && !reducedMotion ? window.gsap : null);
export const getScrollTrigger = () => (window.ScrollTrigger && getGsap() ? window.ScrollTrigger : null);

export const clamp = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
export const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeInBack = (t) => 2.70158 * t * t * t - 1.70158 * t * t;

export function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

export async function postJSON(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken(), Accept: 'application/json' },
    body: JSON.stringify(body || {}),
  });
  let data = {};
  try { data = await response.json(); } catch (_) { data = {}; }
  return { ok: response.ok && data.ok !== false, status: response.status, data };
}

export function formatNumber(value, decimals = 0) {
  try {
    return new Intl.NumberFormat('kk-KZ', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
  } catch (_) {
    return Number(value).toFixed(decimals);
  }
}

export function onVisible(el, callback, options = { threshold: 0.2 }) {
  if (!('IntersectionObserver' in window)) { callback(); return () => {}; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) { io.disconnect(); callback(); }
    });
  }, options);
  io.observe(el);
  return () => io.disconnect();
}

export function readJSONScript(id) {
  const node = document.getElementById(id);
  if (!node) return null;
  try { return JSON.parse(node.textContent); } catch (_) { return null; }
}
