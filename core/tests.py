"""Every phrase shown on the site exists in Russian, Kazakh and English."""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client

from core import translations
from core.i18n import translate
from core.translations import TRANSLATIONS
from core.translations.js import JS_KEYS

BASE = Path(settings.BASE_DIR)
TEMPLATE_RE = re.compile(r"""{%\s*t\s+(["'])(.*?)\1""", re.S)
PY_RE = re.compile(r"""\b(?:t|t_lazy|translate|N_)\(\s*(["'])(.*?)(?<!\\)\1""", re.S)
JS_RE = re.compile(r"""\bt\(\s*(['"])(.*?)(?<!\\)\1""", re.S)
PLACEHOLDER = re.compile(r"{(\w+)}")


def _phrases():
    found = {}
    for path in (BASE / "templates").rglob("*.html"):
        for _, text in TEMPLATE_RE.findall(path.read_text(encoding="utf-8")):
            found.setdefault(text, path.relative_to(BASE))
    for app in ("accounts", "core", "qrauth", "panel"):
        for path in (BASE / app).rglob("*.py"):
            if "migrations" in path.parts or path.name == "tests.py" or "translations" in path.parts or "tests" in path.parts:
                continue
            for _, text in PY_RE.findall(path.read_text(encoding="utf-8")):
                found.setdefault(text, path.relative_to(BASE))
    for path in (BASE / "static" / "js").rglob("*.js"):
        for _, text in JS_RE.findall(path.read_text(encoding="utf-8")):
            found.setdefault(text, path.relative_to(BASE))
    return found


def test_every_phrase_is_translated():
    missing = [f"{where}: {text!r}" for text, where in _phrases().items() if text not in TRANSLATIONS]
    assert not missing, "Missing translations:\n" + "\n".join(sorted(missing))


def test_translations_are_complete_and_consistent():
    problems = []
    for ru, (kk, en) in TRANSLATIONS.items():
        if not kk or not en:
            problems.append(f"empty translation: {ru!r}")
        for lang, text in (("kk", kk), ("en", en)):
            if set(PLACEHOLDER.findall(ru)) != set(PLACEHOLDER.findall(text)):
                problems.append(f"placeholders differ ({lang}): {ru!r}")
    assert not problems, "\n".join(problems)


def test_no_conflicting_duplicates_between_modules():
    seen, conflicts = {}, []
    for module in (translations.common, translations.pages, translations.auth, translations.qr, translations.panel, translations.js):
        for ru, value in module.T.items():
            if ru in seen and seen[ru] != value:
                conflicts.append(ru)
            seen[ru] = value
    assert not conflicts, "Same phrase translated differently: " + ", ".join(conflicts)


def test_js_phrases_are_registered():
    used = {text for path in (BASE / "static" / "js").rglob("*.js") for _, text in JS_RE.findall(path.read_text(encoding="utf-8"))}
    assert used <= set(JS_KEYS), "Add to JS_KEYS: " + ", ".join(sorted(used - set(JS_KEYS)))


@pytest.mark.django_db
@pytest.mark.parametrize("lang,expected", [("ru", "Войти по QR"), ("kk", "QR арқылы кіру"), ("en", "Sign in with QR")])
def test_language_switch(lang, expected):
    client = Client()
    response = client.get(f"/?lang={lang}")
    assert response.status_code == 302 and response["Location"] == "/"
    page = client.get("/").content.decode()
    assert expected in page and f'<html lang="{lang}">' in page


@pytest.mark.django_db
def test_russian_is_default_even_for_kazakh_browsers():
    page = Client(HTTP_ACCEPT_LANGUAGE="kk,en;q=0.8").get("/").content.decode()
    assert '<html lang="ru">' in page and "Войти по QR" in page


def test_translate_falls_back_to_russian():
    assert translate("Фраза без перевода", "en") == "Фраза без перевода"
