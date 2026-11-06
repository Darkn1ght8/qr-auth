// Phone scanner (html5-qrcode).
// - Live camera needs a secure context (HTTPS or localhost).
// - Over plain HTTP in the local network the "take a photo" path still works:
//   the phone camera app takes a picture and html5-qrcode decodes it from the file.
// Only links to this site's /qr/scan/ endpoint are opened (anti-phishing).

const SCAN_PATH = /^\/qr\/scan\/[^/]+\/[^/]+\/?$/;

function validate(text, allowedOrigins) {
  let url;
  try { url = new URL(String(text).trim()); } catch (_) { return { ok: false, reason: 'Бұл QR-код сілтеме емес.' }; }
  if (!allowedOrigins.includes(url.origin)) {
    return { ok: false, reason: `Бұл QR басқа сайтқа (${url.host}) апарады — қауіпсіздік үшін ашылмайды.` };
  }
  if (!SCAN_PATH.test(url.pathname)) {
    return { ok: false, reason: 'Бұл кіруге арналған QR-код емес. Компьютерде «QR арқылы кіру» бетін ашыңыз.' };
  }
  return { ok: true, url: url.href };
}

export function init() {
  const root = document.querySelector('[data-scanner]');
  if (!root) return;
  const allowed = [window.location.origin];
  if (root.dataset.publicBase) allowed.push(new URL(root.dataset.publicBase).origin);

  const box = root.querySelector('[data-scanner-box]');
  const msg = root.querySelector('[data-scanner-msg]');
  const startBtn = root.querySelector('[data-scanner-start]');
  const stopBtn = root.querySelector('[data-scanner-stop]');
  const photoInput = root.querySelector('[data-photo-input]');
  const photoLabel = root.querySelector('[data-photo-label]');
  const idleText = root.querySelector('[data-idle-text]');
  const form = root.querySelector('[data-manual-form]');
  const liveCamera = window.isSecureContext && !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  let scanner = null;
  let handled = false;

  const say = (text, isError = false) => {
    msg.textContent = text;
    msg.classList.toggle('is-error', isError);
  };

  const go = (result) => {
    handled = true;
    if (navigator.vibrate) navigator.vibrate(60);
    say('QR танылды, ашылуда…');
    window.location.href = result.url;
  };

  const onDecoded = (text) => {
    if (handled) return;
    const result = validate(text, allowed);
    if (result.ok) stop().then(() => go(result));
    else say(result.reason, true);
  };

  if (!liveCamera) {
    // Plain HTTP: live video is blocked by the browser, so lead with the photo option.
    startBtn.hidden = true;
    photoLabel.classList.replace('btn--ghost', 'btn--primary');
    idleText.textContent = '«Суретке түсіріп сканерлеу» батырмасын басып, компьютердегі QR-ды суретке түсіріңіз.';
  }

  async function stop() {
    if (scanner) {
      try { await scanner.stop(); } catch (_) { /* already stopped */ }
      try { scanner.clear(); } catch (_) { /* ignore */ }
    }
    scanner = null;
    box.classList.remove('is-running');
    startBtn.hidden = !liveCamera;
    stopBtn.hidden = true;
  }

  async function start() {
    if (!window.Html5Qrcode) {
      say('Сканер кітапханасы жүктелмеді. Интернет байланысын тексеріңіз.', true);
      return;
    }
    handled = false;
    scanner = new window.Html5Qrcode('reader', { verbose: false });
    startBtn.hidden = true;
    stopBtn.hidden = false;
    say('Камера қосылуда…');
    try {
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 12, aspectRatio: 1, qrbox: (w, h) => { const s = Math.floor(Math.min(w, h) * 0.7); return { width: s, height: s }; } },
        onDecoded,
        () => { /* per-frame decode misses are expected */ }
      );
      box.classList.add('is-running');
      say('QR-кодты рамкаға бағыттаңыз');
    } catch (err) {
      await stop();
      const denied = /NotAllowed|Permission/i.test(String(err));
      say(denied
        ? 'Камераға рұқсат берілмеді. Браузер баптауларынан рұқсат беріңіз немесе «Суретке түсіріп сканерлеу» батырмасын қолданыңыз.'
        : 'Камераны қосу мүмкін болмады. «Суретке түсіріп сканерлеу» батырмасын қолданыңыз.', true);
    }
  }

  async function scanPhoto(file) {
    if (!file) return;
    if (!window.Html5Qrcode) { say('Сканер кітапханасы жүктелмеді. Интернет байланысын тексеріңіз.', true); return; }
    await stop();
    say('Сурет өңделуде…');
    const reader = new window.Html5Qrcode('reader-file', { verbose: false });
    try {
      const text = await reader.scanFile(file, false);
      onDecoded(text);
    } catch (_) {
      say('Суреттен QR табылмады. Кодты жақынырақ, анық және толық түсіріп көріңіз.', true);
    } finally {
      try { reader.clear(); } catch (_) { /* ignore */ }
      photoInput.value = '';
    }
  }

  startBtn.addEventListener('click', start);
  stopBtn.addEventListener('click', () => { stop(); say(''); });
  photoInput.addEventListener('change', () => scanPhoto(photoInput.files[0]));
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const result = validate(form.querySelector('input').value, allowed);
    if (result.ok) go(result); else say(result.reason, true);
  });
  window.addEventListener('pagehide', stop);
}
