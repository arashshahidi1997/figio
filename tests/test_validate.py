"""Tests for figio.validate — font size, DPI, and colorblind checks."""

from __future__ import annotations

import struct
import tempfile
from dataclasses import dataclass, field

import pytest

from figio.validate import (
    ValidationCheck,
    _check_colorblind,
    _check_min_font_size,
    _extract_colors_from_svg,
    _extract_font_sizes_from_svg,
    _parse_font_size_pt,
    validate_figure,
    validate_png_dimensions,
)
from figio.composer import BBox, ComposedFigure
from figio.schema import TargetProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_composed(svg: str, width_mm: float = 170.0, height_mm: float = 100.0) -> ComposedFigure:
    return ComposedFigure(
        svg=svg,
        width_mm=width_mm,
        height_mm=height_mm,
        panel_positions={},
    )


def _minimal_svg(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        f"{body}</svg>"
    )


def _write_fake_png(path: str, width: int, height: int) -> None:
    """Write a minimal valid PNG with the given dimensions."""
    with open(path, "wb") as f:
        # PNG signature
        f.write(b"\x89PNG\r\n\x1a\n")
        # IHDR chunk: length(13) + "IHDR" + width(4) + height(4) + ...
        ihdr_data = struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"
        f.write(struct.pack(">I", 13))  # chunk data length
        f.write(b"IHDR")
        f.write(ihdr_data)
        # CRC (not checked by our reader)
        f.write(b"\x00\x00\x00\x00")


# ---------------------------------------------------------------------------
# Font size parsing
# ---------------------------------------------------------------------------

class TestParseFontSize:
    def test_pt(self):
        assert _parse_font_size_pt("12pt") == 12.0

    def test_px(self):
        assert _parse_font_size_pt("16px") == pytest.approx(12.0)

    def test_bare_number(self):
        assert _parse_font_size_pt("10") == pytest.approx(7.5)

    def test_unsupported_unit(self):
        assert _parse_font_size_pt("1.5em") is None

    def test_whitespace(self):
        assert _parse_font_size_pt("  8pt ") == 8.0


# ---------------------------------------------------------------------------
# Font size extraction from SVG
# ---------------------------------------------------------------------------

class TestExtractFontSizes:
    def test_inline_attribute(self):
        svg = _minimal_svg('<text font-size="10pt">hello</text>')
        sizes = _extract_font_sizes_from_svg(svg)
        assert 10.0 in sizes

    def test_style_attribute(self):
        svg = _minimal_svg('<text style="font-size: 8pt; fill: red">hello</text>')
        sizes = _extract_font_sizes_from_svg(svg)
        assert 8.0 in sizes

    def test_style_block(self):
        svg = _minimal_svg(
            '<style>text { font-size: 6pt; }</style>'
            '<text>hello</text>'
        )
        sizes = _extract_font_sizes_from_svg(svg)
        assert 6.0 in sizes

    def test_mixed_units(self):
        svg = _minimal_svg(
            '<text font-size="12pt">a</text>'
            '<text font-size="16px">b</text>'
        )
        sizes = _extract_font_sizes_from_svg(svg)
        assert 12.0 in sizes
        assert pytest.approx(12.0) in sizes  # 16px = 12pt


# ---------------------------------------------------------------------------
# Min font size check
# ---------------------------------------------------------------------------

class TestMinFontSizeCheck:
    def test_pass(self):
        svg = _minimal_svg('<text font-size="10pt">ok</text>')
        checks = _check_min_font_size(svg, 6.0)
        assert len(checks) == 1
        assert checks[0].passed is True

    def test_fail(self):
        svg = _minimal_svg('<text font-size="4pt">too small</text>')
        checks = _check_min_font_size(svg, 6.0)
        assert len(checks) == 1
        assert checks[0].passed is False
        assert "4.0pt" in checks[0].message
        assert checks[0].severity == "error"

    def test_no_fonts(self):
        svg = _minimal_svg('<rect width="10" height="10"/>')
        checks = _check_min_font_size(svg, 6.0)
        assert checks[0].passed is True


# ---------------------------------------------------------------------------
# DPI / PNG dimension check
# ---------------------------------------------------------------------------

