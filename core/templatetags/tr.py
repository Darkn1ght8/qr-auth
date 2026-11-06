"""Template helpers for the three languages.

    {% t "Текст на русском" %}
    {% t "Привет, {name}" name=user.username %}     (params are HTML-escaped)
    {% t "Текст" as label %}
    {{ some_value|tr }}                               (translate data, e.g. DB labels)
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.i18n import translate

register = template.Library()


@register.simple_tag(name="t")
def t_tag(text, **params):
    translated = translate(str(text))
    # Phrases are trusted constants from core.translations (some contain <b>/<a> markup);
    # parameters are escaped by format_html.
    return format_html(translated, **params) if params else mark_safe(translated)


@register.filter(name="tr")
def tr_filter(value):
    return translate(str(value)) if value is not None else ""
