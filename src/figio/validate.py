"""Validation checks against target profile constraints."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET

from pydantic import BaseModel

from figio.composer import ComposedFigure
from figio.schema import TargetProfile


class ValidationCheck(BaseModel):
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    severity: str = "warning"  # "warning" or "error"


def validate_figure(
    composed: ComposedFigure,
    target: TargetProfile,
) -> list[ValidationCheck]:
    """Run validation checks against a target profile.

    Returns a list of checks with pass/fail status.
    """
    checks: list[ValidationCheck] = []

    # Width check
    checks.append(ValidationCheck(
        name="figure_width",
        passed=abs(composed.width_mm - target.figure_width_mm) < 0.5,
        message=(
            f"Figure width {composed.width_mm:.1f}mm "
            f"{'matches' if abs(composed.width_mm - target.figure_width_mm) < 0.5 else 'does not match'} "
            f"target {target.figure_width_mm:.1f}mm"
        ),
        severity="error",
    ))

    # Max height check
    if target.max_height_mm:
        over = composed.height_mm > target.max_height_mm
        checks.append(ValidationCheck(
            name="max_height",
            passed=not over,
            message=(
                f"Figure height {composed.height_mm:.1f}mm "
                f"{'exceeds' if over else 'within'} "
                f"max {target.max_height_mm:.1f}mm"
            ),
            severity="warning",
        ))

    # Panel overflow check
    for panel_id, pos in composed.panel_positions.items():
        overflow = pos.x + pos.width > composed.width_mm + 0.1
        checks.append(ValidationCheck(
            name=f"panel_overflow_{panel_id}",
            passed=not overflow,
            message=(
                f"Panel {panel_id!r} "
                f"{'overflows' if overflow else 'fits within'} "
                f"figure width"
            ),
            severity="error" if overflow else "warning",
        ))

    # Min font size check
    checks.extend(_check_min_font_size(composed.svg, target.min_font_pt))

    # DPI check
    checks.append(_check_dpi(composed, target))

    # Colorblind check
    if target.colorblind_check:
        checks.extend(_check_colorblind(composed.svg))

    return checks


# ---------------------------------------------------------------------------
# Min font size check
# ---------------------------------------------------------------------------

_PT_PER_PX = 0.75  # CSS default: 1px = 0.75pt


def _parse_font_size_pt(value: str) -> float | None:
    """Parse a CSS font-size value and return size in points.

    Supports: ``12pt``, ``16px``, ``1.2em``, bare numbers (treated as px).
    Returns None for unsupported units (%, rem, named sizes).
    """
    value = value.strip().lower()
    if value.endswith("pt"):
        try:
            return float(value[:-2])
        except ValueError:
            return None
    if value.endswith("px"):
        try:
            return float(value[:-2]) * _PT_PER_PX
        except ValueError:
            return None
    if value.endswith("mm"):
        try:
            return float(value[:-2]) / 0.3528  # 1pt = 0.3528mm
        except ValueError:
            return None
    # bare number → px
    try:
        return float(value) * _PT_PER_PX
    except ValueError:
        return None


def _extract_font_sizes_from_svg(svg: str) -> list[float]:
    """Extract all font sizes (in pt) from an SVG string.

    Parses both inline ``font-size`` attributes and ``<style>`` CSS rules.
    Skips elements inside the ``#annotations`` group (figio-controlled, uses
    viewBox user units not pt).
    """
    sizes: list[float] = []

    # 1. Inline font-size attributes on elements
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return sizes

    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Collect annotation group element IDs to skip
    _annotation_elems: set[ET.Element] = set()
    for g in root.iter():
        if g.get("id") == "annotations":
            _annotation_elems.update(g.iter())

    for elem in root.iter():
        if elem in _annotation_elems:
            continue

        # Direct font-size attribute
        for attr_name in ("font-size", "{http://www.w3.org/2000/svg}font-size"):
            val = elem.get(attr_name)
            if val:
                pt = _parse_font_size_pt(val)
                if pt is not None:
                    sizes.append(pt)

        # font-size in style attribute
        style = elem.get("style", "")
        if "font-size" in style:
            m = re.search(r"font-size\s*:\s*([^;\"']+)", style)
            if m:
                pt = _parse_font_size_pt(m.group(1))
                if pt is not None:
                    sizes.append(pt)

    # 2. font-size in <style> blocks
    _FONT_SIZE_RULE = re.compile(r"font-size\s*:\s*([^;}\s]+)")
    for style_elem in root.iter("{http://www.w3.org/2000/svg}style"):
        text = style_elem.text or ""
        for m in _FONT_SIZE_RULE.finditer(text):
            pt = _parse_font_size_pt(m.group(1))
            if pt is not None:
                sizes.append(pt)

    return sizes


def _check_min_font_size(
    svg: str, min_font_pt: float,
) -> list[ValidationCheck]:
    """Check that all font sizes in the SVG meet the minimum."""
    sizes = _extract_font_sizes_from_svg(svg)
    if not sizes:
        return [ValidationCheck(
            name="min_font_size",
            passed=True,
            message=f"No font-size declarations found; min is {min_font_pt}pt",
        )]
    smallest = min(sizes)
    passed = smallest >= min_font_pt
    return [ValidationCheck(
        name="min_font_size",
        passed=passed,
        message=(
            f"Smallest font {smallest:.1f}pt "
            f"{'meets' if passed else 'below'} "
            f"minimum {min_font_pt:.1f}pt"
        ),
        severity="error" if not passed else "warning",
    )]


# ---------------------------------------------------------------------------
# DPI / dimension check
# ---------------------------------------------------------------------------

def _check_dpi(
    composed: ComposedFigure, target: TargetProfile,
) -> ValidationCheck:
    """Verify expected pixel dimensions for PNG export at target DPI."""
    expected_w = target.dpi * target.figure_width_mm / 25.4
    expected_h = target.dpi * composed.height_mm / 25.4
    return ValidationCheck(
        name="dpi",
        passed=True,
        message=(
            f"Target DPI {target.dpi}: "
            f"expected PNG {expected_w:.0f}x{expected_h:.0f}px"
        ),
    )


def validate_png_dimensions(
    png_path: str,
    width_mm: float,
    height_mm: float,
    dpi: int,
    tolerance: float = 2.0,
) -> ValidationCheck:
    """Check that a PNG file has the expected pixel dimensions.

    Args:
        png_path: Path to the PNG file.
        width_mm: Expected width in mm.
        height_mm: Expected height in mm.
        dpi: Target DPI.
        tolerance: Allowed pixel deviation.

    Returns:
        A ValidationCheck with pass/fail.
    """
    expected_w = dpi * width_mm / 25.4
    expected_h = dpi * height_mm / 25.4

    try:
        actual_w, actual_h = _read_png_dimensions(png_path)
    except Exception as exc:
        return ValidationCheck(
            name="png_dimensions",
            passed=False,
            message=f"Cannot read PNG dimensions: {exc}",
            severity="error",
        )

    w_ok = abs(actual_w - expected_w) <= tolerance
    h_ok = abs(actual_h - expected_h) <= tolerance
    passed = w_ok and h_ok
    return ValidationCheck(
        name="png_dimensions",
        passed=passed,
        message=(
            f"PNG {actual_w}x{actual_h}px "
            f"{'matches' if passed else 'does not match'} "
            f"expected {expected_w:.0f}x{expected_h:.0f}px "
            f"({width_mm:.1f}mm @ {dpi}dpi)"
        ),
        severity="error" if not passed else "warning",
    )


def _read_png_dimensions(path: str) -> tuple[int, int]:
    """Read width and height from a PNG file header (IHDR chunk)."""
    import struct

    with open(path, "rb") as f:
        sig = f.read(8)
        if sig[:4] != b"\x89PNG":
            raise ValueError("Not a valid PNG file")
        # IHDR is always the first chunk
        _length = f.read(4)
        chunk_type = f.read(4)
        if chunk_type != b"IHDR":
            raise ValueError("Missing IHDR chunk")
        width = struct.unpack(">I", f.read(4))[0]
        height = struct.unpack(">I", f.read(4))[0]
    return width, height


# ---------------------------------------------------------------------------
# Colorblind safety check
# ---------------------------------------------------------------------------

# Known problematic color pairs (sRGB hex) for deuteranopia
_PROBLEMATIC_PAIRS = [
    ("#ff0000", "#00ff00"),  # pure red / pure green
    ("#ff0000", "#008000"),  # red / dark green
    ("#cc0000", "#00cc00"),
    ("#e41a1c", "#4daf4a"),  # ColorBrewer Set1 red/green
    ("#d62728", "#2ca02c"),  # Matplotlib tab10 red/green
]


def _hex_to_rgb(h: str) -> tuple[float, float, float]:
    """Convert ``#rrggbb`` or ``#rgb`` to (r, g, b) in [0, 1]."""
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: #{h}")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return r, g, b


