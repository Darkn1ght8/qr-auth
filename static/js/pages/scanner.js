// Phone scanner (html5-qrcode).
// - Live camera needs a secure context (HTTPS or localhost).
// - Over plain HTTP in the local network the "take a photo" path still works:
//   the phone camera app takes a picture and html5-qrcode decodes it from the file.
// Only links to this site's /qr/scan/ endpoint are opened (anti-phishing).
import { t } from '../lib/i18n.js';

const SCAN_PATH = /^\/qr\/scan\/[^/]+\/[^/]+\/?$/;

function validate(text, allowedOrigins) {
  let url;
  try { url = new URL(String(text).trim()); } catch (_) { return { ok: false, reason: t('Этот QR-код — не ссылка.') }; }
  if (!allowedOrigins.includes(url.origin)) {
    return { ok: false, reason: t('Этот QR ведёт на другой сайт ({host}) — ради безопасности он не откроется.', { host: url.host }) };
  }
  if (!SCAN_PATH.test(url.pathname)) {
    return { ok: false, reason: t('Это не QR-код для входа. Откройте на компьютере страницу «Войти по QR».') };
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
    say(t('QR распознан, открываем…'));
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
    idleText.textContent = t('Нажмите «Сфотографировать и распознать» и сфотографируйте QR на компьютере.');
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
      say(t('Библиотека сканера не загрузилась. Проверьте подключение к интернету.'), true);
      return;
    }
    handled = false;
    scanner = new window.Html5Qrcode('reader', { verbose: false });
    startBtn.hidden = true;
    stopBtn.hidden = false;
    say(t('Включаем камеру…'));
    try {
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 12, aspectRatio: 1, qrbox: (w, h) => { const s = Math.floor(Math.min(w, h) * 0.7); return { width: s, height: s }; } },
        onDecoded,
        () => { /* per-frame decode misses are expected */ }
      );
      box.classList.add('is-running');
      say(t('Наведите рамку на QR-код'));
    } catch (err) {
      await stop();
      const denied = /NotAllowed|Permission/i.test(String(err));
      say(denied
        ? t('Нет доступа к камере. Разрешите его в настройках браузера или используйте «Сфотографировать и распознать».')
        : t('Не удалось включить камеру. Используйте «Сфотографировать и распознать».'), true);
    }
  }

  async function scanPhoto(file) {
    if (!file) return;
    if (!window.Html5Qrcode) { say(t('Библиотека сканера не загрузилась. Проверьте подключение к интернету.'), true); return; }
    await stop();
    say(t('Обрабатываем фото…'));
    const reader = new window.Html5Qrcode('reader-file', { verbose: false });
    try {
      const text = await reader.scanFile(file, false);
      onDecoded(text);
    } catch (_) {
      say(t('На фото не найден QR. Сфотографируйте код ближе, чётко и целиком.'), true);
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
