// Cabinet: refresh sessions, stats and the login journal live when the server
// reports a change (new login on a phone, scanned QR, ended session, ...).
// The fresh HTML comes from our own server (Django-escaped template output).

let timer = null;
let busy = false;

async function refresh() {
  if (busy) return;
  busy = true;
  try {
    const res = await fetch(window.location.pathname + window.location.search, { credentials: 'same-origin', cache: 'no-store', headers: { 'X-Requested-With': 'live' } });
    if (!res.ok || res.redirected) return; // logged out: live-session.js handles it
    const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
    document.querySelectorAll('[data-live]').forEach((region) => {
      const fresh = doc.querySelector(`[data-live="${region.dataset.live}"]`);
      if (!fresh || fresh.innerHTML === region.innerHTML) return;
      region.replaceChildren(...Array.from(fresh.childNodes).map((n) => document.importNode(n, true)));
      region.classList.remove('is-flash');
      void region.offsetWidth; // restart the highlight animation
      region.classList.add('is-flash');
    });
  } catch (_) {
    /* network hiccup: the next change event retries */
  } finally {
    busy = false;
  }
}

export function init() {
  document.addEventListener('qrauth:sessions-changed', () => {
    clearTimeout(timer);
    timer = setTimeout(refresh, 300);
  });
  // Also catch up when the laptop tab becomes visible again.
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
}
