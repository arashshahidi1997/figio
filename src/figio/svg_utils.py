"""SVG manipulation helpers for composing multi-panel figures.

Uses ``xml.etree.ElementTree`` (stdlib) for parsing. Handles SVG namespaces
correctly via namespace-aware element lookups.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Register namespaces so serialization doesn't mangle prefixes
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def merge_defs(svgs: list[str]) -> str:
    """Extract and merge ``<defs>`` blocks from multiple SVG fragments.

    Returns the inner content of a merged ``<defs>`` element (without the
    outer ``<defs>`` tags themselves).
    """
    merged: list[str] = []
    for svg in svgs:
        # Try namespace-aware first, then plain
        for pattern in [
            re.compile(r'<defs[^>]*>(.*?)</defs>', re.DOTALL),
            re.compile(rf'<{{{SVG_NS}}}defs[^>]*>(.*?)</{{{SVG_NS}}}defs>', re.DOTALL),
        ]:
            for m in pattern.finditer(svg):
                content = m.group(1).strip()
                if content:
                    merged.append(content)
    return "\n".join(merged)


def extract_svg_content(svg: str) -> str:
    """Strip the outer ``<svg>`` wrapper and return inner content.

    Removes the opening ``<svg ...>`` and closing ``</svg>`` tags.
    Also strips ``<defs>`` blocks (they're merged separately).
    """
    # Remove XML declaration if present
    svg = re.sub(r'<\?xml[^?]*\?>\s*', '', svg)
    # Remove doctype if present
    svg = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg)
    # Remove outer <svg> tags
    svg = re.sub(r'<svg[^>]*>', '', svg, count=1)
    svg = re.sub(r'</svg>\s*$', '', svg)
    # Remove defs blocks (merged separately)
    svg = re.sub(r'<defs[^>]*>.*?</defs>', '', svg, flags=re.DOTALL)
    return svg.strip()


def make_svg_document(
    content: str,
    width_mm: float,
    height_mm: float,
    defs: str = "",
) -> str:
    """Build a well-formed SVG document with mm-based viewBox.

    Args:
        content: Inner SVG content (groups, shapes, text).
        width_mm: Document width in millimeters.
        height_mm: Document height in millimeters.
        defs: Content for the ``<defs>`` block.
    """
    defs_block = f"  <defs>\n{defs}\n  </defs>\n" if defs else ""
    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}"\n'
        f'     width="{width_mm:.2f}mm" height="{height_mm:.2f}mm"\n'
        f'     viewBox="0 0 {width_mm:.2f} {height_mm:.2f}">\n'
        f'{defs_block}'
        f'{content}\n'
        f'</svg>\n'
    )


def extract_viewbox(svg: str) -> tuple[float, float, float, float] | None:
    """Extract the viewBox attribute from an SVG string.

    Returns a 4-tuple ``(min_x, min_y, width, height)`` or ``None`` if absent.
    """
    m = re.search(r'viewBox="([^"]+)"', svg)
    if m:
        parts = m.group(1).split()
        if len(parts) == 4:
            return tuple(float(p) for p in parts)  # type: ignore[return-value]
    return None


def prefix_ids(svg: str, prefix: str) -> str:
    """Prefix all ``id=`` and ``url(#...)`` references to avoid collisions."""
    # Prefix id="..." attributes
    svg = re.sub(
        r'id="([^"]+)"',
        lambda m: f'id="{prefix}_{m.group(1)}"',
        svg,
    )
    # Update url(#...) references
    svg = re.sub(
        r'url\(#([^)]+)\)',
        lambda m: f'url(#{prefix}_{m.group(1)})',
        svg,
    )
    # Update xlink:href="#..." references
    svg = re.sub(
        r'xlink:href="#([^"]+)"',
        lambda m: f'xlink:href="#{prefix}_{m.group(1)}"',
        svg,
    )
    # Update href="#..." references (SVG 2), but not xlink:href (already handled)
    svg = re.sub(
        r'(?<!xlink:)href="#([^"]+)"',
        lambda m: f'href="#{prefix}_{m.group(1)}"',
        svg,
    )
    return svg


def normalize_viewbox(svg: str, width_mm: float, height_mm: float) -> str:
    """Set the SVG viewBox and dimension attributes to mm units."""
    viewbox = f'0 0 {width_mm:.2f} {height_mm:.2f}'
    if 'viewBox=' in svg:
        svg = re.sub(r'viewBox="[^"]*"', f'viewBox="{viewbox}"', svg)
    else:
        svg = svg.replace("<svg ", f'<svg viewBox="{viewbox}" ', 1)
    svg = re.sub(r'width="[^"]*"', f'width="{width_mm:.2f}mm"', svg, count=1)
    svg = re.sub(r'height="[^"]*"', f'height="{height_mm:.2f}mm"', svg, count=1)
    return svg


def inject_style(svg: str, css: str) -> str:
    """Add a ``<style>`` element into the SVG's ``<defs>`` block.

    If no ``<defs>`` block exists, creates one after the opening ``<svg>`` tag.
    """
    style_el = f"<style type=\"text/css\">\n{css}\n</style>"

    # Try inserting into existing <defs>
    if "<defs>" in svg:
        return svg.replace("<defs>", f"<defs>\n{style_el}", 1)
    if "<defs " in svg:
        # <defs with attributes>
        m = re.search(r'(<defs[^>]*>)', svg)
        if m:
            return svg.replace(m.group(1), f"{m.group(1)}\n{style_el}", 1)

    # No defs block — insert after <svg ...>
    m = re.search(r'(<svg[^>]*>)', svg)
    if m:
        return svg.replace(
            m.group(1),
            f"{m.group(1)}\n<defs>\n{style_el}\n</defs>",
            1,
        )
    return svg
