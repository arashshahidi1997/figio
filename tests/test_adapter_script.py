"""Tests for the Script panel adapter."""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import pytest

from figio.adapters import PanelResult
from figio.adapters.script import ScriptAdapter, _extract_bbox_mm, _parse_svg_dimension
from figio.schema import Generator, PanelSpec, StyleSpec


FIXTURE_SCRIPT = "tests/fixtures/panel_script_rect.py"


@pytest.fixture
def adapter() -> ScriptAdapter:
    return ScriptAdapter()


@pytest.fixture
def script_spec() -> PanelSpec:
    return PanelSpec(
        generator=Generator.script,
        source=FIXTURE_SCRIPT,
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


def test_render_returns_panel_result(
    adapter: ScriptAdapter,
    script_spec: PanelSpec,
    style: StyleSpec,
    workdir: Path,
) -> None:
    result = adapter.render("script_panel", script_spec, style, workdir)
    assert isinstance(result, PanelResult)


def test_render_produces_valid_svg(
    adapter: ScriptAdapter,
    script_spec: PanelSpec,
    style: StyleSpec,
    workdir: Path,
) -> None:
    result = adapter.render("script_panel", script_spec, style, workdir)
    assert "<svg" in result.svg
    assert "</svg>" in result.svg


def test_render_bbox_positive(
    adapter: ScriptAdapter,
    script_spec: PanelSpec,
    style: StyleSpec,
    workdir: Path,
) -> None:
    result = adapter.render("script_panel", script_spec, style, workdir)
    x, y, w, h = result.bbox_mm
    assert x == 0.0
    assert y == 0.0
    assert w > 0
    assert h > 0


def test_render_svg_has_prefixed_ids(
    adapter: ScriptAdapter,
    script_spec: PanelSpec,
    style: StyleSpec,
    workdir: Path,
) -> None:
    result = adapter.render("myscript", script_spec, style, workdir)
    ids = re.findall(r'id="([^"]+)"', result.svg)
    assert ids, "SVG should contain at least one id= attribute"
    for id_val in ids:
        assert id_val.startswith("myscript_"), f"ID {id_val!r} not prefixed"


def test_render_stores_original_viewbox(
    adapter: ScriptAdapter,
    script_spec: PanelSpec,
    style: StyleSpec,
    workdir: Path,
) -> None:
    result = adapter.render("vb", script_spec, style, workdir)
    # The fixture script writes a viewBox; it should be captured
    assert result.viewbox is not None
    assert len(result.viewbox) == 4


# ---------------------------------------------------------------------------
# Supported constraints
# ---------------------------------------------------------------------------


def test_supported_constraints(adapter: ScriptAdapter) -> None:
    constraints = adapter.supported_constraints()
    assert "equal_height" in constraints
    assert "equal_width" in constraints


# ---------------------------------------------------------------------------
# Dimension parsing helpers
# ---------------------------------------------------------------------------


def test_parse_svg_dimension_mm() -> None:
    svg = '<svg width="80mm" height="60mm"/>'
    assert _parse_svg_dimension(svg, "width") == pytest.approx(80.0)
    assert _parse_svg_dimension(svg, "height") == pytest.approx(60.0)


def test_parse_svg_dimension_px() -> None:
    svg = '<svg width="96px" height="96px"/>'
    val = _parse_svg_dimension(svg, "width")
    assert val == pytest.approx(25.4)  # 96px × (25.4/96) mm


def test_parse_svg_dimension_pt() -> None:
    svg = '<svg width="72pt"/>'
    val = _parse_svg_dimension(svg, "width")
    assert val == pytest.approx(25.4)  # 72pt × (25.4/72) mm


def test_parse_svg_dimension_unitless() -> None:
    svg = '<svg width="96"/>'
    val = _parse_svg_dimension(svg, "width")
    assert val == pytest.approx(25.4)  # treated as px


def test_parse_svg_dimension_missing() -> None:
    svg = '<svg/>'
    assert _parse_svg_dimension(svg, "width") is None


def test_extract_bbox_mm_from_mm_attrs() -> None:
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="80mm" height="60mm" viewBox="0 0 80 60"/>'
    x, y, w, h = _extract_bbox_mm(svg)
    assert x == 0.0
    assert y == 0.0
    assert w == pytest.approx(80.0)
    assert h == pytest.approx(60.0)


def test_extract_bbox_mm_falls_back_to_viewbox() -> None:
    # No width/height, only viewBox — treated as px
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 72"/>'
    x, y, w, h = _extract_bbox_mm(svg)
    assert w == pytest.approx(25.4)   # 96px
    assert h == pytest.approx(19.05)  # 72px


def test_extract_bbox_mm_fallback_defaults() -> None:
    svg = '<svg xmlns="http://www.w3.org/2000/svg"/>'
    x, y, w, h = _extract_bbox_mm(svg)
    assert w > 0
    assert h > 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_render_raises_on_missing_script(
    adapter: ScriptAdapter,
    style: StyleSpec,
    workdir: Path,
) -> None:
    spec = PanelSpec(generator=Generator.script, source="nonexistent_script.py")
    with pytest.raises(Exception):
        adapter.render("p", spec, style, workdir)


def test_render_raises_when_script_fails(
    adapter: ScriptAdapter,
    style: StyleSpec,
    workdir: Path,
    tmp_path: Path,
) -> None:
    # Write a script that exits with non-zero status
    bad_script = tmp_path / "bad_panel.py"
    bad_script.write_text(
        textwrap.dedent("""\
            import sys
            sys.exit(1)
        """)
    )
    # Use absolute path — workdir / absolute resolves to the absolute path
    spec = PanelSpec(
        generator=Generator.script,
        source=str(bad_script),
    )
    with pytest.raises(RuntimeError, match="failed"):
        adapter.render("p", spec, style, workdir)


# ---------------------------------------------------------------------------
# Integration: build pipeline with generator: script
# ---------------------------------------------------------------------------


def test_build_pipeline_with_script_generator(tmp_path: Path, workdir: Path) -> None:
    """End-to-end: build a figure that uses generator: script."""
    import yaml
    from figio.build import build

    # Copy the fixture script into tmp_path so spec paths align
    fixture = workdir / FIXTURE_SCRIPT
    panel_script = tmp_path / "panel_rect.py"
    panel_script.write_text(fixture.read_text())

    spec_data = {
        "figure": {
            "id": "test_script_fig",
            "panels": {
                "rect": {
                    "generator": "script",
                    "source": "panel_rect.py",
                }
            },
            "layout": {"rows": 1, "cols": 1},
        }
    }
    spec_path = tmp_path / "figurespec.yaml"
    spec_path.write_text(yaml.safe_dump(spec_data))

    result = build(spec_path, output_dir=tmp_path / "_build")
    assert (tmp_path / "_build" / "test_script_fig.svg").exists()
    assert "rect" in result.panel_results
