from .i18n import HTML_LANG, LANGUAGES, SHORT_NAMES, current_language, translate
from .translations.js import JS_KEYS

NAV = [
    ("core:overview", "Обзор"),
    ("core:how", "Как это работает"),
    ("core:demo", "Демо"),
    ("core:testing", "Тестирование"),
    ("core:security", "Безопасность"),
]


def _switch_url(request, code: str) -> str:
    params = request.GET.copy()
    params["lang"] = code
    return f"{request.path}?{params.urlencode()}"


def site(request):
    match = getattr(request, "resolver_match", None)
    current = f"{match.namespace}:{match.url_name}" if match and match.namespace else ""
    lang = current_language()
    return {
        "nav_items": [(route, translate(label, lang)) for route, label in NAV],
        "current_route": current,
        "lang": lang,
        "html_lang": HTML_LANG[lang],
        # (code, "RU", "Русский", url that switches to it and keeps the current query)
        "languages": [(code, SHORT_NAMES[code], name, _switch_url(request, code)) for code, name in LANGUAGES.items()],
        # Phrases used by the JavaScript modules, in the current language.
        "js_i18n": {key: translate(key, lang) for key in JS_KEYS},
    }
