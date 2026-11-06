// Entry point: global motion system + lazy page modules.
import { reducedMotion, getGsap, getScrollTrigger } from './lib/env.js';
import { initSplitHeadings, initReveals, initTypewriter, initCounters } from './lib/reveal.js';
import { initCursor, initMagnetic, initTilt, initNav, initToasts } from './lib/interactions.js';
import { initTransitions } from './lib/transitions.js';

const PAGE_MODULES = {
  home: () => import('./pages/home.js'),
  overview: () => import('./pages/overview.js'),
  how: () => import('./pages/how.js'),
  testing: () => import('./pages/testing.js'),
  security: () => import('./pages/security.js'),
  'qr-login': () => import('./pages/qr-login.js'),
  scanner: () => import('./pages/scanner.js'),
  confirm: () => import('./pages/confirm.js'),
};

function initSmoothScroll() {
  const gsap = getGsap();
  const ScrollTrigger = getScrollTrigger();
  if (gsap && ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
  if (reducedMotion || !window.Lenis) return null;
  const lenis = new window.Lenis({ lerp: 0.1, smoothWheel: true, wheelMultiplier: 1 });
  if (gsap && ScrollTrigger) {
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
  } else {
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }
  return lenis;
}

function boot() {
  if (reducedMotion) document.documentElement.classList.add('reduced-motion');
  const lenis = initSmoothScroll();
  window.__lenis = lenis;
  initNav();
  initToasts();
  initTransitions(lenis);
  initSplitHeadings();
  initReveals();
  initTypewriter();
  initCounters();
  initCursor();
  initMagnetic();
  initTilt();

  const page = document.body.dataset.page;
  const loader = PAGE_MODULES[page];
  if (loader) {
    loader()
      .then((mod) => mod.init && mod.init({ lenis }))
      .catch((err) => console.error(`[qrauth] page module "${page}" failed`, err));
  }
  // Fonts change line metrics; refresh trigger positions once they are ready.
  if (document.fonts && getScrollTrigger()) document.fonts.ready.then(() => getScrollTrigger().refresh());
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();
