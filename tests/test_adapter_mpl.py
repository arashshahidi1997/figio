"""Tests for the Matplotlib panel adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

mpl = pytest.importorskip("matplotlib")  # noqa: F841

from figio.adapters import PanelResult
from figio.adapters.matplotlib import MatplotlibAdapter, _strip_mpl_boilerplate
from figio.schema import Generator, PanelSpec, StyleSpec
from figio.svg_utils import normalize_viewbox as _normalize_viewbox, prefix_ids as _prefix_ids


@pytest.fixture
def adapter() -> MatplotlibAdapter:
    return MatplotlibAdapter()


@pytest.fixture
def simple_spec() -> PanelSpec:
    return PanelSpec(
        generator=Generator.matplotlib,
        source="tests/fixtures/panel_simple.py",
    )


@pytest.fixture
def style() -> StyleSpec:
    return StyleSpec(font_family="sans-serif", panel_gap_mm=3, line_weight=1.0)


@pytest.fixture
def workdir() -> Path:
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Render tests
# ---------------------------------------------------------------------------


def test_render_simple(adapter: MatplotlibAdapter, simple_spec: PanelSpec, style: StyleSpec, workdir: Path) -> None:
    result = adapter.render("panel_a", simple_spec, style, workdir)

    assert isinstance(result, PanelResult)
    assert "<svg" in result.svg
    assert result.bbox_mm[2] > 0  # width > 0
    assert result.bbox_mm[3] > 0  # height > 0


def test_render_returns_anchors(adapter: MatplotlibAdapter, simple_spec: PanelSpec, style: StyleSpec, workdir: Path) -> None:
    result = adapter.render("panel_a", simple_spec, style, workdir)
    # Should have at least one axis anchor
    assert any("center" in k for k in result.anchors)


def test_render_svg_has_prefixed_ids(adapter: MatplotlibAdapter, simple_spec: PanelSpec, style: StyleSpec, workdir: Path) -> None:
    result = adapter.render("mypanel", simple_spec, style, workdir)
    # All id= attributes should have the panel prefix
    import re
    ids = re.findall(r'id="([^"]+)"', result.svg)
    for id_val in ids:
        assert id_val.startswith("mypanel_"), f"ID {id_val!r} not prefixed"


# ---------------------------------------------------------------------------
# SVG normalization tests
# ---------------------------------------------------------------------------


def test_prefix_ids() -> None:
    svg = '<g id="axes_1"><use xlink:href="#clip1"/></g>'
    result = _prefix_ids(svg, "p1")
    assert 'id="p1_axes_1"' in result
    assert 'xlink:href="#p1_clip1"' in result


def test_normalize_viewbox() -> None:
    svg = '<svg width="300" height="200" viewBox="0 0 300 200"><rect/></svg>'
    result = _normalize_viewbox(svg, 100.0, 80.0)
    assert 'viewBox="0 0 100.00 80.00"' in result
    assert 'width="100.00mm"' in result
    assert 'height="80.00mm"' in result


def test_strip_mpl_boilerplate() -> None:
    svg = '<!-- Created with matplotlib (version 3.8.0) -->\n<svg><metadata><rdf:RDF></rdf:RDF></metadata><rect/></svg>'
    result = _strip_mpl_boilerplate(svg)
    assert "Created with matplotlib" not in result
    assert "<metadata>" not in result
    assert "<rect/>" in result


# ---------------------------------------------------------------------------
# Bounding box extraction
# ---------------------------------------------------------------------------


def test_bbox_positive(adapter: MatplotlibAdapter, simple_spec: PanelSpec, style: StyleSpec, workdir: Path) -> None:
    result = adapter.render("p", simple_spec, style, workdir)
    x, y, w, h = result.bbox_mm
    assert x == 0.0
    assert y == 0.0
    assert w > 0
    assert h > 0


# ---------------------------------------------------------------------------
# Style application
# ---------------------------------------------------------------------------


def test_style_applied(adapter: MatplotlibAdapter, style: StyleSpec, workdir: Path) -> None:
    """Style tokens should be applied during render."""
    spec = PanelSpec(
        generator=Generator.matplotlib,
        source="tests/fixtures/panel_simple.py",
    )
    custom_style = StyleSpec(
        font_family="monospace",
        font_size_pt=14.0,
        line_weight=2.5,
    )
    # Should not raise
    result = adapter.render("styled", spec, custom_style, workdir)
    assert isinstance(result, PanelResult)


# ---------------------------------------------------------------------------
# Supported constraints
# ---------------------------------------------------------------------------


def test_supported_constraints(adapter: MatplotlibAdapter) -> None:
    constraints = adapter.supported_constraints()
    assert "equal_height" in constraints
    assert "equal_width" in constraints
    assert "align_ylabels" in constraints
