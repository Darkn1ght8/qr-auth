// Translations for scripts. The page embeds the phrases of the current language
// (JSON in #i18n-data, built from core/translations/js.py); keys are Russian.
let dict = null;

function load() {
  if (dict) return dict;
  try {
    const node = document.getElementById('i18n-data');
    dict = node ? JSON.parse(node.textContent) : {};
  } catch (_) {
    dict = {};
  }
  return dict;
}

export function t(text, vars) {
  let out = load()[text] || text;
  if (vars) {
    Object.entries(vars).forEach(([key, value]) => { out = out.split(`{${key}}`).join(String(value)); });
  }
  return out;
}

export function pageLang() {
  return document.documentElement.lang || 'ru';
}