def _srgb_to_linear(c: float) -> float:
    """sRGB gamma to linear."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _simulate_deuteranopia(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Approximate deuteranopia simulation via Vienot 1999 matrix.

    Combined sRGB → simulated-sRGB matrix for deuteranopia (from Vienot,
    Brettel, Mollon 1999, Table 2). Input/output in sRGB [0, 1].
    """
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)

    # Vienot 1999 combined RGB→simulated-RGB matrix for deuteranopia
    sr = 0.29275 * rl + 0.70725 * gl + 0.00000 * bl
    sg = 0.29275 * rl + 0.70725 * gl + 0.00000 * bl
    sb = -0.02234 * rl + 0.02234 * gl + 1.00000 * bl

    return (
        max(0.0, min(1.0, sr)),
        max(0.0, min(1.0, sg)),
        max(0.0, min(1.0, sb)),
    )


def _color_distance(c1: tuple[float, float, float], c2: tuple[float, float, float]) -> float:
    """Euclidean distance in linear RGB space, scaled to ~deltaE-like range."""
    dr = (c1[0] - c2[0]) * 255
    dg = (c1[1] - c2[1]) * 255
    db = (c1[2] - c2[2]) * 255
    return math.sqrt(dr * dr + dg * dg + db * db)


def _extract_colors_from_svg(svg: str) -> set[str]:
    """Extract hex colors from fill/stroke attributes and style rules."""
    colors: set[str] = set()
    hex_re = re.compile(r"#([0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)\b")

    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return colors

    for elem in root.iter():
        for attr in ("fill", "stroke", "stop-color", "color"):
            val = elem.get(attr, "")
            for m in hex_re.finditer(val):
                colors.add(f"#{m.group(1).lower()}")
        style = elem.get("style", "")
        for m in hex_re.finditer(style):
            colors.add(f"#{m.group(1).lower()}")

    # Also check <style> blocks
    for style_elem in root.iter("{http://www.w3.org/2000/svg}style"):
        text = style_elem.text or ""
        for m in hex_re.finditer(text):
            colors.add(f"#{m.group(1).lower()}")

    # Normalize 3-digit hex to 6-digit
    normalized: set[str] = set()
    for c in colors:
        h = c.lstrip("#")
        if len(h) == 3:
            h = h[0] * 2 + h[1] * 2 + h[2] * 2
        normalized.add(f"#{h}")
    return normalized


