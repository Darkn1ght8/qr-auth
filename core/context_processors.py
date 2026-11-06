NAV = [
    ("core:overview", "Шолу"),
    ("core:how", "Қалай жұмыс істейді"),
    ("core:demo", "Демо"),
    ("core:testing", "Тестілеу"),
    ("core:security", "Қауіпсіздік"),
]


def site(request):
    match = getattr(request, "resolver_match", None)
    current = f"{match.namespace}:{match.url_name}" if match and match.namespace else ""
    return {
        "nav_items": NAV,
        "current_route": current,
        "project_title": "QR-код арқылы қауіпсіз аутентификация жүйесі",
    }
