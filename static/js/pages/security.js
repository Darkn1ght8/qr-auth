// Security score gauge + per-threat score bars.
import { getGsap, onVisible } from '../lib/env.js';

const ARC = 75; // the gauge uses 270° of a 100-unit circle

export function init() {
  const gauge = document.querySelector('[data-gauge]');
  const gsap = getGsap();
  if (gauge) {
    const score = parseFloat(gauge.dataset.gauge) || 0;
    const bar = gauge.querySelector('[data-gauge-bar]');
    const target = (score / 10) * ARC;
    if (!gsap) {
      bar.setAttribute('stroke-dasharray', `${target} 100`);
    } else {
      const state = { v: 0 };
      onVisible(gauge, () => gsap.to(state, {
        v: target,
        duration: 2,
        ease: 'power3.out',
        delay: 0.4,
        onUpdate: () => bar.setAttribute('stroke-dasharray', `${state.v} 100`),
      }));
    }
  }
  if (gsap) {
    document.querySelectorAll('.score-bar b').forEach((b) => {
      onVisible(b, () => gsap.from(b, { scaleX: 0, duration: 1.2, ease: 'expo.out' }));
    });
  }
}