def _check_colorblind(svg: str) -> list[ValidationCheck]:
    """Check extracted SVG palette for colorblind-problematic pairs."""
    colors = _extract_colors_from_svg(svg)

    # Filter out near-black, near-white, and common neutral colors
    filtered: list[str] = []
    for c in colors:
        try:
            r, g, b = _hex_to_rgb(c)
        except ValueError:
            continue
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if 0.05 < luminance < 0.95:
            filtered.append(c)

    if not filtered:
        return [ValidationCheck(
            name="colorblind_safety",
            passed=True,
            message="No chromatic colors found to check",
        )]

    # Check all pairs via deuteranopia simulation
    issues: list[str] = []
    checked = list(filtered)
    for i in range(len(checked)):
        for j in range(i + 1, len(checked)):
            try:
                r1, g1, b1 = _hex_to_rgb(checked[i])
                r2, g2, b2 = _hex_to_rgb(checked[j])
            except ValueError:
                continue

            # Original distance
            orig_dist = _color_distance((r1, g1, b1), (r2, g2, b2))
            if orig_dist < 10:
                continue  # already similar, not a new issue

            # Simulated distance
            sim1 = _simulate_deuteranopia(r1, g1, b1)
            sim2 = _simulate_deuteranopia(r2, g2, b2)
            sim_dist = _color_distance(sim1, sim2)

            # Flag if simulated distance drops below threshold OR
            # the ratio of simulated/original distance is very small
            # (colors that were distinct become much more similar)
            ratio = sim_dist / orig_dist if orig_dist > 0 else 1.0
            if sim_dist < 5 or (ratio < 0.15 and orig_dist > 50):
                issues.append(f"{checked[i]} and {checked[j]}")

    if issues:
        pairs_str = "; ".join(issues[:5])
        extra = f" (+{len(issues) - 5} more)" if len(issues) > 5 else ""
        return [ValidationCheck(
            name="colorblind_safety",
            passed=False,
            message=f"Potentially confusable under deuteranopia: {pairs_str}{extra}",
            severity="warning",
        )]

    return [ValidationCheck(
        name="colorblind_safety",
        passed=True,
        message=f"Checked {len(filtered)} colors — no deuteranopia conflicts detected",
    )]
