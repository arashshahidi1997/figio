# Figio Design Spec

## What Figio Is

Figio is a declarative build orchestrator for reproducible scientific figures. It coordinates existing plotting libraries through a YAML manifest (FigureSpec) that describes panels, layout, annotations, and style tokens, then assembles them into a single, validated SVG suitable for journal submission.

Figio is an **orchestration system**, not a rendering engine. Panels are opaque -- figio does not reach inside them. It coordinates their output into a composed figure with validated positioning, annotations, and journal compliance checks.

## Why It Exists

Scientific figures for journal submission require precise dimensional compliance (width in mm, minimum font size, DPI), reproducible builds from source data, and consistent styling across multi-panel layouts. These requirements are tedious to enforce manually and error-prone when figures change during revision cycles.

Existing tools (Matplotlib, seaborn, plotly) generate individual panels but do not compose them into a single figure with validated journal constraints. Manual composition in Illustrator/Inkscape breaks reproducibility. Figio fills the gap: declarative specification, automated composition, and target-profile validation.

## Design Principles

1. **Panels are opaque.** Figio never modifies panel content. Adapters render panels into SVG; the composer places them. This separation means any plotting library that produces SVG can be an adapter.

2. **The spec is the source of truth.** Every build from the same FigureSpec and panel scripts produces the same output. No hidden state, no interactive tweaking.

3. **Validation is first-class.** Target profiles encode journal requirements. Validation runs automatically after every build. A figure that fails validation should not be submitted.

4. **Caching for iteration speed.** Panel rendering is the expensive step. SHA-256 content hashing ensures only changed panels re-render. Full rebuilds take seconds, cached rebuilds are instant.

5. **MCP-first agent interface.** All operations are exposed as MCP tools for agent-driven figure management within the projio ecosystem.

## Architecture

```
FigureSpec (YAML) --> Adapters --> Panel SVGs --> Composer --> Composed SVG --> Export (PDF/PNG)
                                                    ^
                                                    |
                                               Target Profile
                                              (validation checks)
```

### Layers

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Schema | `schema.py` | Pydantic models: FigureSpec, PanelSpec, LayoutSpec, AnnotationSpec, StyleSpec, TargetProfile |
| Targets | `targets.py` | Built-in journal profiles (Nature, Science, PNAS, eLife, PLOS, Cell, IEEE), target resolution |
| Adapters | `adapters/` | Protocol + backends: `matplotlib.py` renders via Matplotlib, `script.py` runs generic scripts |
| Composer | `composer.py` | Grid solver, constraint application, SVG assembly with nested `<svg>` elements, annotation placement |
| SVG Utils | `svg_utils.py` | Defs merging, content extraction, document building, style injection |
| Build | `build.py` | Orchestrates render -> compose -> export pipeline with file-level caching |
| Cache | `cache.py` | SHA-256 content hashing, cache check/update |
| Validate | `validate.py` | Checks against target profile (width, height, font size, DPI, colorblind safety) |
| Export | `export.py` | SVG -> PDF/PNG via CairoSVG (optional dependency) |
| CLI | `cli.py` | `figio build/validate/inspect/init` commands |
| MCP | `mcp.py` | Tool functions for projio MCP server integration |

### Adapter Protocol

All adapters implement:

```python
class PanelAdapter(Protocol):
    def render(self, panel_id: str, spec: PanelSpec, style: StyleSpec,
               workdir: Path) -> PanelResult: ...
    def supported_constraints(self) -> list[str]: ...
```

PanelResult contains:
- `svg` -- rendered SVG fragment
- `bbox_mm` -- bounding box in mm
- `viewbox` -- original SVG viewBox (internal coordinate system)
- `anchors` -- named anchor points for annotation targeting
- `semantic_ids` -- element IDs for cross-referencing

### Composition Model

The composer uses **nested `<svg>` elements** for coordinate mapping. Each panel retains its original viewBox (typically in points for Matplotlib) while being placed in the composed figure's mm-based coordinate space. SVG handles the coordinate transformation natively via `viewBox` + `preserveAspectRatio`.

This avoids the fragile alternative of manual scale transforms, which fail when the panel's internal coordinates don't match the composed figure's units.

Annotations (panel labels, captions, callouts) are placed in the outer mm-based coordinate space as a separate `<g id="annotations">` layer. Font sizes for annotations use bare user units (= mm in the viewBox), not `pt` or `mm` CSS units, because CairoSVG double-scales absolute CSS units within a viewBox-based coordinate system.

### Validation Model

Validation checks run against a TargetProfile after composition:

| Check | Source | Severity |
|-------|--------|----------|
| `figure_width` | composed width vs target | error |
| `max_height` | composed height vs target max | warning |
| `panel_overflow_{id}` | panel right edge vs figure width | error |
| `min_font_size` | extracted font sizes vs target min | error |
| `dpi` / `png_dimensions` | PNG pixel dimensions vs target DPI | warning |
| `colorblind_safety` | deuteranopia simulation on extracted palette | warning |

Font sizes are extracted from panel SVG content only (the annotation layer is excluded -- its sizes are controlled by figio, not user content).

The colorblind check uses the Vienot 1999 deuteranopia simulation matrix with a ratio-based detection threshold: pairs whose simulated distance / original distance < 0.15 are flagged.

## Non-Goals

- **Not a plotting library.** Figio does not generate plots, charts, or diagrams. It composes output from libraries that do.
- **Not a GUI.** No interactive editor. The YAML spec and CLI/MCP tools are the interface.
- **Not a template system.** Each figure is independently specified. There is no inheritance or template mechanism between figures.
- **Not a layout engine.** Grid layout with constraints covers the common case. Arbitrary freeform placement is not supported.

## Relationship to the Projio Ecosystem

Figio is a standalone package (`pip install figio`) that integrates into the projio ecosystem as a registered package:

- **projio MCP server** wraps figio's 6 tools (`figio_figure_list`, `figio_inspect`, `figio_build`, `figio_validate`, `figio_edit_spec`, `figio_query_output`)
- **notio/manuscript** calls figio for figure building (`manuscript_figure_insert`, `manuscript_figure_build_all`)
- **`agent_instructions()`** includes figio tool routing when the package is enabled
- **`ecosystem_status()`** reports figure count

The full paper production pipeline: **figio** (figures) + **biblio** (citations) + **notio/manuscript** (section assembly + pandoc render) = PDF.
