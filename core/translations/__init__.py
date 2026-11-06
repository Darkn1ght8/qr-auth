"""Translations: Russian source phrase -> (Kazakh, English).

Split by area of the site; merged here. A test checks that every phrase used
in templates, Python code and JavaScript has both translations.
"""
from . import auth, common, js, pages, panel, qr

TRANSLATIONS: dict[str, tuple[str, str]] = {}
for module in (common, pages, auth, qr, panel, js):
    TRANSLATIONS.update(module.T)
