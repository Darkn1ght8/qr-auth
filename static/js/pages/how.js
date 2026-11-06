// Pinned, scroll-scrubbed data-flow diagram + sequence diagram reveal.
import { getGsap, getScrollTrigger, clamp } from '../lib/env.js';

const STEPS = 6;
const PACKET_COLORS = { wire: '#00E5FF', 'wire--violet': '#7C5CFF', 'wire--green': '#22E39B' };

function packetColor(wire) {
  if (wire.classList.contains('wire--violet')) return PACKET_COLORS['wire--violet'];
  if (wire.classList.contains('wire--green')) return PACKET_COLORS['wire--green'];
  return PACKET_COLORS.wire;
}

function render(state, progress) {
  const scaled = clamp(progress) * STEPS;
  const step = Math.min(STEPS - 1, Math.floor(scaled));
  const local = progress >= 1 ? 1 : scaled - step;

  if (step !== state.step) {
    state.step = step;
    state.stepEls.forEach((el, i) => el.classList.toggle('is-active', i === step));
    state.nodes.forEach((node) => {
      const steps = node.dataset.steps.split(',').map(Number);
      node.classList.toggle('is-lit', steps.includes(step));
    });
  }
  state.bars.forEach((bar, i) => {
    const v = i < step ? 1 : i > step ? 0 : local;
    bar.style.transform = `scaleX(${v})`;
  });

  let packetPlaced = false;
  state.wires.forEach((wire) => {
    const s = wire.step;
    let draw;
    if (s < step) draw = 1;
    else if (s > step) draw = 0;
    else {
      const k = state.wiresByStep[s].length;
      const seg = local * k;
      draw = clamp(seg - wire.order);
      if (!packetPlaced && draw > 0 && draw < 1) {
        const pt = wire.el.getPointAtLength(draw * wire.length);
        state.packet.setAttribute('transform', `translate(${pt.x} ${pt.y})`);
        state.packet.style.opacity = '1';
        state.packetRect.style.fill = packetColor(wire.el);
        if (state.packetText.textContent !== wire.label) state.packetText.textContent = wire.label;
        packetPlaced = true;
      }
    }
    wire.el.style.strokeDashoffset = String(wire.length * (1 - draw));
  });
  if (!packetPlaced) state.packet.style.opacity = '0';
}

function initDiagram() {
  const pin = document.querySelector('[data-how-pin]');
  const diagram = document.querySelector('[data-diagram]');
  if (!pin || !diagram) return;
  const state = {
    step: -1,
    stepEls: Array.from(pin.querySelectorAll('.how-step')),
    bars: Array.from(pin.querySelectorAll('.how-progress b')),
    nodes: Array.from(diagram.querySelectorAll('.node')),
    packet: diagram.querySelector('[data-packet]'),
    packetRect: diagram.querySelector('[data-packet] rect'),
    packetText: diagram.querySelector('[data-packet-label]'),
    wires: [],
    wiresByStep: {},
  };
  diagram.querySelectorAll('.wire').forEach((el) => {
    const step = Number(el.dataset.step);
    state.wiresByStep[step] = state.wiresByStep[step] || [];
    const wire = { el, step, order: state.wiresByStep[step].length, length: el.getTotalLength(), label: el.dataset.label || '' };
    state.wiresByStep[step].push(wire);
    state.wires.push(wire);
    el.style.strokeDasharray = String(wire.length);
    el.style.strokeDashoffset = String(wire.length);
  });

  const gsap = getGsap();
  const ScrollTrigger = getScrollTrigger();
  if (!gsap || !ScrollTrigger) {
    // Reduced motion / no GSAP: show the complete diagram and all steps.
    render(state, 1);
    pin.querySelector('[data-how-steps]').classList.add('how-static');
    state.packet.style.opacity = '0';
    return;
  }
  render(state, 0);
  ScrollTrigger.create({
    trigger: pin,
    start: 'top top',
    end: () => `+=${window.innerHeight * 4}`,
    pin: true,
    scrub: 0.6,
    anticipatePin: 1,
    onUpdate: (self) => render(state, self.progress),
  });
}

function initSequence() {
  const gsap = getGsap();
  const svg = document.querySelector('[data-seq]');
  if (!gsap || !svg) return;
  const msgs = svg.querySelectorAll('[data-seq-msg]');
  gsap.from(msgs, {
    opacity: 0,
    x: -16,
    duration: 0.6,
    ease: 'power3.out',
    stagger: 0.12,
    scrollTrigger: { trigger: svg, start: 'top 75%', once: true },
  });
}

export function init() {
  initDiagram();
  initSequence();
}
