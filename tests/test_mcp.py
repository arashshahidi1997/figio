"""Tests for figio MCP tool functions."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from figio.mcp import (
    mcp_build,
    mcp_edit_spec,
    mcp_figure_list,
    mcp_inspect,
    mcp_query_output,
    mcp_validate,
)


def _write_spec(root: Path, figure_id: str = "fig_test") -> Path:
    """Write a minimal figurespec for testing."""
    spec = {
        "figure": {
            "id": figure_id,
            "target": "default",
            "panels": {
                "a": {"generator": "matplotlib", "source": "panels/a.py"},
                "b": {"generator": "matplotlib", "source": "panels/b.py"},
            },
            "layout": {"type": "grid", "rows": 1, "cols": 2},
            "annotations": [
                {"type": "panel_label", "target": "a", "text": "A"},
            ],
            "style": {"font_family": "Helvetica", "panel_gap_mm": 3},
        }
    }
    spec_path = root / "figurespec.yaml"
    with open(spec_path, "w") as f:
        yaml.safe_dump(spec, f, sort_keys=False)
    return spec_path


# ---------------------------------------------------------------------------
# mcp_figure_list
# ---------------------------------------------------------------------------


def test_figure_list_empty(tmp_path: Path) -> None:
    result = mcp_figure_list(tmp_path)
    assert result["count"] == 0


def test_figure_list_finds_spec(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_figure_list(tmp_path)
    assert result["count"] == 1
    assert result["figures"][0]["figure_id"] == "fig_test"


# ---------------------------------------------------------------------------
# mcp_inspect
# ---------------------------------------------------------------------------


def test_inspect_no_id(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_inspect(tmp_path)
    # Falls back to listing
    assert "figures" in result or "count" in result


def test_inspect_with_id(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_inspect(tmp_path, figure_id="fig_test")
    assert result["figure_id"] == "fig_test"
    assert "panels" in result
    assert "a" in result["panels"]
    assert "b" in result["panels"]
    assert result["layout"]["type"] == "grid"


def test_inspect_missing(tmp_path: Path) -> None:
    result = mcp_inspect(tmp_path, figure_id="nonexistent")
    assert "error" in result


# ---------------------------------------------------------------------------
# mcp_validate
# ---------------------------------------------------------------------------


def test_validate(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_validate(tmp_path, figure_id="fig_test")
    assert "checks" in result
    assert isinstance(result["all_passed"], bool)


def test_validate_with_target(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_validate(tmp_path, figure_id="fig_test", target="nature_single_column")
    assert "checks" in result


# ---------------------------------------------------------------------------
# mcp_edit_spec
# ---------------------------------------------------------------------------


def test_edit_spec(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_edit_spec(
        tmp_path,
        figure_id="fig_test",
        patch={"style": {"font_family": "Arial"}},
    )
    assert result["updated"] is True

    # Verify the change persisted
    result2 = mcp_inspect(tmp_path, figure_id="fig_test")
    assert result2["style"]["font_family"] == "Arial"


def test_edit_spec_invalid_patch(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_edit_spec(
        tmp_path,
        figure_id="fig_test",
        patch={"panels": "not_a_dict"},
    )
    assert "error" in result


# ---------------------------------------------------------------------------
# mcp_query_output
# ---------------------------------------------------------------------------


def test_query_output_no_build(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = mcp_query_output(tmp_path, figure_id="fig_test", query="dimensions")
    assert "error" in result  # No build yet
