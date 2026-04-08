# Tutorial: Multi-Panel Figure

This tutorial walks through building a realistic 2×2 scientific figure —
four panels, grid layout, equal-height constraints, all annotation types,
style tokens, and a Nature double-column target profile.

All files are in [`docs/guide/examples/multipanel/`](examples/multipanel/).

---

## Prerequisites

```bash
pip install figio[all]   # includes matplotlib adapter and PDF/PNG export
```

---

## 1. Create the panel scripts

Each panel is a plain Python file with a `make_figure(**kwargs)` function
that returns a Matplotlib `Figure`. figio renders it and extracts the SVG
— you never touch the composition machinery.

### `panel_line.py` — time-series signal (Panel A)

```python
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(0)
    t = np.linspace(0, 4 * np.pi, 300)
    signal = np.sin(t) + rng.normal(0, 0.15, len(t))

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.plot(t, signal, lw=0.8, color="#1f77b4")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Signal over time")
    fig.tight_layout()
    return fig
```

### `panel_bar.py` — condition means (Panel B)

```python
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(1)
    conditions = ["Control", "Drug A", "Drug B", "Drug C"]
    means = rng.uniform(0.4, 0.9, len(conditions))
    errors = rng.uniform(0.02, 0.08, len(conditions))

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    x = np.arange(len(conditions))
    ax.bar(x, means, yerr=errors, capsize=3, color="#ff7f0e", width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=20, ha="right")
    ax.set_ylabel("Response (a.u.)")
    ax.set_title("Condition comparison")
    fig.tight_layout()
    return fig
```

### `panel_heatmap.py` — correlation matrix (Panel C)

```python
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(2)
    n = 5
    raw = rng.standard_normal((n, n))
    cov = raw @ raw.T
    d = np.sqrt(np.diag(cov))
    corr = cov / np.outer(d, d)
    labels = [f"X{i+1}" for i in range(n)]

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Correlation matrix")
    fig.tight_layout()
    return fig
```

### `panel_scatter.py` — scatter with regression (Panel D)

```python
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(3)
    x = rng.standard_normal(120)
    y = 1.5 * x + rng.standard_normal(120) * 0.6

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.scatter(x, y, s=12, alpha=0.6, color="#2ca02c", edgecolors="none")
    m, b = np.polyfit(x, y, 1)
    xr = np.array([x.min(), x.max()])
    ax.plot(xr, m * xr + b, color="black", lw=1, ls="--")
    ax.set_xlabel("Feature X")
    ax.set_ylabel("Feature Y")
    ax.set_title("X vs Y (r²={:.2f})".format(np.corrcoef(x, y)[0, 1] ** 2))
    fig.tight_layout()
    return fig
```

---

## 2. Write the FigureSpec

Create `figurespec.yaml` alongside the panel scripts:

```yaml
figure:
  id: fig_multipanel
  target: nature_double_column

  panels:
    line:
      generator: matplotlib
      source: panel_line.py

    bar:
      generator: matplotlib
      source: panel_bar.py

    heatmap:
      generator: matplotlib
      source: panel_heatmap.py

    scatter:
      generator: matplotlib
      source: panel_scatter.py

  layout:
    type: grid
    rows: 2
    cols: 2
    constraints:
      - equal_height: [line, bar]
      - equal_height: [heatmap, scatter]

  annotations:
    - type: panel_label
      target: line
      text: A
    - type: panel_label
      target: bar
      text: B
    - type: panel_label
      target: heatmap
      text: C
    - type: panel_label
      target: scatter
      text: D
    - type: caption
      text: "Figure 1. Multi-panel figure. (A) Time-series signal. (B) Condition means ± SEM. (C) Correlation matrix. (D) Scatter plot with regression line."

  style:
    font_family: Helvetica
    font_size_pt: 8
    panel_gap_mm: 4
```

### Key concepts in this spec

**`target: nature_double_column`**
Applies the Nature double-column profile (183 mm wide, ≥5 pt font, 300 DPI).
figio will scale the composed figure to fit and flag any violations during validate.

