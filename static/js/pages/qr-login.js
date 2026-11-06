// Desktop QR login controller.
// pending -> scanned -> confirmed | rejected | expired, delivered via WebSocket
// (or long-polling fallback). The confirmed event carries a one-time code that
// is exchanged for a Django session together with the browser fingerprint.
import { QRParticles, confettiBurst } from '../lib/qr-canvas.js';
import { t } from '../lib/i18n.js';
import { postJSON, getGsap, reducedMotion } from '../lib/env.js';
import { navigate } from '../lib/transitions.js';

const STATUS_TEXT = {
  loading: t('Готовим QR…'),
  pending: t('Отсканируйте телефоном'),
  opened: t('Войдите в аккаунт на телефоне'),
  scanned: t('Подтвердите на телефоне'),
  confirmed: t('Подтверждено! Переходим в кабинет…'),
  rejected: t('Вход отклонён'),
  expired: t('Срок QR истёк'),
  error: t('Произошла ошибка'),
};

function deviceId() {
  try {
    let id = localStorage.getItem('qrauth.device');
    if (!id) {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      id = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
      localStorage.setItem('qrauth.device', id);
    }
    return id;
  } catch (_) {
    return 'no-storage';
  }
}

function fingerprint() {
  const parts = [
    deviceId(),
    navigator.language,
    (navigator.languages || []).join(','),
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    `${screen.width}x${screen.height}x${screen.colorDepth}`,
    navigator.hardwareConcurrency || 0,
    navigator.platform || '',
  ];
  return parts.join('|').slice(0, 512);
}

