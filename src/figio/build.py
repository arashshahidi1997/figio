"""Build engine — orchestrates panel rendering, composition, and export.

Provides file-level caching: panels whose source scripts and inputs have
not changed are skipped on subsequent builds.
"""

from __future__ import annotations

import time
from pathlib import Path

from pydantic import BaseModel, Field

from figio.adapters import PanelResult
from figio.cache import check_cache, compute_hash, update_cache
from figio.composer import ComposedFigure, compose
from figio.export import export_pdf, export_png
from figio.schema import FigureSpec, Generator, StyleSpec
from figio.targets import resolve_target
from figio.validate import ValidationCheck, validate_figure


class BuildResult(BaseModel):
    """Result of a figure build."""

    figure_id: str
    output_svg: str  # Path as string for serialization
    output_pdf: str | None = None
    output_png: str | None = None
    panel_results: dict[str, PanelResult] = Field(default_factory=dict)
    composed: ComposedFigure | None = None
    validation: list[ValidationCheck] = Field(default_factory=list)
    cached_panels: list[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0


def build(
    spec_path: Path,
    output_dir: Path | None = None,
    panels: list[str] | None = None,
    force: bool = False,
    formats: list[str] | None = None,
) -> BuildResult:
    """Build a figure from a FigureSpec YAML file.

    Args:
        spec_path: Path to the FigureSpec YAML.
        output_dir: Output directory (default: ``_build/`` next to spec).
        panels: Subset of panel IDs to render (default: all).
        force: If True, bypass cache and re-render all panels.
        formats: Output formats (default: ``["svg"]``).

    Returns:
        ``BuildResult`` with paths, validation, and timing.
    """
    t0 = time.monotonic()
    spec = FigureSpec.from_yaml(spec_path)
    spec_dir = spec_path.parent.resolve()

    if formats is None:
        formats = ["svg"]

    # Resolve target profile
    target = resolve_target(spec.target)

    # Set up output directory
    if output_dir is None:
        output_dir = spec_dir / "_build"
    output_dir.mkdir(parents=True, exist_ok=True)

    panels_dir = output_dir / "panels"
    panels_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / ".cache"

    # Determine which panels to render
    panel_ids = list(spec.panels.keys()) if panels is None else panels

    # Render panels
    panel_results: dict[str, PanelResult] = {}
    cached_panels: list[str] = []

    for pid in panel_ids:
        if pid not in spec.panels:
            continue
        panel_spec = spec.panels[pid]

        # Compute content hash
        source_path = spec_dir / panel_spec.source
        input_paths = [spec_dir / inp for inp in panel_spec.inputs]
        hash_paths = [source_path] + input_paths
        style_str = spec.style.model_dump_json()
        current_hash = compute_hash(hash_paths, extra=style_str)

        # Check cache
        cached_svg = panels_dir / f"{pid}.svg"
        if not force and check_cache(cache_dir, pid, current_hash) and cached_svg.exists():
            # Load cached SVG
            svg_content = cached_svg.read_text()
            # Reconstruct a minimal PanelResult
            panel_results[pid] = PanelResult(
                svg=svg_content,
                bbox_mm=(0, 0, target.figure_width_mm / spec.layout.cols, 30),
                anchors={},
                semantic_ids=[],
            )
            cached_panels.append(pid)
            continue

        # Render via adapter
        adapter = _get_adapter(panel_spec.generator)
        result = adapter.render(pid, panel_spec, spec.style, spec_dir)
        panel_results[pid] = result

        # Save panel SVG
        cached_svg.write_text(result.svg)
        update_cache(cache_dir, pid, current_hash)

    # Compose
    composed = compose(
        panel_results,
        spec.layout,
        spec.annotations,
        spec.style,
        target,
    )

    # Write composed SVG
    svg_path = output_dir / f"{spec.id}.svg"
    svg_path.write_text(composed.svg)

    # Export derived formats
    pdf_path = None
    png_path = None

    if "pdf" in formats:
        pdf_out = output_dir / f"{spec.id}.pdf"
        if export_pdf(svg_path, pdf_out):
            pdf_path = str(pdf_out)

    if "png" in formats:
        png_out = output_dir / f"{spec.id}.png"
        if export_png(svg_path, png_out, dpi=target.dpi):
            png_path = str(png_out)

    # Validate
    validation = validate_figure(composed, target)

    elapsed = time.monotonic() - t0

    return BuildResult(
        figure_id=spec.id,
        output_svg=str(svg_path),
        output_pdf=pdf_path,
        output_png=png_path,
        panel_results=panel_results,
        composed=composed,
        validation=validation,
        cached_panels=cached_panels,
        elapsed_seconds=round(elapsed, 3),
    )


def _get_adapter(generator: Generator):
    """Instantiate the appropriate adapter for a generator type."""
    if generator == Generator.matplotlib:
        from figio.adapters.matplotlib import MatplotlibAdapter
        return MatplotlibAdapter()
    raise ValueError(
        f"No adapter for generator {generator.value!r}. "
        f"Currently supported: matplotlib"
    )