**`layout.constraints`**
`equal_height` forces both panels in each row to the same height (the maximum
of the two). This ensures a clean grid regardless of individual aspect ratios.

**`annotations`**
- `panel_label` — places a bold letter in the top-left corner of each panel.
  Use `position: [-2, -1]` (mm offsets) to nudge placement if needed.
- `caption` — adds a text block below the figure.

**`style`**
Tokens apply at composition time. `font_size_pt: 8` sets the base size for
annotation text. `panel_gap_mm: 4` controls the whitespace between panels.

---

## 3. Build

```bash
cd docs/guide/examples/multipanel
figio build figurespec.yaml --format svg,pdf,png
```

Expected output:

```
Built fig_multipanel
  SVG: /path/to/_build/fig_multipanel.svg
  PDF: /path/to/_build/fig_multipanel.pdf
  PNG: /path/to/_build/fig_multipanel.png
  Time: 3.21s
  [PASS] figure_width: Figure width 183.0mm matches target 183.0mm
  [PASS] panel_overflow_line: Panel 'line' fits within figure width
  [PASS] panel_overflow_bar: Panel 'bar' fits within figure width
  [PASS] panel_overflow_heatmap: Panel 'heatmap' fits within figure width
  [PASS] panel_overflow_scatter: Panel 'scatter' fits within figure width
  [PASS] dpi: Target DPI is 300 (checked at export time)
```

The `--format svg,pdf,png` flag exports all three formats. Omit it to get SVG only.

To rebuild only specific panels (useful during iteration):

```bash
figio build figurespec.yaml --panels line,bar
```

To force a full rebuild ignoring cache:

```bash
figio build figurespec.yaml --force
```

---

## 4. Validate against the target profile

```bash
figio validate figurespec.yaml --target nature_double_column
```

figio checks:

| Check | What it verifies |
|-------|-----------------|
| `figure_width` | Composed SVG width matches target (±0.5 mm) |
| `max_height` | Height ≤ `max_height_mm` (if profile sets a limit) |
| `panel_overflow_<id>` | Each panel fits within figure bounds |
| `dpi` | Reports target DPI (enforced at export time) |

A passing result:

```
[PASS] figure_width: Figure width 183.0mm matches target 183.0mm
[PASS] panel_overflow_line: Panel 'line' fits within figure width
[PASS] panel_overflow_bar: Panel 'bar' fits within figure width
[PASS] panel_overflow_heatmap: Panel 'heatmap' fits within figure width
[PASS] panel_overflow_scatter: Panel 'scatter' fits within figure width
[PASS] dpi: Target DPI is 300 (checked at export time)
```

A failing result identifies the specific violation:

```
[FAIL] figure_width: Figure width 185.2mm does not match target 183.0mm
```

---

## 5. Inspect the spec

```bash
figio inspect figurespec.yaml
```

This prints a structured summary of panels, layout, annotations, and
resolved target profile — useful for verifying the spec before a long build.

---

## 6. Iterating

**Changing layout:**
Swap `rows: 2, cols: 2` for `rows: 1, cols: 4` to produce a single-row figure.
Remove the `equal_height` constraints if panels have very different heights.

**Adjusting panel gap:**
Increase `panel_gap_mm` for more breathing room, or decrease it to fit
within a tight width budget.

**Nudging panel labels:**
```yaml
- type: panel_label
  target: line
  text: A
  position: [-3, -2]   # shift 3 mm left, 2 mm up
```

**Using a different target:**
```yaml
target: nature_single_column   # 89 mm wide
```

You will likely need to reduce `font_size_pt` and `panel_gap_mm` to pass validation.

---

## Summary

| Concept | Where used |
|---------|-----------|
| `target: nature_double_column` | Journal compliance profile |
| `rows: 2, cols: 2` | 2×2 grid layout |
| `equal_height` constraints | Uniform row heights |
| `panel_label` annotations | A/B/C/D labels |
| `caption` annotation | Figure caption below |
| `font_family`, `font_size_pt`, `panel_gap_mm` | Style tokens |
| `--format svg,pdf,png` | Multi-format export |

The complete runnable example lives in
[`docs/guide/examples/multipanel/`](examples/multipanel/).
