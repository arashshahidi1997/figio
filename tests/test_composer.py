"""Tests for the SVG composer."""

from __future__ import annotations

import pytest

from figio.adapters import PanelResult
from figio.composer import BBox, ComposedFigure, compose
from figio.schema import (
    AnnotationSpec,
    AnnotationType,
    ConstraintType,
    LayoutConstraint,
    LayoutSpec,
    LayoutType,
    StyleSpec,
    TargetProfile,
)


# ---------------------------------------------------------------------------
# Fixtures — synthetic PanelResult with minimal SVG
# ---------------------------------------------------------------------------


def _make_panel(width_mm: float = 40.0, height_mm: float = 30.0, panel_id: str = "p") -> PanelResult:
    """Create a synthetic PanelResult with a minimal SVG fragment."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_mm}mm" height="{height_mm}mm" '
        f'viewBox="0 0 {width_mm} {height_mm}">'
        f'<defs><clipPath id="{panel_id}_clip"><rect width="{width_mm}" height="{height_mm}"/></clipPath></defs>'
        f'<rect id="{panel_id}_bg" width="{width_mm}" height="{height_mm}" fill="#eee"/>'
        f'<text x="5" y="15">Panel {panel_id}</text>'
        f'</svg>'
    )
    return PanelResult(
        svg=svg,
        bbox_mm=(0.0, 0.0, width_mm, height_mm),
        anchors={f"{panel_id}_center": (width_mm / 2, height_mm / 2)},
        semantic_ids=[f"{panel_id}_bg"],
    )


@pytest.fixture
def style() -> StyleSpec:
    return StyleSpec(font_family="Helvetica", panel_gap_mm=4.0)


@pytest.fixture
def target() -> TargetProfile:
    return TargetProfile(name="test", figure_width_mm=100.0, min_font_pt=6.0, dpi=150)


# ---------------------------------------------------------------------------
# Grid layout tests
# ---------------------------------------------------------------------------


def test_two_panels_one_row(style: StyleSpec, target: TargetProfile) -> None:
    """2 panels in 1×2 grid: verify positions and dimensions."""
    panels = {
        "a": _make_panel(40, 30, "a"),
        "b": _make_panel(40, 30, "b"),
    }
    layout = LayoutSpec(type=LayoutType.grid, rows=1, cols=2)

    result = compose(panels, layout, [], style, target)

    assert isinstance(result, ComposedFigure)
    assert "<svg" in result.svg
    assert result.width_mm == 100.0

    # Both panels should be positioned
    assert "a" in result.panel_positions
    assert "b" in result.panel_positions

    pos_a = result.panel_positions["a"]
    pos_b = result.panel_positions["b"]

    # Panel A starts at x=0
    assert pos_a.x == 0.0
    # Panel B starts after A + gap
    assert pos_b.x == pytest.approx(pos_a.width + style.panel_gap_mm, abs=0.1)
    # Both at same y
    assert pos_a.y == pos_b.y == 0.0


def test_four_panels_2x2(style: StyleSpec, target: TargetProfile) -> None:
    """4 panels in 2×2 grid: verify layout."""
    panels = {
        "a": _make_panel(40, 30, "a"),
        "b": _make_panel(40, 30, "b"),
        "c": _make_panel(40, 30, "c"),
        "d": _make_panel(40, 30, "d"),
    }
    layout = LayoutSpec(type=LayoutType.grid, rows=2, cols=2)

    result = compose(panels, layout, [], style, target)

    assert len(result.panel_positions) == 4

    # Row 1
    assert result.panel_positions["a"].y == 0.0
    assert result.panel_positions["b"].y == 0.0
    # Row 2 below row 1
    assert result.panel_positions["c"].y > 0.0
    assert result.panel_positions["d"].y > 0.0
    assert result.panel_positions["c"].y == result.panel_positions["d"].y


# ---------------------------------------------------------------------------
# Constraint tests
# ---------------------------------------------------------------------------


def test_equal_height_constraint(style: StyleSpec, target: TargetProfile) -> None:
    """Panels with different heights get equalized."""
    panels = {
        "tall": _make_panel(40, 60, "tall"),
        "short": _make_panel(40, 20, "short"),
    }
    layout = LayoutSpec(
        type=LayoutType.grid,
        rows=1,
        cols=2,
        constraints=[
            LayoutConstraint(type=ConstraintType.equal_height, panels=["tall", "short"])
        ],
    )

    result = compose(panels, layout, [], style, target)

    # Both panels should have the same height (the taller one)
    h_tall = result.panel_positions["tall"].height
    h_short = result.panel_positions["short"].height
    assert h_tall == pytest.approx(h_short, abs=0.01)


# ---------------------------------------------------------------------------
# Annotation tests
# ---------------------------------------------------------------------------


def test_panel_labels(style: StyleSpec, target: TargetProfile) -> None:
    """Panel label annotations appear in the SVG."""
    panels = {"a": _make_panel(40, 30, "a"), "b": _make_panel(40, 30, "b")}
    layout = LayoutSpec(type=LayoutType.grid, rows=1, cols=2)
    annotations = [
        AnnotationSpec(type=AnnotationType.panel_label, target="a", text="A"),
        AnnotationSpec(type=AnnotationType.panel_label, target="b", text="B"),
    ]

    result = compose(panels, layout, annotations, style, target)

    assert ">A</text>" in result.svg
    assert ">B</text>" in result.svg
    assert 'id="annotations"' in result.svg


# ---------------------------------------------------------------------------
# Warning tests
# ---------------------------------------------------------------------------


def test_max_height_warning(style: StyleSpec) -> None:
    """Figure exceeding max_height triggers a warning."""
    target = TargetProfile(
        name="tight",
        figure_width_mm=100.0,
        min_font_pt=6.0,
        dpi=150,
        max_height_mm=10.0,  # Very tight constraint
    )
    panels = {"a": _make_panel(40, 30, "a")}
    layout = LayoutSpec(type=LayoutType.grid, rows=1, cols=1)

    result = compose(panels, layout, [], style, target)

    assert any("exceeds target max" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Defs merging
# ---------------------------------------------------------------------------


def test_defs_merging(style: StyleSpec, target: TargetProfile) -> None:
    """Two panels with <defs> produce a single merged defs block."""
    panels = {
        "a": _make_panel(40, 30, "a"),
        "b": _make_panel(40, 30, "b"),
    }
    layout = LayoutSpec(type=LayoutType.grid, rows=1, cols=2)

    result = compose(panels, layout, [], style, target)

    # Should have defs content from both panels
    assert "<defs>" in result.svg
    assert "a_clip" in result.svg
    assert "b_clip" in result.svg


# ---------------------------------------------------------------------------
# SVG document structure
# ---------------------------------------------------------------------------


def test_svg_document_structure(style: StyleSpec, target: TargetProfile) -> None:
    """Composed SVG is a well-formed document with viewBox."""
    panels = {"a": _make_panel(40, 30, "a")}
    layout = LayoutSpec(type=LayoutType.grid, rows=1, cols=1)

    result = compose(panels, layout, [], style, target)

    assert result.svg.startswith("<?xml")
    assert 'viewBox="0 0' in result.svg
    assert 'id="panel-a"' in result.svg
    assert "font-family" in result.svg


def test_empty_panels(style: StyleSpec, target: TargetProfile) -> None:
    """Composing with no panels produces valid but empty SVG."""
    result = compose({}, LayoutSpec(), [], style, target)
    assert "<svg" in result.svg
    assert result.height_mm == 0.0
