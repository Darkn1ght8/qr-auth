// Minimal SplitText alternative: splits text nodes into word/char spans.
// Child elements (e.g. <span class="grad">) are kept intact and treated as one unit
// so gradients and links keep working.

export function splitText(el) {
  if (el.dataset.splitDone) return Array.from(el.querySelectorAll('.split-char'));
  const label = el.textContent.trim().replace(/\s+/g, ' ');
  el.setAttribute('aria-label', label);
  const units = [];

  const processNode = (node, parent) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const parts = node.textContent.split(/(\s+)/);
      const fragment = document.createDocumentFragment();
      parts.forEach((part) => {
        if (!part) return;
        if (/^\s+$/.test(part)) { fragment.appendChild(document.createTextNode(' ')); return; }
        const word = document.createElement('span');
        word.className = 'split-word';
        word.setAttribute('aria-hidden', 'true');
        Array.from(part).forEach((ch) => {
          const c = document.createElement('span');
          c.className = 'split-char';
          c.textContent = ch;
          word.appendChild(c);
          units.push(c);
        });
        fragment.appendChild(word);
      });
      parent.replaceChild(fragment, node);
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      const wrapper = document.createElement('span');
      wrapper.className = 'split-word';
      wrapper.setAttribute('aria-hidden', 'true');
      const unit = document.createElement('span');
      unit.className = 'split-char';
      parent.replaceChild(wrapper, node);
      unit.appendChild(node);
      wrapper.appendChild(unit);
      units.push(unit);
    }
  };

  Array.from(el.childNodes).forEach((node) => processNode(node, el));
  el.dataset.splitDone = '1';
  return units;
}
