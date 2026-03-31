---
title: "Implement SVG composer for multi-panel figure assembly"
date: 2026-03-31
timestamp: 20260331-030003-000003
status: done
actionable: true
project_primary: figio
tags: [task, phase-1]
---
# Implement SVG composer for multi-panel figure assembly

## Goal

Build the SVG composer — the core new engineering in figio. It takes panel SVG fragments with metadata envelopes and assembles them into a single composed SVG with proper positioning, annotations, and style.

## Context

This is the most critical piece. The design doc estimates ~500-1000 LOC. It must handle: viewBox normalization, ID deduplication (done by adapter), unit consistency (mm throughout), `<defs>` merging, clipping path management, and typed annotation placement.

Depends on: schema models + adapter protocol (PanelResult).

## Prompt

> Implement the SVG composer for figio. This is a code implementation task — this is the most important module in figio.
>
> 1. Read the design doc section on SVG Composer at `/storage2/arash/projects/projio/docs/log/idea/idea-arash-20260331-022337-352248.md`.
>
> 2. Read the adapter protocol in `src/figio/adapters/__init__.py` to understand `PanelResult` (svg, bbox_mm, anchors, semantic_ids).
>
> 3. Read the schema models in `src/figio/schema.py` — especially LayoutSpec, AnnotationSpec, StyleSpec, TargetProfile.
>
> 4. Create `src/figio/composer.py` with:
>
>    **`ComposedFigure` dataclass/model:**
>    - `svg: str` — final composed SVG content
>    - `width_mm: float`, `height_mm: float`
>    - `panel_positions: dict[str, BBox]` — final positions of each panel (for query_output MCP tool)
>    - `warnings: list[str]` — layout warnings (e.g., overflow, tight fit)
>
>    **`compose(panels: dict[str, PanelResult], layout: LayoutSpec, annotations: list[AnnotationSpec], style: StyleSpec, target: TargetProfile) -> ComposedFigure`:**
>
>    Core algorithm:
>    a. **Grid solver**: Given layout.rows, layout.cols, target.figure_width_mm, and panel bounding boxes:
>       - Distribute available width across columns (equal by default, or weighted)
>       - Calculate row heights from panel aspect ratios
>       - Apply constraints: `equal_height` → max height in group; `equal_width` → max width in group; `align_ylabels` → left-align all y-label anchors
>       - Apply style.panel_gap_mm between panels
>       - Compute total figure height
>
>    b. **SVG assembly**: Build the composed SVG document:
>       - Create root `<svg>` with viewBox in mm, width/height attributes
>       - Create a `<defs>` block merging all panel defs (fonts, gradients, clip paths)
>       - For each panel, wrap its SVG content in a `<g>` with `transform="translate(x, y)"` positioning
>       - Each panel group gets `id="panel-{panel_id}"` for addressability
>
>    c. **Annotation placement**:
>       - `panel_label`: position at top-left of panel bbox with configurable offset, use style font
>       - `callout`: position relative to target panel's anchor point
>       - `arrow`: SVG `<line>` or `<path>` between two anchor points
>       - `bracket`: SVG path grouping multiple panels
>       - `caption`: positioned below figure
>       - All annotations go in a dedicated `<g id="annotations">` layer
>
>    d. **Style application**:
>       - Inject font-family CSS via `<style>` element in defs
>       - Apply panel_gap_mm as spacing
>       - Apply color_roles if panels reference them
>
>    e. **Validation warnings**: check if figure exceeds target max_height_mm, if any panel overflows its allocated cell, if font sizes are below target.min_font_pt
>
> 5. Create `src/figio/svg_utils.py` for SVG manipulation helpers:
>    - `merge_defs(svgs: list[str]) -> str` — extract and merge `<defs>` blocks
>    - `extract_svg_content(svg: str) -> str` — strip outer `<svg>` wrapper, return inner content
>    - `make_svg_document(content: str, width_mm: float, height_mm: float, defs: str = "") -> str` — build a well-formed SVG document
>    - `inject_style(svg: str, css: str) -> str` — add `<style>` element
>    Use `xml.etree.ElementTree` for parsing (stdlib, no extra dependency). Handle SVG namespaces correctly.
>
> 6. Write tests in `tests/test_composer.py`:
>    - Test grid layout with 2 panels in 1 row: verify positions and dimensions
>    - Test 2x2 grid: verify 4-panel layout
>    - Test `equal_height` constraint: panels with different heights get equalized
>    - Test panel label annotations: verify SVG contains label text at correct positions
>    - Test warnings: figure exceeding max_height triggers warning
>    - Test defs merging: two panels with `<defs>` → single merged defs block
>    - Use synthetic PanelResult fixtures (hand-crafted minimal SVG fragments), NOT actual matplotlib renders
>
> 7. Run tests to verify.

## Acceptance Criteria

- [ ] `compose()` function produces valid SVG from panel fragments
- [ ] Grid layout solver handles rows/cols/gaps
- [ ] Constraint handling (equal_height, equal_width, align)
- [ ] Panel label annotations placed correctly
- [ ] `<defs>` merging works
- [ ] Validation warnings for target violations
- [ ] Tests pass with synthetic SVG fixtures


## Batch Result

- status: done
- batch queue_id: `735c988b6fbb`
- session: `d48ef8e3-1dbb-443a-a603-941c084a0b14`
- batch duration: 1128.7s
