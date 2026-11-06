// Live session channel for logged-in pages.
// - "revoked": this session was ended on another device -> log out on this page right now.
// - "changed": sessions/journal changed -> pages listening for `qrauth:sessions-changed` refresh.
// Falls back to polling /api/session/ when WebSocket is unavailable.
import { t } from './i18n.js';

const POLL_MS = 6000;
const PING_MS = 25000;

let revokedShown = false;

function showRevoked(loginUrl) {
  if (revokedShown) return;
  revokedShown = true;
  const overlay = document.createElement('div');
  overlay.className = 'revoked-overlay';
  overlay.setAttribute('role', 'alertdialog');
  overlay.setAttribute('aria-live', 'assertive');
  const card = document.createElement('div');
  card.className = 'revoked-overlay__card';
  card.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg>';
  const title = document.createElement('p');
  title.className = 'revoked-overlay__title';
  title.textContent = t('Сессия завершена');
  const text = document.createElement('p');
  text.className = 'revoked-overlay__text';
  text.textContent = t('Вход на этом устройстве был остановлен с другого устройства. В целях безопасности вы вышли из системы.');
  card.append(title, text);
  overlay.appendChild(card);
  document.body.appendChild(overlay);
  setTimeout(() => { window.location.replace(`${loginUrl}?revoked=1`); }, 1800);
}

export function initLiveSession() {
  const body = document.body;
  if (body.dataset.auth !== '1') return;
  const api = body.dataset.sessionApi;
  const loginUrl = body.dataset.loginUrl || '/login/password/';
  let ws = null;
  let pollTimer = null;
  let pingTimer = null;
  let retries = 0;

  const changed = () => document.dispatchEvent(new CustomEvent('qrauth:sessions-changed'));

  async function poll() {
    try {
      const res = await fetch(api, { credentials: 'same-origin', headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (res.status === 401) { showRevoked(loginUrl); return; }
    } catch (_) { /* offline: try again later */ }
    pollTimer = setTimeout(poll, POLL_MS);
  }

  function startPolling() {
    if (!pollTimer) pollTimer = setTimeout(poll, 500);
  }

  function connect() {
    if (!('WebSocket' in window)) { startPolling(); return; }
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${window.location.host}/ws/session/`);
    ws.onopen = () => {
      retries = 0;
      clearTimeout(pollTimer); pollTimer = null;
      clearInterval(pingTimer);
      pingTimer = setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send('{"type":"ping"}'); }, PING_MS);
    };
    ws.onmessage = (event) => {
      let msg = {};
      try { msg = JSON.parse(event.data); } catch (_) { return; }
      if (msg.type === 'revoked') showRevoked(loginUrl);
      else if (msg.type === 'changed') changed();
    };
    ws.onclose = (event) => {
      clearInterval(pingTimer);
      if (revokedShown) return;
      if (event.code === 4401) { poll(); return; } // server says: not logged in any more
      // Network hiccup / server restart: poll meanwhile, then reconnect with backoff.
      startPolling();
      retries += 1;
      setTimeout(connect, Math.min(30000, 1000 * 2 ** Math.min(retries, 5)));
    };
  }

  // Coming back to a tab (phone unlocked) must reflect a revoke that happened meanwhile.
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) poll();
  });

  connect();
}
