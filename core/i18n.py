"""Three-language support: Russian (default, source text), Kazakh, English.

Every user-visible phrase is written in Russian and looked up in
`core.translations` for Kazakh and English. Django's own messages (form
errors, password validators, "5 minutes ago") are translated by Django's
built-in catalogs, which are activated for the same language.
"""
from __future__ import annotations

from django.utils import translation
from django.utils.functional import lazy

from .translations import TRANSLATIONS

DEFAULT_LANGUAGE = "ru"
LANGUAGES = {"ru": "Русский", "kk": "Қазақша", "en": "English"}
SHORT_NAMES = {"ru": "RU", "kk": "KZ", "en": "EN"}
HTML_LANG = {"ru": "ru", "kk": "kk", "en": "en"}
COOKIE_NAME = "lang"
_INDEX = {"kk": 0, "en": 1}


def current_language() -> str:
    lang = (translation.get_language() or DEFAULT_LANGUAGE)[:2]
    return lang if lang in LANGUAGES else DEFAULT_LANGUAGE


def translate(text: str, lang: str | None = None) -> str:
    """Russian source text -> text in `lang` (falls back to Russian if missing)."""
    lang = lang or current_language()
    if lang == "ru" or not text:
        return text
    entry = TRANSLATIONS.get(text)
    if entry is None:
        return text
    return entry[_INDEX[lang]] or text


def t(text: str, **params) -> str:
    """Translate and fill `{name}` placeholders."""
    translated = translate(text)
    return translated.format(**params) if params else translated


t_lazy = lazy(t, str)


class LanguageMiddleware:
    """Pick the language: ?lang=xx (saved in a cookie) > cookie > Russian.

    The browser's Accept-Language is deliberately ignored: Russian is the default.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.http import HttpResponseRedirect

        chosen = request.GET.get("lang")
        if chosen in LANGUAGES and request.method == "GET":
            params = request.GET.copy()
            params.pop("lang")
            target = request.path + (f"?{params.urlencode()}" if params else "")
            response = HttpResponseRedirect(target)
            response.set_cookie(COOKIE_NAME, chosen, max_age=60 * 60 * 24 * 365, samesite="Lax",
                                secure=request.is_secure(), httponly=True)
            return response

        lang = request.COOKIES.get(COOKIE_NAME)
        if lang not in LANGUAGES:
            lang = DEFAULT_LANGUAGE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        translation.deactivate()
        return response


def N_(text: str) -> str:
    """Mark a Russian phrase for translation without translating it now
    (data that templates show with the |tr filter)."""
    return text