export function init() {
  const root = document.querySelector('[data-qr-login]');
  if (!root) return;

  const el = {
    stage: root.querySelector('[data-qr-stage]'),
    canvas: root.querySelector('[data-qr-canvas]'),
    ring: root.querySelector('[data-qr-ring]'),
    status: root.querySelector('[data-qr-status]'),
    statusText: root.querySelector('[data-qr-status-text]'),
    refresh: root.querySelector('[data-qr-refresh]'),
    channel: root.querySelector('[data-qr-channel]'),
    sid: root.querySelector('[data-qr-sid]'),
    overlayScanned: root.querySelector('[data-overlay="scanned"]'),
    overlayExpired: root.querySelector('[data-overlay="expired"]'),
    expiredTitle: root.querySelector('[data-expired-title]'),
    expiredText: root.querySelector('[data-expired-text]'),
    scannedUser: root.querySelector('[data-scanned-user]'),
    retry: root.querySelector('[data-qr-retry]'),
    check: root.querySelector('[data-qr-check]'),
    flash: root.querySelector('[data-qr-flash]'),
    confetti: root.querySelector('[data-qr-confetti]'),
    frame: root.querySelector('[data-qr-frame]'),
  };
  const cfg = {
    apiNew: root.dataset.apiNew,
    apiExchange: root.dataset.apiExchange,
    ttl: parseInt(root.dataset.ttl, 10) || 60,
    refresh: parseInt(root.dataset.refresh, 10) || 30,
  };

  const renderer = new QRParticles(el.canvas);
  const fp = fingerprint();
  const s = {
    sid: null, state: 'loading', expiresAt: 0, refreshAt: 0,
    ws: null, polling: false, exchanging: false, busy: false, finished: false,
  };

  // ---------- UI state ----------
  function setState(state, extra = {}) {
    s.state = state;
    el.status.dataset.state = state;
    el.statusText.textContent = extra.text || STATUS_TEXT[state] || state;
    ['is-scanned', 'is-confirmed', 'is-expired', 'is-rejected'].forEach((c) => el.stage.classList.remove(c));
    if (state === 'scanned' || state === 'confirmed' || state === 'expired' || state === 'rejected') el.stage.classList.add(`is-${state}`);
    el.overlayScanned.classList.toggle('is-visible', state === 'scanned');
    const dead = state === 'expired' || state === 'rejected' || state === 'error';
    el.overlayExpired.classList.toggle('is-visible', dead);
    if (dead) {
      el.expiredTitle.textContent = extra.title || STATUS_TEXT[state];
      el.expiredText.textContent = extra.text || (state === 'rejected'
        ? t('Пользователь на телефоне отклонил этот запрос.')
        : t('Ради безопасности код перестаёт действовать через 60 секунд.'));
      if (state === 'expired' && extra.text) el.statusText.textContent = STATUS_TEXT.expired;
    }
    if (state === 'scanned') {
      el.scannedUser.textContent = extra.user ? t('Аккаунт: {user}', { user: extra.user }) : '';
      const gsap = getGsap();
      if (gsap) gsap.fromTo(el.overlayScanned.firstElementChild, { scale: 0.85, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: 'back.out(2)' });
    }
  }

  function setChannel(name) { el.channel.textContent = name; }

  // ---------- countdown ring ----------
  function tick() {
    if (s.finished) return;
    const now = Date.now();
    if (s.state === 'pending' || s.state === 'scanned') {
      const left = Math.max(0, s.expiresAt - now);
      const ratio = Math.min(1, left / (s.window || cfg.ttl * 1000));
      el.ring.setAttribute('stroke-dashoffset', String(1 - ratio));
      el.stage.classList.toggle('is-low', ratio < 0.25 && s.state === 'pending');
      if (s.state === 'pending') {
        const toRefresh = Math.max(0, Math.ceil((s.refreshAt - now) / 1000));
        el.refresh.textContent = t('{n} с', { n: toRefresh });
        if (s.opened) el.refresh.textContent = t('остановлено');
        else if (now >= s.refreshAt && !s.busy && !document.hidden) issueQR(true);
      } else {
        el.refresh.textContent = t('остановлено');
      }
      if (left <= 0 && (s.state === 'scanned' || s.opened)) requestStatus();
    }
    requestAnimationFrame(tick);
  }

  // ---------- network ----------
  async function issueQR(isRefresh) {
    s.busy = true;
    closeChannel();
    if (!isRefresh) setState('loading');
    const { ok, data, status } = await postJSON(cfg.apiNew, { fp }).catch(() => ({ ok: false, data: {}, status: 0 }));
    s.busy = false;
    if (!ok) {
      setState('error', {
        title: status === 429 ? t('Слишком много запросов') : t('Не удалось создать QR'),
        text: data.message || t('Проверьте подключение к сети и попробуйте снова.'),
      });
      return;
    }
    s.sid = data.sid;
    s.opened = false;
    s.window = data.ttl * 1000;
    s.expiresAt = Date.now() + data.ttl * 1000;
    s.refreshAt = Date.now() + data.refresh * 1000;
    el.sid.textContent = data.sid.slice(0, 8);
    el.stage.classList.remove('is-glitch');
    el.frame.style.opacity = '';
    setState('pending');
    renderer.transitionTo(data.matrix);
    openChannel(data);
  }

  function closeChannel() {
    if (s.ws) {
      s.ws.onclose = null;
      s.ws.onmessage = null;
      try { s.ws.close(); } catch (_) { /* ignore */ }
      s.ws = null;
    }
    s.polling = false;
  }

  function openChannel(data) {
    if (!('WebSocket' in window)) { startPolling(data.sid, data.poll); return; }
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const sid = data.sid;
    let opened = false;
    const ws = new WebSocket(`${proto}://${window.location.host}${data.ws}`);
    s.ws = ws;
    const fallbackTimer = setTimeout(() => { if (!opened && s.sid === sid) { closeChannel(); startPolling(sid, data.poll); } }, 3500);
    ws.onopen = () => { opened = true; clearTimeout(fallbackTimer); setChannel('WebSocket'); };
    ws.onmessage = (event) => {
      try { handle(JSON.parse(event.data)); } catch (_) { /* ignore malformed */ }
    };
    ws.onclose = () => {
      clearTimeout(fallbackTimer);
      if (s.sid === sid && !s.finished && ['pending', 'scanned', 'confirmed'].includes(s.state)) {
        s.ws = null;
        startPolling(sid, data.poll);
      }
    };
    s.pollUrl = data.poll;
  }

  async function startPolling(sid, url) {
    if (s.polling) return;
    s.polling = true;
    setChannel('Long-polling');
    while (s.polling && s.sid === sid && !s.finished) {
      try {
        const res = await fetch(`${url}?since=${encodeURIComponent(s.state)}`, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
        if (res.status === 403) { s.polling = false; break; }
        const payload = await res.json();
        if (s.sid === sid) handle(payload);
      } catch (_) {
        await new Promise((r) => setTimeout(r, 2000));
      }
    }
  }

  function requestStatus() {
    if (s.ws && s.ws.readyState === WebSocket.OPEN) {
      if (!s.pingAt || Date.now() - s.pingAt > 1500) { s.pingAt = Date.now(); s.ws.send(JSON.stringify({ type: 'ping' })); }
    }
  }

  function handle(payload) {
    if (!payload || payload.sid !== s.sid || s.finished) return;
    switch (payload.status) {
      case 'pending':
        if (payload.opened && !s.opened) {
          // Phone opened the link and is signing in: hold this QR (server extended its TTL).
          s.opened = true;
          s.expiresAt = Date.now() + payload.seconds_left * 1000;
          s.window = payload.seconds_left * 1000;
          setState('pending', { text: STATUS_TEXT.opened });
        } else if (s.state !== 'pending') setState('pending');
        break;
      case 'scanned':
        if (s.state !== 'scanned') {
          s.expiresAt = Date.now() + payload.seconds_left * 1000;
          setState('scanned', { user: payload.user });
        }
        break;
      case 'confirmed':
        if (payload.code && !s.exchanging) exchange(payload.code);
        break;
      case 'rejected':
        die('rejected');
        break;
      case 'expired':
        if (!s.busy) die('expired');
        break;
      default:
        break;
    }
  }

  function die(state, extra) {
    closeChannel();
    setState(state, extra);
    if (!reducedMotion) {
      el.stage.classList.add('is-glitch');
    }
    el.ring.setAttribute('stroke-dashoffset', '1');
    el.refresh.textContent = '—';
  }

  async function exchange(code) {
    s.exchanging = true;
    const sid = s.sid;
    const { ok, data } = await postJSON(cfg.apiExchange, { sid, code, fp }).catch(() => ({ ok: false, data: {} }));
    if (!ok) {
      s.exchanging = false;
      die('error', { title: t('Вход заблокирован'), text: data.message || t('Не удалось обменять код на сессию.') });
      return;
    }
    s.finished = true;
    closeChannel();
    await playSuccess();
    navigate(data.redirect || '/cabinet/');
  }

  async function playSuccess() {
    setState('confirmed');
    el.ring.setAttribute('stroke-dashoffset', '0');
    el.refresh.textContent = '✓';
    const gsap = getGsap();
    // rAF pauses in background tabs; never let the redirect wait on it forever.
    await Promise.race([renderer.collapse(), new Promise((r) => setTimeout(r, 1200))]);
    const [circle, path] = el.check.querySelectorAll('circle, path');
    if (!gsap) {
      el.check.style.opacity = '1';
      circle.setAttribute('stroke-dashoffset', '0');
      path.setAttribute('stroke-dashoffset', '0');
      await new Promise((r) => setTimeout(r, 900));
      return;
    }
    el.frame.style.opacity = '0';
    const tl = gsap.timeline();
    tl.set(el.check, { opacity: 1 })
      .fromTo(el.flash, { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1.2, duration: 0.35, ease: 'power2.out' }, 0)
      .to(el.flash, { opacity: 0, duration: 0.9, ease: 'power2.out' }, 0.35)
      .fromTo(circle, { attr: { 'stroke-dashoffset': 1 } }, { attr: { 'stroke-dashoffset': 0 }, duration: 0.7, ease: 'power2.out' }, 0.05)
      .fromTo(path, { attr: { 'stroke-dashoffset': 1 } }, { attr: { 'stroke-dashoffset': 0 }, duration: 0.5, ease: 'power3.out' }, 0.45)
      .fromTo(el.check, { scale: 0.6 }, { scale: 1, duration: 0.9, ease: 'elastic.out(1, 0.5)' }, 0);
    confettiBurst(el.confetti);
    await new Promise((r) => setTimeout(r, 1700));
  }

  el.retry.addEventListener('click', () => {
    s.exchanging = false;
    issueQR(false);
  });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && s.state === 'pending' && !s.opened && Date.now() >= s.refreshAt && !s.busy) issueQR(true);
  });

  issueQR(false);
  requestAnimationFrame(tick);
}
