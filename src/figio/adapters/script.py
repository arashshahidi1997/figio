"""Script panel adapter.

Runs any script that produces an SVG file via a subprocess interface.
Scripts receive ``--output PATH``, ``--width-mm FLOAT``, and
``--height-mm FLOAT`` arguments; they must write a valid SVG to that path.

Scripts can be any language (Python, R, Julia, shell wrappers, etc.) as
long as the interpreter is on PATH.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from figio.adapters import PanelResult
from figio.schema import PanelSpec, StyleSpec
from figio.svg_utils import extract_viewbox, normalize_viewbox, prefix_ids

# Unit conversion constants
_MM_PER_PX = 25.4 / 96   # CSS reference pixel → mm
_MM_PER_PT = 25.4 / 72   # point → mm

# Default fallback dimensions when the SVG carries no size information
_DEFAULT_WIDTH_MM = 100.0
_DEFAULT_HEIGHT_MM = 80.0


class ScriptAdapter:
    """Adapter that renders panels by executing arbitrary scripts."""

    def render(
        self,
        panel_id: str,
        spec: PanelSpec,
        style: StyleSpec,
        workdir: Path,
    ) -> PanelResult:
        """Execute the panel script and return normalised SVG with metadata."""
        source = workdir / spec.source

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            _run_script(source, output_path, style)
            svg = output_path.read_text(encoding="utf-8")
        finally:
            output_path.unlink(missing_ok=True)

        bbox_mm = _extract_bbox_mm(svg)
        original_viewbox = extract_viewbox(svg)
        svg = prefix_ids(svg, panel_id)
        svg = normalize_viewbox(svg, bbox_mm[2], bbox_mm[3])

        return PanelResult(
            svg=svg,
            bbox_mm=bbox_mm,
            viewbox=original_viewbox,
            anchors={},
            semantic_ids=[],
        )

    def supported_constraints(self) -> list[str]:
        return ["equal_height", "equal_width"]


# ---------------------------------------------------------------------------
# Script execution
# ---------------------------------------------------------------------------


def _run_script(source: Path, output_path: Path, style: StyleSpec) -> None:
    """Execute the panel script with standard figio arguments."""
    cmd = [
        str(source),
        "--output", str(output_path),
        "--width-mm", str(_DEFAULT_WIDTH_MM),
        "--height-mm", str(_DEFAULT_HEIGHT_MM),
    ]

    # Determine interpreter: .py → python, others → run directly
    if source.suffix.lower() == ".py":
        import sys
        cmd = [sys.executable] + cmd

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Script {source} failed (exit {result.returncode}):\n"
            f"{result.stderr or result.stdout}"
        )
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(
            f"Script {source} did not write any SVG to {output_path}"
        )


# ---------------------------------------------------------------------------
# Dimension extraction
# ---------------------------------------------------------------------------


def _extract_bbox_mm(svg: str) -> tuple[float, float, float, float]:
    """Infer bounding box in mm from SVG width/height attributes or viewBox.

    Resolution order:
    1. ``width`` and ``height`` attributes with explicit units (mm, pt, px)
    2. Unitless ``width``/``height`` treated as pixels at 96 dpi
    3. ``viewBox`` dimensions treated as pixels
    4. Fallback constants
    """
    w_mm = _parse_svg_dimension(svg, "width")
    h_mm = _parse_svg_dimension(svg, "height")

    if w_mm is None or h_mm is None:
        vb = extract_viewbox(svg)
        if vb is not None:
            w_mm = w_mm if w_mm is not None else vb[2] * _MM_PER_PX
            h_mm = h_mm if h_mm is not None else vb[3] * _MM_PER_PX

    w_mm = w_mm if w_mm is not None else _DEFAULT_WIDTH_MM
    h_mm = h_mm if h_mm is not None else _DEFAULT_HEIGHT_MM

    return (0.0, 0.0, round(w_mm, 4), round(h_mm, 4))


def _parse_svg_dimension(svg: str, attr: str) -> float | None:
    """Parse a root-level SVG dimension attribute and return its value in mm.

    Recognises ``mm``, ``pt``, ``px``, and unitless (treated as px) values.
    Returns ``None`` if the attribute is absent or unparseable.
    """
    m = re.search(rf'{attr}="([^"]+)"', svg)
    if not m:
        return None
    raw = m.group(1).strip()

    if raw.endswith("mm"):
        try:
            return float(raw[:-2])
        except ValueError:
            return None
    if raw.endswith("pt"):
        try:
            return float(raw[:-2]) * _MM_PER_PT
        except ValueError:
            return None
    if raw.endswith("px"):
        try:
            return float(raw[:-2]) * _MM_PER_PX
        except ValueError:
            return None
    # Unitless — treat as pixels
    try:
        return float(raw) * _MM_PER_PX
    except ValueError:
        return None
