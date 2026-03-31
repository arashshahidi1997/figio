# FigureSpec YAML Reference

A FigureSpec is a declarative manifest describing a multi-panel scientific figure. The spec is the single source of truth — every build produces the same output.

## Top-Level Structure

```yaml
figure:
  id: <string>                    # unique figure identifier
  target: <string | TargetProfile> # journal profile name or inline
  panels: <dict[str, PanelSpec]>  # panel definitions
  layout: <LayoutSpec>            # arrangement specification
  annotations: <list[AnnotationSpec]>  # labels, callouts, arrows
  style: <StyleSpec>              # composition-time style tokens
```

## Panels

Each panel references a generator backend and a source script.

```yaml
panels:
  panel_name:
    generator: matplotlib   # matplotlib | vega | mermaid | graphviz | script
    source: panels/plot.py  # path to panel script (relative to spec)
    inputs:                 # data dependencies (for caching)
      - data/input.csv
    anchors: {}             # named anchor points (optional)
    semantic_ids: []        # element IDs for annotation targeting (optional)
```

### Generator backends

| Backend | Description |
|---------|-------------|
| `matplotlib` | Renders via Matplotlib `make_figure()` or subprocess |
| `vega` | Vega-Lite JSON spec (planned) |
| `mermaid` | Mermaid diagram (planned) |
| `graphviz` | DOT graph (planned) |
| `script` | Generic script producing SVG (planned) |

## Layout

```yaml
layout:
  type: grid              # grid | mosaic
  rows: 2
  cols: 2
  mosaic: null            # mosaic pattern string (for type: mosaic)
  constraints:
    - equal_height: [panel_a, panel_b]
    - align_ylabels: [panel_a, panel_c]
```

### Constraint types

| Constraint | Effect |
|-----------|--------|
| `equal_height` | All listed panels get the same height (max of group) |
| `equal_width` | All listed panels get the same width (max of group) |
| `align_ylabels` | Align left edges of listed panels |
| `align_xlabels` | Align bottom edges of listed panels |
| `shared_colorbar` | Shared colorbar across panels (planned) |

Constraints accept two formats:

```yaml
# Shorthand
- equal_height: [a, b]

# Explicit
- type: equal_height
  panels: [a, b]
```

## Annotations

```yaml
annotations:
  - type: panel_label     # panel_label | callout | arrow | bracket | caption
    target: panel_a       # target panel ID
    text: A               # label text
    position: [-2, -1]    # offset in mm (optional)

  - type: arrow
    start: panel_a        # source panel
    end: panel_b          # destination panel

  - type: caption
    text: "Figure 1. Example figure."
```

## Style

```yaml
style:
  font_family: Helvetica
  font_size_pt: 8         # base font size (optional)
  panel_gap_mm: 3         # gap between panels
  line_weight: 0.5        # default line width
  color_roles:            # named colors for panels to reference
    primary: "#1f77b4"
    secondary: "#ff7f0e"
```

## Target Profiles

Reference a built-in profile by name or define inline:

```yaml
# By name
target: nature_single_column

# Inline
target:
  name: custom
  figure_width_mm: 120
  min_font_pt: 7
  dpi: 300
  max_height_mm: 200
  colorblind_check: true
```

### Built-in profiles

| Name | Width | Min Font | DPI |
|------|-------|----------|-----|
| `nature_single_column` | 89mm | 5pt | 300 |
| `nature_double_column` | 183mm | 5pt | 300 |
| `default` | 170mm | 6pt | 150 |
