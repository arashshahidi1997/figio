"""Tests for the build engine, caching, validation, and CLI."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from figio.build import build, BuildResult
from figio.cache import check_cache, compute_hash, update_cache
from figio.validate import ValidationCheck, validate_figure
from figio.composer import ComposedFigure, BBox


# ---------------------------------------------------------------------------
# Cache tests
# ---------------------------------------------------------------------------


def test_compute_hash_deterministic(tmp_path: Path) -> None:
    f = tmp_path / "a.py"
    f.write_text("hello")
    h1 = compute_hash([f])
    h2 = compute_hash([f])
    assert h1 == h2


def test_compute_hash_changes_with_content(tmp_path: Path) -> None:
    f = tmp_path / "a.py"
    f.write_text("hello")
    h1 = compute_hash([f])
    f.write_text("world")
    h2 = compute_hash([f])
    assert h1 != h2


def test_compute_hash_with_extra(tmp_path: Path) -> None:
    f = tmp_path / "a.py"
    f.write_text("hello")
    h1 = compute_hash([f], extra="style1")
    h2 = compute_hash([f], extra="style2")
    assert h1 != h2


def test_cache_miss_then_hit(tmp_path: Path) -> None:
    cache_dir = tmp_path / ".cache"
    assert not check_cache(cache_dir, "panel_a", "abc123")
    update_cache(cache_dir, "panel_a", "abc123")
    assert check_cache(cache_dir, "panel_a", "abc123")


def test_cache_invalidated(tmp_path: Path) -> None:
    cache_dir = tmp_path / ".cache"
    update_cache(cache_dir, "panel_a", "abc123")
    assert not check_cache(cache_dir, "panel_a", "xyz789")


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_validate_width_match() -> None:
    composed = ComposedFigure(
        svg="<svg/>", width_mm=89.0, height_mm=50.0,
        panel_positions={"a": BBox(x=0, y=0, width=89, height=50)},
    )
    from figio.schema import TargetProfile
    target = TargetProfile(figure_width_mm=89.0, min_font_pt=5.0, dpi=300)
    checks = validate_figure(composed, target)
    width_check = next(c for c in checks if c.name == "figure_width")
    assert width_check.passed


def test_validate_max_height_exceeded() -> None:
    composed = ComposedFigure(
        svg="<svg/>", width_mm=89.0, height_mm=200.0,
        panel_positions={},
    )
    from figio.schema import TargetProfile
    target = TargetProfile(figure_width_mm=89.0, min_font_pt=5.0, dpi=300, max_height_mm=100.0)
    checks = validate_figure(composed, target)
    height_check = next(c for c in checks if c.name == "max_height")
    assert not height_check.passed


# ---------------------------------------------------------------------------
# Build pipeline tests (using synthetic panels, no matplotlib needed)
# ---------------------------------------------------------------------------


def _write_spec(tmp_path: Path, panels: dict | None = None) -> Path:
    """Write a minimal figurespec with script-based panels."""
    if panels is None:
        panels = {
            "a": {"generator": "script", "source": "panels/a.svg"},
            "b": {"generator": "script", "source": "panels/b.svg"},
        }
    spec = {
        "figure": {
            "id": "fig_test",
            "target": "default",
            "panels": panels,
            "layout": {"type": "grid", "rows": 1, "cols": 2},
            "annotations": [
                {"type": "panel_label", "target": "a", "text": "A"},
            ],
            "style": {"font_family": "Helvetica", "panel_gap_mm": 3},
        }
    }
    spec_path = tmp_path / "figurespec.yaml"
    with open(spec_path, "w") as f:
        yaml.safe_dump(spec, f, sort_keys=False)
    return spec_path


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """figio init creates a scaffold YAML."""
    monkeypatch.chdir(tmp_path)
    from figio.cli import main
    main(["init"])
    assert (tmp_path / "figurespec.yaml").exists()
    # Loading it should succeed
    from figio.schema import FigureSpec
    spec = FigureSpec.from_yaml(tmp_path / "figurespec.yaml")
    assert spec.id == "fig_example"


def test_cli_init_refuses_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """figio init refuses to overwrite existing file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "figurespec.yaml").write_text("existing")
    from figio.cli import main
    with pytest.raises(SystemExit):
        main(["init"])


def test_cli_inspect(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """figio inspect prints spec summary."""
    spec_path = _write_spec(tmp_path)
    from figio.cli import main
    main(["inspect", str(spec_path)])
    output = capsys.readouterr().out
    assert "fig_test" in output
    assert "Panels (2)" in output


def test_cli_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    """figio with no subcommand prints help."""
    from figio.cli import main
    with pytest.raises(SystemExit):
        main([])
