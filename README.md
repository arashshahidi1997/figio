# figio

Declarative build orchestrator for reproducible scientific figures.

Distribution name: `figio`
Import package: `figio`
CLI: `figio`

figio coordinates existing plotting libraries (Matplotlib, Vega-Lite, etc.) through a YAML manifest (FigureSpec) that describes panels, layout, annotations, and style tokens — then assembles them into a single, validated SVG suitable for journal submission.

figio is an **orchestration system**, not a rendering engine. Panels are opaque — figio doesn't reach inside them. It coordinates their output into a composed figure with validated positioning, annotations, and journal compliance checks.

## Install

```bash
pip install figio                # core orchestrator
pip install "figio[mpl]"         # + Matplotlib adapter
pip install "figio[export]"      # + PDF/PNG export via CairoSVG
pip install "figio[all]"         # everything
```

## Quick start

```bash
# Scaffold a figure spec
figio init

# Build a figure from spec
figio build figures/fig1.yaml

# Validate against journal target
figio validate figures/fig1.yaml --target nature

# Inspect spec metadata
figio inspect figures/fig1.yaml
```

## Architecture

```
FigureSpec (YAML) → Adapters → Panel SVGs → Composer → Composed SVG → Export (PDF/PNG)
```

| Layer | What it does |
|-------|-------------|
| **Schema** | Pydantic models: FigureSpec, PanelSpec, LayoutSpec, AnnotationSpec |
| **Targets** | Built-in journal profiles (Nature, default) with size/font constraints |
| **Adapters** | Protocol + backends: Matplotlib renders panels to SVG |
| **Composer** | Grid solver, constraint application, SVG assembly, annotation placement |
| **Validate** | Checks against target profile (width, height, font size, overflow) |
| **Export** | SVG → PDF/PNG via CairoSVG (optional dependency) |
| **Cache** | SHA-256 content hashing for incremental rebuilds |

## Part of the projio ecosystem

figio integrates with [projio](https://github.com/arashshahidi1997/projio) as the figure orchestration layer. When used through projio's MCP server, it exposes tools for AI-assisted figure authoring: `figio_build`, `figio_inspect`, `figio_validate`, `figio_edit_spec`, `figio_query_output`.

## License

MIT
