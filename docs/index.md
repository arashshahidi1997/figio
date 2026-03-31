# figio

**figio** is a declarative build orchestrator for reproducible scientific figures. It coordinates existing plotting libraries (Matplotlib, Vega-Lite, etc.) through a YAML manifest that describes panels, layout, annotations, and style — then assembles them into a single, validated SVG suitable for journal submission.

## Quick Start

1. Create a figure spec:

```yaml
figure:
  id: fig_example
  target: nature_single_column

  panels:
    psd:
      generator: matplotlib
      source: panels/psd.py
      inputs: [data/session01_psd.parquet]
    topo:
      generator: matplotlib
      source: panels/topomap.py

  layout:
    type: grid
    rows: 1
    cols: 2
    constraints:
      - equal_height: [psd, topo]

  annotations:
    - type: panel_label
      target: psd
      text: A
    - type: panel_label
      target: topo
      text: B

  style:
    font_family: Helvetica
    panel_gap_mm: 3
```

2. Build:

```bash
figio build figurespec.yaml
```

3. Validate against journal requirements:

```bash
figio validate figurespec.yaml --target nature_single_column
```

## Documentation

- [Quick Start](guide/quickstart.md) — step-by-step first figure
- [Multi-Panel Tutorial](guide/tutorial-multipanel.md) — 2×2 grid with constraints, annotations, and journal target
- [Spec Format Reference](guide/spec-format.md) — complete YAML schema
- [Target Profiles](guide/targets.md) — journal requirements, validation workflow, custom profiles
- [Panel Adapters](guide/adapters.md) — writing panel scripts
- [CLI Reference](reference/cli.md) — command-line interface
- [MCP Tools](reference/mcp-tools.md) — agent interface
- [Troubleshooting & FAQ](guide/troubleshooting.md) — common errors and fixes
