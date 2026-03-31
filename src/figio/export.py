"""Format conversion: SVG to PDF and PNG.

Uses CairoSVG when available; warns gracefully otherwise.
"""

from __future__ import annotations

import warnings
from pathlib import Path


def export_pdf(svg_path: Path, output_path: Path) -> bool:
    """Convert SVG to PDF via CairoSVG.

    Returns True on success, False if CairoSVG is not available.
    """
    try:
        import cairosvg
    except ImportError:
        warnings.warn(
            "cairosvg not installed — PDF export unavailable. "
            "Install with: pip install figio[export]",
            stacklevel=2,
        )
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(url=str(svg_path), write_to=str(output_path))
    return True


def export_png(svg_path: Path, output_path: Path, dpi: int = 150) -> bool:
    """Convert SVG to PNG via CairoSVG at the given DPI.

    Returns True on success, False if CairoSVG is not available.
    """
    try:
        import cairosvg
    except ImportError:
        warnings.warn(
            "cairosvg not installed — PNG export unavailable. "
            "Install with: pip install figio[export]",
            stacklevel=2,
        )
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(svg_path), write_to=str(output_path), dpi=dpi)
    return True
