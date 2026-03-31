# Quick Start

## Installation

```bash
pip install figio            # core (schema + composer)
pip install figio[mpl]       # + matplotlib adapter
pip install figio[export]    # + PDF/PNG export (CairoSVG)
pip install figio[all]       # everything
```

## Write Your First Spec

Create `figurespec.yaml`:

```yaml
figure:
  id: fig_demo
  target: default

  panels:
    scatter:
      generator: matplotlib
      source: panels/scatter.py

  layout:
    type: grid
    rows: 1
    cols: 1

  annotations:
    - type: panel_label
      target: scatter
      text: A

  style:
    font_family: Helvetica
    panel_gap_mm: 3
```

## Write a Panel Script

Create `panels/scatter.py` with a `make_figure()` function:

```python
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.random.randn(100)
    y = 2 * x + np.random.randn(100) * 0.5
    ax.scatter(x, y, s=10, alpha=0.7)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    return fig
```

## Build

```bash
figio build figurespec.yaml
```

Output: `_build/fig_demo.svg`

## Validate

```bash
figio validate figurespec.yaml --target nature_single_column
```

## Scaffold

Use `figio init` to create a template spec in the current directory.
