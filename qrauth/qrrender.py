"""Server-side QR generation: returns an SVG string and the raw module matrix."""
from __future__ import annotations

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def build_matrix(data: str, error_correction=ERROR_CORRECT_M) -> list[list[bool]]:
    qr = qrcode.QRCode(error_correction=error_correction, border=0, box_size=1)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.get_matrix()


def matrix_to_svg(matrix: list[list[bool]], quiet_zone: int = 2, css_class: str = "qr-svg") -> str:
    size = len(matrix) + quiet_zone * 2
    parts = []
    for y, row in enumerate(matrix):
        x = 0
        while x < len(row):
            if row[x]:
                run = 1
                while x + run < len(row) and row[x + run]:
                    run += 1
                parts.append(f"M{x + quiet_zone} {y + quiet_zone}h{run}v1h-{run}z")
                x += run
            else:
                x += 1
    path = "".join(parts)
    return (
        f'<svg class="{css_class}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'shape-rendering="crispEdges" role="img" aria-label="QR-код">'
        f'<rect width="{size}" height="{size}" fill="#fff"/>'
        f'<path d="{path}" fill="#07090F"/></svg>'
    )


def render(data: str) -> tuple[str, list[str]]:
    """Return (svg, rows) where rows are '0'/'1' strings for the JS particle renderer."""
    matrix = build_matrix(data)
    rows = ["".join("1" if cell else "0" for cell in row) for row in matrix]
    return matrix_to_svg(matrix), rows
