"""Integration tests — end-to-end build/validate/export with realistic figure patterns."""

from __future__ import annotations

import struct
import textwrap
from pathlib import Path

import pytest
import yaml

from figio.build import build
from figio.schema import FigureSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_panel_script(path: Path, *, width_in: float = 3.0, height_in: float = 2.0) -> None:
    """Write a minimal matplotlib panel script that draws a rectangle."""
    path.write_text(textwrap.dedent(f"""\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        def make_figure():
            fig, ax = plt.subplots(figsize=({width_in}, {height_in}))
            ax.add_patch(patches.Rectangle((0.1, 0.1), 0.8, 0.8, fill=False))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            return fig
    """))


def _write_spec(path: Path, spec_dict: dict) -> None:
    """Write a FigureSpec YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        yaml.safe_dump({"figure": spec_dict}, fh, sort_keys=False)


def _has_cairosvg() -> bool:
    try:
        import cairosvg  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# 1. Single-panel nature figure
# ---------------------------------------------------------------------------

def test_single_panel_nature(tmp_path: Path):
    """Single matplotlib panel, nature_single_column target, panel label."""
    _write_panel_script(tmp_path / "panel_a.py")
    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig1",
        "target": "nature_single_column",
        "panels": {
            "a": {"generator": "matplotlib", "source": "panel_a.py"},
        },
        "layout": {"type": "grid", "rows": 1, "cols": 1},
        "annotations": [
            {"type": "panel_label", "target": "a", "text": "A"},
        ],
    })

    result = build(tmp_path / "fig.yaml")

    # SVG was produced
    assert Path(result.output_svg).exists()
    svg = Path(result.output_svg).read_text()

    # Width matches nature_single_column = 89mm
    assert result.composed is not None
    assert abs(result.composed.width_mm - 89.0) < 0.5

    # Panel label present
    assert ">A</text>" in svg

    # Width check passes in validation
    width_checks = [c for c in result.validation if c.name == "figure_width"]
    assert width_checks and width_checks[0].passed


# ---------------------------------------------------------------------------
# 2. Two-panel comparison (1x2 grid)
# ---------------------------------------------------------------------------

def test_two_panel_comparison(tmp_path: Path):
    """Side-by-side panels, equal_height constraint, panel labels A/B, caption."""
    _write_panel_script(tmp_path / "left.py", width_in=3.0, height_in=2.0)
    _write_panel_script(tmp_path / "right.py", width_in=3.0, height_in=3.0)
    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig2",
        "target": "default",
        "panels": {
            "left": {"generator": "matplotlib", "source": "left.py"},
            "right": {"generator": "matplotlib", "source": "right.py"},
        },
        "layout": {
            "type": "grid", "rows": 1, "cols": 2,
            "constraints": [{"equal_height": ["left", "right"]}],
        },
        "annotations": [
            {"type": "panel_label", "target": "left", "text": "A"},
            {"type": "panel_label", "target": "right", "text": "B"},
            {"type": "caption", "text": "Figure 2. A comparison."},
        ],
    })

    result = build(tmp_path / "fig.yaml")
    svg = Path(result.output_svg).read_text()

    # Both panels in composed SVG
    assert 'id="panel-left"' in svg
    assert 'id="panel-right"' in svg

    # Equal-height constraint: both panels should have same height
    pos = result.composed.panel_positions
    assert abs(pos["left"].height - pos["right"].height) < 0.01

    # Labels present
    assert ">A</text>" in svg
    assert ">B</text>" in svg


# ---------------------------------------------------------------------------
# 3. Four-panel grid (2x2)
# ---------------------------------------------------------------------------

def test_four_panel_grid(tmp_path: Path):
    """2x2 grid with per-row equal_height, nature_double_column target."""
    for name in ("a", "b", "c", "d"):
        _write_panel_script(tmp_path / f"panel_{name}.py")

    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig3",
        "target": "nature_double_column",
        "panels": {
            "a": {"generator": "matplotlib", "source": "panel_a.py"},
            "b": {"generator": "matplotlib", "source": "panel_b.py"},
            "c": {"generator": "matplotlib", "source": "panel_c.py"},
            "d": {"generator": "matplotlib", "source": "panel_d.py"},
        },
        "layout": {
            "type": "grid", "rows": 2, "cols": 2,
            "constraints": [
                {"equal_height": ["a", "b"]},
                {"equal_height": ["c", "d"]},
            ],
        },
        "annotations": [
            {"type": "panel_label", "target": "a", "text": "A"},
            {"type": "panel_label", "target": "b", "text": "B"},
            {"type": "panel_label", "target": "c", "text": "C"},
            {"type": "panel_label", "target": "d", "text": "D"},
        ],
    })

    result = build(tmp_path / "fig.yaml")
    svg = Path(result.output_svg).read_text()

    # All four panels present
    for pid in ("a", "b", "c", "d"):
        assert f'id="panel-{pid}"' in svg

    # 4 distinct positions
    pos = result.composed.panel_positions
    panel_pos = {k: v for k, v in pos.items() if not k.startswith("__")}
    assert len(panel_pos) == 4

    # Width = nature_double_column = 183mm
    assert abs(result.composed.width_mm - 183.0) < 0.5


# ---------------------------------------------------------------------------
# 4. Cache roundtrip
# ---------------------------------------------------------------------------

def test_cache_roundtrip(tmp_path: Path):
    """Build, modify one panel, rebuild — only changed panel re-renders."""
    _write_panel_script(tmp_path / "p1.py")
    _write_panel_script(tmp_path / "p2.py")
    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig_cache",
        "target": "default",
        "panels": {
            "p1": {"generator": "matplotlib", "source": "p1.py"},
            "p2": {"generator": "matplotlib", "source": "p2.py"},
        },
        "layout": {"type": "grid", "rows": 1, "cols": 2},
    })

    # First build — nothing cached
    r1 = build(tmp_path / "fig.yaml")
    assert r1.cached_panels == []

    # Second build (no changes) — both panels cached
    r2 = build(tmp_path / "fig.yaml")
    assert sorted(r2.cached_panels) == ["p1", "p2"]

    # Modify p1 source
    _write_panel_script(tmp_path / "p1.py", width_in=4.0, height_in=2.5)

    # Third build — only p2 should be cached, p1 re-rendered
    r3 = build(tmp_path / "fig.yaml")
    assert "p2" in r3.cached_panels
    assert "p1" not in r3.cached_panels

    # Force build — nothing cached
    r4 = build(tmp_path / "fig.yaml", force=True)
    assert r4.cached_panels == []


# ---------------------------------------------------------------------------
# 5. Export formats (requires cairosvg)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _has_cairosvg(), reason="cairosvg not installed")
def test_export_formats(tmp_path: Path):
    """Build with svg, pdf, png — all files exist with non-zero size."""
    _write_panel_script(tmp_path / "panel.py")
    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig_export",
        "target": "default",
        "panels": {
            "main": {"generator": "matplotlib", "source": "panel.py"},
        },
        "layout": {"type": "grid", "rows": 1, "cols": 1},
    })

    result = build(tmp_path / "fig.yaml", formats=["svg", "pdf", "png"])

    svg_path = Path(result.output_svg)
    assert svg_path.exists() and svg_path.stat().st_size > 0

    assert result.output_pdf is not None
    pdf_path = Path(result.output_pdf)
    assert pdf_path.exists() and pdf_path.stat().st_size > 0

    assert result.output_png is not None
    png_path = Path(result.output_png)
    assert png_path.exists() and png_path.stat().st_size > 0

    # PNG dimensions should be roughly correct for DPI=150, 170mm width
    # 170mm / 25.4 * 150 = ~1004 px
    w, h = _read_png_dims(png_path)
    expected_w = int(150 * 170.0 / 25.4)
    assert abs(w - expected_w) < 20  # generous tolerance


# ---------------------------------------------------------------------------
# 6. Validation failure — panel overflow
# ---------------------------------------------------------------------------

def test_validation_overflow(tmp_path: Path):
    """Create a spec where layout would produce overflow warnings."""
    # Use a very wide panel in a narrow target
    _write_panel_script(tmp_path / "wide.py", width_in=8.0, height_in=2.0)
    _write_panel_script(tmp_path / "extra.py", width_in=8.0, height_in=2.0)

    # Force 1x1 layout but place two panels — the second won't be positioned,
    # but we can test max_height overflow instead.
    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig_overflow",
        "target": {
            "name": "narrow",
            "figure_width_mm": 60.0,
            "min_font_pt": 6.0,
            "dpi": 150,
            "max_height_mm": 10.0,  # very short — figure will exceed this
        },
        "panels": {
            "wide": {"generator": "matplotlib", "source": "wide.py"},
        },
        "layout": {"type": "grid", "rows": 1, "cols": 1},
    })

    result = build(tmp_path / "fig.yaml")

    # Max height should be violated (panel aspect will make height > 10mm)
    height_checks = [c for c in result.validation if c.name == "max_height"]
    assert height_checks and not height_checks[0].passed


# ---------------------------------------------------------------------------
# 7. Data dependencies — input file invalidates cache
# ---------------------------------------------------------------------------

def test_data_dependency_cache(tmp_path: Path):
    """Panel with inputs: [data.csv]. Changing data invalidates cache."""
    data_file = tmp_path / "data.csv"
    data_file.write_text("x,y\n1,2\n3,4\n")

    # Panel script that references data but doesn't actually read it in make_figure
    (tmp_path / "panel_data.py").write_text(textwrap.dedent("""\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        def make_figure():
            fig, ax = plt.subplots(figsize=(3, 2))
            ax.plot([1, 2, 3], [1, 4, 9])
            return fig
    """))

    _write_spec(tmp_path / "fig.yaml", {
        "id": "fig_data",
        "target": "default",
        "panels": {
            "dp": {
                "generator": "matplotlib",
                "source": "panel_data.py",
                "inputs": ["data.csv"],
            },
        },
        "layout": {"type": "grid", "rows": 1, "cols": 1},
    })

    # First build
    r1 = build(tmp_path / "fig.yaml")
    assert r1.cached_panels == []

    # Second build, no changes — cached
    r2 = build(tmp_path / "fig.yaml")
    assert "dp" in r2.cached_panels

    # Modify data file
    data_file.write_text("x,y\n1,2\n3,4\n5,6\n")

    # Third build — cache invalidated
    r3 = build(tmp_path / "fig.yaml")
    assert "dp" not in r3.cached_panels


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _read_png_dims(path: Path) -> tuple[int, int]:
    """Read width/height from PNG IHDR chunk."""
    with open(path, "rb") as f:
        f.read(8)  # signature
        f.read(4)  # length
        f.read(4)  # chunk type
        w = struct.unpack(">I", f.read(4))[0]
        h = struct.unpack(">I", f.read(4))[0]
    return w, h
