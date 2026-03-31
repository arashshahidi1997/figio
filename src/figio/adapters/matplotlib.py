"""Matplotlib panel adapter.

Renders a panel script via Matplotlib, captures the figure as SVG,
extracts bounding box metadata, and normalizes the SVG for composition.

Panel scripts can expose a ``make_figure(**kwargs)`` function (preferred)
or be run as standalone scripts that save to a specified output path.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Any, Iterator

from figio.adapters import PanelResult
from figio.schema import PanelSpec, StyleSpec
from figio.svg_utils import extract_viewbox, normalize_viewbox, prefix_ids


class MatplotlibAdapter:
    """Adapter that renders panels via Matplotlib."""

    def render(
        self,
        panel_id: str,
        spec: PanelSpec,
        style: StyleSpec,
        workdir: Path,
    ) -> PanelResult:
        """Render a panel and return normalized SVG with metadata."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        source = workdir / spec.source

        with _apply_style(style):
            fig = _execute_panel(source, workdir)

            # Capture SVG
            buf = BytesIO()
            fig.savefig(buf, format="svg", bbox_inches="tight")
            buf.seek(0)
            svg = buf.read().decode("utf-8")

            # Extract bounding box in mm
            bbox_mm = _extract_bbox_mm(fig)

            # Extract anchors from axes positions
            anchors = _extract_anchors(fig, panel_id)

            plt.close(fig)

        # Normalize SVG
        svg = _strip_mpl_boilerplate(svg)
        original_viewbox = extract_viewbox(svg)
        svg = prefix_ids(svg, panel_id)
        svg = normalize_viewbox(svg, bbox_mm[2], bbox_mm[3])

        return PanelResult(
            svg=svg,
            bbox_mm=bbox_mm,
            viewbox=original_viewbox,
            anchors=anchors,
            semantic_ids=[f"{panel_id}_ax{i}" for i in range(len(fig.axes) if hasattr(fig, 'axes') else 0)],
        )

    def supported_constraints(self) -> list[str]:
        return ["equal_height", "equal_width", "align_ylabels", "align_xlabels"]


# ---------------------------------------------------------------------------
# Panel execution
# ---------------------------------------------------------------------------


def _execute_panel(source: Path, workdir: Path) -> Any:
    """Execute a panel script and return the matplotlib Figure.

    If the script exposes a ``make_figure()`` function, call it directly.
    Otherwise run as a subprocess and capture the saved SVG.
    """
    import matplotlib.pyplot as plt

    # Try function-based approach first
    mod = _load_module(source)
    if hasattr(mod, "make_figure"):
        fig = mod.make_figure()
        return fig

    # Fallback: run as subprocess, capture current figure
    # The script should create a figure via plt
    spec = importlib.util.spec_from_file_location("_panel", source)
    if spec and spec.loader:
        old_argv = sys.argv
        sys.argv = [str(source)]
        try:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.argv = old_argv

    fig = plt.gcf()
    if not fig.axes:
        raise RuntimeError(f"Panel script {source} did not create any axes")
    return fig


def _load_module(source: Path) -> Any:
    """Import a Python source file as a module."""
    spec = importlib.util.spec_from_file_location("_panel", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {source}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Bounding box and anchor extraction
# ---------------------------------------------------------------------------

# Conversion factor: inches to mm
_IN_TO_MM = 25.4


def _extract_bbox_mm(fig: Any) -> tuple[float, float, float, float]:
    """Extract figure bounding box in mm from a Matplotlib figure."""
    w_in, h_in = fig.get_size_inches()
    return (0.0, 0.0, w_in * _IN_TO_MM, h_in * _IN_TO_MM)


def _extract_anchors(fig: Any, panel_id: str) -> dict[str, tuple[float, float]]:
    """Extract anchor points from axes positions (in mm)."""
    anchors: dict[str, tuple[float, float]] = {}
    w_in, h_in = fig.get_size_inches()
    for i, ax in enumerate(fig.axes):
        pos = ax.get_position()
        # Center of each axis in mm
        cx = (pos.x0 + pos.x1) / 2 * w_in * _IN_TO_MM
        cy = (1 - (pos.y0 + pos.y1) / 2) * h_in * _IN_TO_MM  # SVG y is inverted
        anchors[f"{panel_id}_ax{i}_center"] = (round(cx, 2), round(cy, 2))
        # Top-left
        anchors[f"{panel_id}_ax{i}_topleft"] = (
            round(pos.x0 * w_in * _IN_TO_MM, 2),
            round((1 - pos.y1) * h_in * _IN_TO_MM, 2),
        )
    return anchors


# ---------------------------------------------------------------------------
# SVG normalization
# ---------------------------------------------------------------------------


def _strip_mpl_boilerplate(svg: str) -> str:
    """Remove Matplotlib-specific boilerplate from SVG output."""
    # Remove Matplotlib version comments
    svg = re.sub(r'<!-- Created with matplotlib.*?-->\s*', '', svg)
    # Remove date/time metadata comments
    svg = re.sub(r'<!--.*?Date:.*?-->\s*', '', svg)
    # Remove Matplotlib generator metadata
    svg = re.sub(
        r'<metadata>.*?</metadata>',
        '',
        svg,
        flags=re.DOTALL,
    )
    return svg


# ---------------------------------------------------------------------------
# Style context manager
# ---------------------------------------------------------------------------


@contextmanager
def _apply_style(style: StyleSpec) -> Iterator[None]:
    """Temporarily apply style tokens to matplotlib rcParams."""
    import matplotlib.pyplot as plt

    orig = plt.rcParams.copy()
    try:
        plt.rcParams["font.family"] = style.font_family
        if style.font_size_pt is not None:
            plt.rcParams["font.size"] = style.font_size_pt
        plt.rcParams["lines.linewidth"] = style.line_weight
        yield
    finally:
        plt.rcParams.update(orig)
