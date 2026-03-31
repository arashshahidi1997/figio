"""SVG Composer — assembles panel SVG fragments into a single composed figure.

This is the core composition engine. It:
- Positions panels according to layout and constraints
- Merges SVG defs (fonts, gradients, clip paths)
- Attaches typed annotations (panel labels, callouts, arrows)
- Applies style tokens (font injection, gap spacing)
- Validates against target profile constraints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from figio.adapters import PanelResult
from figio.schema import (
    AnnotationSpec,
    AnnotationType,
    ConstraintType,
    LayoutConstraint,
    LayoutSpec,
    StyleSpec,
    TargetProfile,
)
from figio.svg_utils import extract_svg_content, inject_style, make_svg_document, merge_defs


@dataclass
class BBox:
    """Axis-aligned bounding box in mm."""

    x: float
    y: float
    width: float
    height: float


@dataclass
class ComposedFigure:
    """Result of figure composition."""

    svg: str
    width_mm: float
    height_mm: float
    panel_positions: dict[str, BBox] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compose(
    panels: dict[str, PanelResult],
    layout: LayoutSpec,
    annotations: list[AnnotationSpec],
    style: StyleSpec,
    target: TargetProfile,
) -> ComposedFigure:
    """Compose panel SVG fragments into a single figure SVG.

    Args:
        panels: Rendered panel results keyed by panel ID.
        layout: Layout specification (grid/mosaic, constraints).
        annotations: Typed annotations to overlay.
        style: Style tokens for composition.
        target: Target profile for dimensions and validation.

    Returns:
        A ``ComposedFigure`` with the composed SVG and metadata.
    """
    warnings: list[str] = []

    # 1. Solve grid positions
    positions = _solve_grid(panels, layout, style, target)

    # 2. Apply constraints
    _apply_constraints(positions, panels, layout.constraints, warnings)

    # 3. Compute total figure dimensions
    fig_width = target.figure_width_mm
    fig_height = _compute_figure_height(positions)

    # 4. Merge defs from all panels
    all_svgs = [p.svg for p in panels.values()]
    merged_defs = merge_defs(all_svgs)

    # 4b. Inject arrow marker def if any arrow annotations exist
    if any(a.type == AnnotationType.arrow for a in annotations):
        merged_defs += "\n" + _build_marker_defs()

    # 5. Build panel groups using nested <svg> elements for correct viewBox mapping
    panel_groups: list[str] = []
    for panel_id, pos in positions.items():
        if panel_id not in panels:
            continue  # skip metadata entries like __colorbar
        panel = panels[panel_id]
        panel_svg = extract_svg_content(panel.svg)

        # Use the original viewBox (internal coordinate system) if available,
        # otherwise fall back to bbox_mm (which may not match internal coords)
        if panel.viewbox:
            vb = f"{panel.viewbox[0]} {panel.viewbox[1]} {panel.viewbox[2]} {panel.viewbox[3]}"
        else:
            vb = f"0 0 {panel.bbox_mm[2]:.2f} {panel.bbox_mm[3]:.2f}"

        # Nested <svg> with viewBox handles coordinate mapping natively
        group = (
            f'  <svg id="panel-{panel_id}" '
            f'x="{pos.x:.2f}" y="{pos.y:.2f}" '
            f'width="{pos.width:.2f}" height="{pos.height:.2f}" '
            f'viewBox="{vb}" preserveAspectRatio="xMidYMid meet">\n'
            f'    {panel_svg}\n'
            f'  </svg>'
        )
        panel_groups.append(group)

    # 6. Build annotation layer
    annotation_svg = _build_annotations(annotations, positions, style)

    # 7. Assemble content
    content_parts = panel_groups
    if annotation_svg:
        content_parts.append(f'  <g id="annotations">\n{annotation_svg}\n  </g>')
    content = "\n".join(content_parts)

    # 8. Build font CSS
    css = f'text, tspan {{ font-family: "{style.font_family}"; }}'
    if style.font_size_pt:
        css += f'\ntext {{ font-size: {style.font_size_pt}pt; }}'

    # 9. Make document
    svg = make_svg_document(content, fig_width, fig_height, defs=merged_defs)
    svg = inject_style(svg, css)

    # 10. Validation warnings
    if target.max_height_mm and fig_height > target.max_height_mm:
        warnings.append(
            f"Figure height {fig_height:.1f}mm exceeds target max {target.max_height_mm:.1f}mm"
        )

    for panel_id, pos in positions.items():
        if pos.x + pos.width > fig_width + 0.1:
            warnings.append(f"Panel {panel_id!r} overflows figure width")

    return ComposedFigure(
        svg=svg,
        width_mm=fig_width,
        height_mm=fig_height,
        panel_positions=positions,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Grid solver
# ---------------------------------------------------------------------------


def _solve_grid(
    panels: dict[str, PanelResult],
    layout: LayoutSpec,
    style: StyleSpec,
    target: TargetProfile,
) -> dict[str, BBox]:
    """Distribute panels in a grid layout.

    Assigns positions based on grid row/col, distributing available width
    evenly across columns and computing row heights from panel aspect ratios.
    """
    rows = layout.rows
    cols = layout.cols
    gap = style.panel_gap_mm
    fig_width = target.figure_width_mm

    # Available width for panels (subtract gaps between columns)
    available_width = fig_width - gap * (cols - 1)
    col_width = available_width / cols

    # Map panel IDs to grid cells (row-major order)
    panel_ids = list(panels.keys())

    # Compute row heights from panel aspect ratios
    row_heights: list[float] = []
    for r in range(rows):
        max_h = 0.0
        for c in range(cols):
            idx = r * cols + c
            if idx < len(panel_ids):
                pid = panel_ids[idx]
                bbox = panels[pid].bbox_mm
                aspect = bbox[3] / bbox[2] if bbox[2] > 0 else 1.0
                panel_h = col_width * aspect
                max_h = max(max_h, panel_h)
        row_heights.append(max_h if max_h > 0 else col_width)

    # Assign positions
    positions: dict[str, BBox] = {}
    y_offset = 0.0
    for r in range(rows):
        x_offset = 0.0
        for c in range(cols):
            idx = r * cols + c
            if idx < len(panel_ids):
                pid = panel_ids[idx]
                positions[pid] = BBox(
                    x=x_offset,
                    y=y_offset,
                    width=col_width,
                    height=row_heights[r],
                )
            x_offset += col_width + gap
        y_offset += row_heights[r] + gap

    return positions


# ---------------------------------------------------------------------------
# Constraint application
# ---------------------------------------------------------------------------


def _apply_constraints(
    positions: dict[str, BBox],
    panels: dict[str, PanelResult],
    constraints: list[LayoutConstraint],
    warnings: list[str],
) -> None:
    """Apply layout constraints to panel positions (in-place)."""
    for constraint in constraints:
        affected = [p for p in constraint.panels if p in positions]
        if not affected:
            continue

        if constraint.type == ConstraintType.equal_height:
            max_h = max(positions[p].height for p in affected)
            for p in affected:
                positions[p].height = max_h

        elif constraint.type == ConstraintType.equal_width:
            max_w = max(positions[p].width for p in affected)
            for p in affected:
                positions[p].width = max_w

        elif constraint.type == ConstraintType.align_ylabels:
            # Align left edges
            min_x = min(positions[p].x for p in affected)
            for p in affected:
                positions[p].x = min_x

        elif constraint.type == ConstraintType.align_xlabels:
            # Align bottom edges (y + height)
            max_bottom = max(positions[p].y + positions[p].height for p in affected)
            for p in affected:
                positions[p].height = max_bottom - positions[p].y

        elif constraint.type == ConstraintType.shared_colorbar:
            # Reserve space on the right for a shared colorbar.
            # Shrink each affected panel by a fraction and place a
            # colorbar-width column to the right of the rightmost panel.
            colorbar_frac = 0.08  # 8% of panel width
            rightmost = max(positions[p].x + positions[p].width for p in affected)
            max_w = max(positions[p].width for p in affected)
            colorbar_w = max_w * colorbar_frac
            for p in affected:
                positions[p].width -= colorbar_w
            # Store colorbar region as a BBox keyed "__colorbar"
            top_y = min(positions[p].y for p in affected)
            bot_y = max(positions[p].y + positions[p].height for p in affected)
            # Recalculate rightmost after shrinking
            new_rightmost = max(
                positions[p].x + positions[p].width for p in affected
            )
            gap = 1.0  # small gap before colorbar
            positions["__colorbar"] = BBox(
                x=new_rightmost + gap,
                y=top_y,
                width=colorbar_w,
                height=bot_y - top_y,
            )
            warnings.append(
                "shared_colorbar: space reserved; adapter must provide colorbar SVG content"
            )


# ---------------------------------------------------------------------------
# Arrow marker defs
# ---------------------------------------------------------------------------


def _build_marker_defs() -> str:
    """Return an SVG ``<marker>`` definition for arrowhead endings.

    The marker uses mm-scale coordinates to match the composed viewBox.
    """
    return (
        '<marker id="arrowhead" markerWidth="4" markerHeight="3" '
        'refX="4" refY="1.5" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L4,1.5 L0,3 Z" fill="black"/>'
        '</marker>'
    )


# ---------------------------------------------------------------------------
# Figure height computation
# ---------------------------------------------------------------------------


def _compute_figure_height(positions: dict[str, BBox]) -> float:
    """Compute total figure height from panel positions."""
    if not positions:
        return 0.0
    return max(p.y + p.height for p in positions.values())


# ---------------------------------------------------------------------------
# Annotation placement
# ---------------------------------------------------------------------------


def _build_annotations(
    annotations: list[AnnotationSpec],
    positions: dict[str, BBox],
    style: StyleSpec,
) -> str:
    """Build SVG elements for annotations."""
    parts: list[str] = []
    font_size = style.font_size_pt or 8.0
    label_size = font_size + 2  # Labels slightly larger

    for ann in annotations:
        if ann.type == AnnotationType.panel_label:
            if ann.target not in positions:
                continue
            pos = positions[ann.target]
            # Default offset: top-left of panel, slightly outside
            dx = ann.position[0] if len(ann.position) > 0 else -2.0
            dy = ann.position[1] if len(ann.position) > 1 else -1.0
            x = pos.x + dx
            y = pos.y + dy
            parts.append(
                f'    <text x="{x:.2f}" y="{y:.2f}" '
                f'font-size="{label_size:.1f}pt" font-weight="bold">'
                f'{ann.text}</text>'
            )

        elif ann.type == AnnotationType.caption:
            # Position below the figure
            fig_h = _compute_figure_height(positions)
            x = ann.position[0] if len(ann.position) > 0 else 0.0
            y = fig_h + (ann.position[1] if len(ann.position) > 1 else 5.0)
            parts.append(
                f'    <text x="{x:.2f}" y="{y:.2f}" '
                f'font-size="{font_size:.1f}pt">'
                f'{ann.text}</text>'
            )

        elif ann.type == AnnotationType.arrow:
            # Arrow between two panels
            if ann.start in positions and ann.end in positions:
                p1 = positions[ann.start]
                p2 = positions[ann.end]
                x1 = p1.x + p1.width
                y1 = p1.y + p1.height / 2
                x2 = p2.x
                y2 = p2.y + p2.height / 2
                parts.append(
                    f'    <line x1="{x1:.2f}" y1="{y1:.2f}" '
                    f'x2="{x2:.2f}" y2="{y2:.2f}" '
                    f'stroke="black" stroke-width="0.5" '
                    f'marker-end="url(#arrowhead)"/>'
                )

        elif ann.type == AnnotationType.callout:
            if ann.target in positions:
                pos = positions[ann.target]
                x = pos.x + (ann.position[0] if len(ann.position) > 0 else pos.width / 2)
                y = pos.y + (ann.position[1] if len(ann.position) > 1 else -3.0)
                parts.append(
                    f'    <text x="{x:.2f}" y="{y:.2f}" '
                    f'font-size="{font_size:.1f}pt" text-anchor="middle">'
                    f'{ann.text}</text>'
                )

        elif ann.type == AnnotationType.bracket:
            # Square bracket grouping panels: vertical ends + horizontal bar
            if ann.start in positions and ann.end in positions:
                p1 = positions[ann.start]
                p2 = positions[ann.end]
                tick = 2.0  # vertical tick height in mm
                y_top = min(p1.y, p2.y) - 3.0
                y_bottom = y_top + tick
                x_left = p1.x
                x_right = p2.x + p2.width
                # Square bracket path: left tick down, across, right tick down
                parts.append(
                    f'    <path d="M{x_left:.2f},{y_bottom:.2f} '
                    f'L{x_left:.2f},{y_top:.2f} '
                    f'L{x_right:.2f},{y_top:.2f} '
                    f'L{x_right:.2f},{y_bottom:.2f}" '
                    f'stroke="black" stroke-width="0.5" fill="none"/>'
                )
                # Label text centered above the bracket
                if ann.text:
                    x_mid = (x_left + x_right) / 2
                    y_text = y_top - 1.5
                    parts.append(
                        f'    <text x="{x_mid:.2f}" y="{y_text:.2f}" '
                        f'font-size="{font_size:.1f}pt" text-anchor="middle">'
                        f'{ann.text}</text>'
                    )

    return "\n".join(parts)
