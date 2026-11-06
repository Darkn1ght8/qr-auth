// Scroll-driven reveals: split headings, fades, staggers, typewriter and counters.
import { getGsap, getScrollTrigger, reducedMotion, formatNumber, onVisible } from './env.js';
import { splitText } from './split.js';

const INTRO_DELAY = 0.55; // wait for the curtain to lift

function isAboveFold(el) {
  const rect = el.getBoundingClientRect();
  return rect.top < window.innerHeight * 0.9;
}

export function initSplitHeadings() {
  const gsap = getGsap();
  document.querySelectorAll('[data-split]').forEach((el) => {
    if (!gsap) return;
    const chars = splitText(el);
    const fromVars = { yPercent: 110, opacity: 0, rotate: 6, transformOrigin: '0% 100%' };
    const toVars = { yPercent: 0, opacity: 1, rotate: 0, duration: 1, ease: 'expo.out', stagger: { each: 0.018, from: 'start' } };
    gsap.set(chars, fromVars);
    if (isAboveFold(el)) {
      gsap.to(chars, { ...toVars, delay: INTRO_DELAY });
    } else {
      gsap.to(chars, { ...toVars, scrollTrigger: { trigger: el, start: 'top 88%', once: true } });
    }
  });
}

export function initReveals() {
  const gsap = getGsap();
  if (!gsap || !getScrollTrigger()) return;
  document.querySelectorAll('[data-reveal], [data-row-reveal]').forEach((el) => {
    const above = isAboveFold(el);
    gsap.from(el, {
      y: 36,
      opacity: 0,
      duration: 1.1,
      ease: 'expo.out',
      delay: above ? INTRO_DELAY + 0.25 : 0,
      scrollTrigger: above ? undefined : { trigger: el, start: 'top 90%', once: true },
    });
  });
  document.querySelectorAll('[data-stagger]').forEach((group) => {
    const items = Array.from(group.children);
    const above = isAboveFold(group);
    gsap.from(items, {
      y: 48,
      opacity: 0,
      duration: 1.1,
      ease: 'expo.out',
      stagger: 0.08,
      delay: above ? INTRO_DELAY + 0.2 : 0,
      scrollTrigger: above ? undefined : { trigger: group, start: 'top 88%', once: true },
    });
  });
}

export function initTypewriter() {
  document.querySelectorAll('[data-type]').forEach((el) => {
    const text = el.dataset.type || el.textContent;
    if (reducedMotion || !getGsap()) { el.textContent = text; return; }
    el.setAttribute('aria-label', text);
    // Keep the final height reserved so layout does not jump while typing.
    el.style.minHeight = `${el.offsetHeight}px`;
    const output = document.createElement('span');
    output.setAttribute('aria-hidden', 'true');
    const caret = document.createElement('span');
    caret.className = 'type-caret';
    caret.setAttribute('aria-hidden', 'true');
    el.textContent = '';
    el.append(output, caret);
    let i = 0;
    const start = () => {
      const tick = () => {
        i += Math.random() < 0.15 ? 2 : 1;
        output.textContent = text.slice(0, i);
        if (i < text.length) {
          const ch = text[i - 1];
          setTimeout(tick, /[.,:]/.test(ch) ? 140 : 14 + Math.random() * 22);
        } else {
          setTimeout(() => caret.remove(), 2400);
        }
      };
      tick();
    };
    setTimeout(() => onVisible(el, start), 900);
  });
}

export function initCounters() {
  document.querySelectorAll('[data-count]').forEach((el) => {
    const target = parseFloat(String(el.dataset.count).replace(',', '.'));
    if (Number.isNaN(target)) return;
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    const gsap = getGsap();
    if (!gsap) { el.textContent = formatNumber(target, decimals); return; }
    const state = { v: 0 };
    el.textContent = formatNumber(0, decimals);
    onVisible(el, () => {
      gsap.to(state, {
        v: target,
        duration: 1.8,
        ease: 'power3.out',
        delay: isAboveFold(el) ? INTRO_DELAY : 0,
        onUpdate: () => { el.textContent = formatNumber(state.v, decimals); },
      });
    }, { threshold: 0.4 });
  });
}