class TestDPICheck:
    def test_correct_dimensions(self):
        # 170mm @ 300dpi = 170 * 300 / 25.4 ≈ 2008
        expected_w = round(300 * 170 / 25.4)
        expected_h = round(300 * 100 / 25.4)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            _write_fake_png(f.name, expected_w, expected_h)
            check = validate_png_dimensions(f.name, 170.0, 100.0, 300)
        assert check.passed is True

    def test_wrong_dimensions(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            _write_fake_png(f.name, 100, 100)
            check = validate_png_dimensions(f.name, 170.0, 100.0, 300)
        assert check.passed is False

    def test_missing_file(self):
        check = validate_png_dimensions("/nonexistent.png", 170.0, 100.0, 300)
        assert check.passed is False

    def test_expected_pixels(self):
        # 85mm @ 150dpi = 85 * 150 / 25.4 ≈ 502
        expected_w = round(150 * 85 / 25.4)
        expected_h = round(150 * 60 / 25.4)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            _write_fake_png(f.name, expected_w, expected_h)
            check = validate_png_dimensions(f.name, 85.0, 60.0, 150)
        assert check.passed is True


# ---------------------------------------------------------------------------
# Color extraction
# ---------------------------------------------------------------------------

class TestExtractColors:
    def test_fill_stroke(self):
        svg = _minimal_svg('<rect fill="#ff0000" stroke="#00ff00"/>')
        colors = _extract_colors_from_svg(svg)
        assert "#ff0000" in colors
        assert "#00ff00" in colors

    def test_style_attribute(self):
        svg = _minimal_svg('<rect style="fill: #0000ff; stroke: #aabbcc"/>')
        colors = _extract_colors_from_svg(svg)
        assert "#0000ff" in colors
        assert "#aabbcc" in colors

    def test_shorthand_hex(self):
        svg = _minimal_svg('<rect fill="#f00"/>')
        colors = _extract_colors_from_svg(svg)
        assert "#ff0000" in colors


# ---------------------------------------------------------------------------
# Colorblind check
# ---------------------------------------------------------------------------

class TestColorblindCheck:
    def test_red_green_fail(self):
        # Use matplotlib tab10 red/green — a realistic confusable pair
        svg = _minimal_svg(
            '<rect fill="#d62728" width="10" height="10"/>'
            '<rect fill="#2ca02c" width="10" height="10"/>'
        )
        checks = _check_colorblind(svg)
        assert len(checks) == 1
        assert checks[0].passed is False
        assert "deuteranopia" in checks[0].message.lower()

    def test_blue_orange_pass(self):
        svg = _minimal_svg(
            '<rect fill="#0000ff" width="10" height="10"/>'
            '<rect fill="#ff8800" width="10" height="10"/>'
        )
        checks = _check_colorblind(svg)
        assert len(checks) == 1
        assert checks[0].passed is True

    def test_no_colors(self):
        svg = _minimal_svg('<rect width="10" height="10"/>')
        checks = _check_colorblind(svg)
        assert checks[0].passed is True


# ---------------------------------------------------------------------------
# Integration: validate_figure with new checks
# ---------------------------------------------------------------------------

class TestValidateFigureIntegration:
    def test_includes_font_check(self):
        svg = _minimal_svg('<text font-size="4pt">tiny</text>')
        composed = _make_composed(svg)
        target = TargetProfile(min_font_pt=6.0)
        checks = validate_figure(composed, target)
        names = [c.name for c in checks]
        assert "min_font_size" in names
        font_check = next(c for c in checks if c.name == "min_font_size")
        assert font_check.passed is False

    def test_colorblind_off_by_default(self):
        svg = _minimal_svg('<rect fill="#ff0000"/><rect fill="#00ff00"/>')
        composed = _make_composed(svg)
        target = TargetProfile(colorblind_check=False)
        checks = validate_figure(composed, target)
        names = [c.name for c in checks]
        assert "colorblind_safety" not in names

    def test_colorblind_on(self):
        svg = _minimal_svg('<rect fill="#ff0000"/><rect fill="#00ff00"/>')
        composed = _make_composed(svg)
        target = TargetProfile(colorblind_check=True)
        checks = validate_figure(composed, target)
        names = [c.name for c in checks]
        assert "colorblind_safety" in names
