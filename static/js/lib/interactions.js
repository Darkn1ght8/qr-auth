// Pointer-driven micro-interactions: custom cursor with trail, magnetic buttons,
// 3D tilt cards with a cursor-following glow. Only transform/opacity are animated.
import { finePointer, reducedMotion, getGsap, lerp } from './env.js';
import { t } from './i18n.js';

export function initCursor() {
  const root = document.querySelector('.cursor');
  if (!root || !finePointer || reducedMotion) return;
  document.documentElement.classList.add('has-cursor');
  root.style.opacity = '0';
  const dot = root.querySelector('.cursor__dot');
  const ring = root.querySelector('.cursor__ring');
  const trail = Array.from(root.querySelectorAll('.cursor__trail'));
  const pointer = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
  const ringPos = { ...pointer };
  const trailPos = trail.map(() => ({ ...pointer }));
  let visible = false;

  window.addEventListener('pointermove', (e) => {
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    if (!visible) { visible = true; root.style.opacity = '1'; }
  }, { passive: true });
  document.addEventListener('pointerleave', () => { visible = false; root.style.opacity = '0'; });

  const hoverSelector = 'a, button, [data-tilt], summary, label, input, .legend__item';
  document.addEventListener('pointerover', (e) => {
    if (e.target.closest && e.target.closest(hoverSelector)) root.classList.add('is-hover');
  });
  document.addEventListener('pointerout', (e) => {
    if (e.target.closest && e.target.closest(hoverSelector)) root.classList.remove('is-hover');
  });

  const frame = () => {
    ringPos.x = lerp(ringPos.x, pointer.x, 0.18);
    ringPos.y = lerp(ringPos.y, pointer.y, 0.18);
    dot.style.transform = `translate3d(${pointer.x}px, ${pointer.y}px, 0)`;
    ring.style.transform = `translate3d(${ringPos.x}px, ${ringPos.y}px, 0)`;
    let lead = pointer;
    trailPos.forEach((p, i) => {
      p.x = lerp(p.x, lead.x, 0.35);
      p.y = lerp(p.y, lead.y, 0.35);
      const scale = 1 - i / trail.length;
      trail[i].style.transform = `translate3d(${p.x}px, ${p.y}px, 0) scale(${scale})`;
      trail[i].style.opacity = String(0.55 * scale);
      lead = p;
    });
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

export function initMagnetic() {
  const gsap = getGsap();
  if (!gsap || !finePointer) return;
  document.querySelectorAll('[data-magnetic]').forEach((el) => {
    const xTo = gsap.quickTo(el, 'x', { duration: 0.5, ease: 'power3.out' });
    const yTo = gsap.quickTo(el, 'y', { duration: 0.5, ease: 'power3.out' });
    const strength = parseFloat(el.dataset.magnetic) || 0.35;
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      xTo((e.clientX - (r.left + r.width / 2)) * strength);
      yTo((e.clientY - (r.top + r.height / 2)) * strength);
    });
    el.addEventListener('pointerleave', () => {
      gsap.to(el, { x: 0, y: 0, duration: 0.9, ease: 'elastic.out(1, 0.35)' });
    });
  });
}

export function initTilt() {
  if (!finePointer || reducedMotion) return;
  const gsap = getGsap();
  document.querySelectorAll('[data-tilt]').forEach((card) => {
    card.classList.add('card--glow');
    const max = parseFloat(card.dataset.tilt) || 7;
    let rect = null;
    const rx = gsap ? gsap.quickTo(card, 'rotationX', { duration: 0.6, ease: 'power3.out' }) : null;
    const ry = gsap ? gsap.quickTo(card, 'rotationY', { duration: 0.6, ease: 'power3.out' }) : null;
    if (gsap) gsap.set(card, { transformPerspective: 900 });
    card.addEventListener('pointerenter', () => { rect = card.getBoundingClientRect(); });
    card.addEventListener('pointermove', (e) => {
      rect = rect || card.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width;
      const py = (e.clientY - rect.top) / rect.height;
      card.style.setProperty('--mx', `${px * 100}%`);
      card.style.setProperty('--my', `${py * 100}%`);
      card.style.setProperty('--gx', `${e.clientX - rect.left}px`);
      card.style.setProperty('--gy', `${e.clientY - rect.top}px`);
      if (rx && ry) {
        rx((0.5 - py) * max * 2);
        ry((px - 0.5) * max * 2);
      }
    });
    card.addEventListener('pointerleave', () => {
      rect = null;
      if (rx && ry) { rx(0); ry(0); }
    });
  });
}

export function initNav() {
  const nav = document.querySelector('[data-nav]');
  if (!nav) return;
  const burger = nav.querySelector('[data-burger]');
  let lastY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle('is-scrolled', y > 24);
    if (!nav.classList.contains('is-open')) {
      nav.classList.toggle('is-hidden', y > lastY && y > 320);
    }
    lastY = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (burger) {
    burger.addEventListener('click', () => {
      const open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? t('Закрыть меню') : t('Открыть меню'));
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        burger.setAttribute('aria-expanded', 'false');
        burger.focus();
      }
    });
  }
}

export function initConfirmForms() {
  document.addEventListener('submit', (event) => {
    const form = event.target.closest && event.target.closest('form[data-confirm]');
    if (form && !window.confirm(form.dataset.confirm)) event.preventDefault();
  }, true);
}

export function initToasts() {
  document.querySelectorAll('.toast').forEach((toast, i) => {
    setTimeout(() => {
      toast.classList.add('is-leaving');
      toast.addEventListener('animationend', () => toast.remove(), { once: true });
    }, 5200 + i * 400);
  });
}
