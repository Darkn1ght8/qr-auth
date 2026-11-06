// Phone confirmation page: live countdown until the QR request expires.
export function init() {
  const bar = document.querySelector('[data-countdown]');
  const label = document.querySelector('[data-countdown-text]');
  if (!bar) return;
  const total = parseInt(bar.dataset.total, 10) || 60;
  const deadline = Date.now() + (parseInt(bar.dataset.countdown, 10) || 0) * 1000;
  const buttons = document.querySelectorAll('.decide button');
  const tick = () => {
    const left = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    bar.style.transform = `scaleX(${left / total})`;
    if (label) label.textContent = String(left);
    if (left <= 0) {
      buttons.forEach((b) => { if (b.value === 'confirm') b.disabled = true; });
      if (label) label.parentElement.textContent = 'Сұраудың мерзімі өтті. Компьютерде жаңа QR ашыңыз.';
      return;
    }
    setTimeout(tick, 250);
  };
  tick();
}
