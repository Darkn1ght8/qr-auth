// Curtain page transitions: the panel covers the page before navigation and
// lifts on load (CSS keyframes), so multi-page navigation feels continuous.
import { reducedMotion } from './env.js';

const COVER_MS = 520;

export function navigate(url) {
  const curtain = document.querySelector('.curtain');
  if (!curtain || reducedMotion) { window.location.href = url; return; }
  curtain.classList.remove('is-done');
  curtain.classList.add('is-covering');
  setTimeout(() => { window.location.href = url; }, COVER_MS);
}

function shouldIntercept(link, event) {
  if (event.defaultPrevented || event.button !== 0) return false;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
  if (link.target && link.target !== '_self') return false;
  if (link.hasAttribute('download') || link.dataset.noTransition !== undefined) return false;
  const url = new URL(link.href, window.location.href);
  if (url.origin !== window.location.origin) return false;
  if (url.pathname === window.location.pathname && url.search === window.location.search) return false; // hash links
  if (url.pathname.startsWith('/admin')) return false;
  return true;
}

// Safety net: once the opening reveal is over, take the curtain out of the page entirely,
// even on a browser that never runs/finishes the CSS animation.
function retireCurtain() {
  const curtain = document.querySelector('.curtain');
  if (!curtain) return;
  const done = () => { if (!curtain.classList.contains('is-covering')) curtain.classList.add('is-done'); };
  curtain.querySelector('.curtain__panel')?.addEventListener('animationend', done, { once: true });
  setTimeout(done, 1500);
}

export function initTransitions(lenis) {
  retireCurtain();
  document.addEventListener('click', (event) => {
    const link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;
    const url = new URL(link.href, window.location.href);
    if (url.origin === window.location.origin && url.pathname === window.location.pathname && url.hash) {
      const target = document.querySelector(url.hash);
      if (target) {
        event.preventDefault();
        if (lenis) lenis.scrollTo(target, { offset: -72 });
        else target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth' });
      }
      return;
    }
    if (!shouldIntercept(link, event)) return;
    event.preventDefault();
    navigate(link.href);
  });
  // Restore after back/forward cache.
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      const curtain = document.querySelector('.curtain');
      curtain?.classList.remove('is-covering');
      curtain?.classList.add('is-done');
    }
  });
}
