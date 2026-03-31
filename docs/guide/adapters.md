# Panel Adapters

Panel adapters are the bridge between plotting libraries and figio's composition engine. Each adapter renders a panel script into an SVG fragment with metadata (bounding box, anchor points) that the composer uses for positioning.

## Adapter Protocol

All adapters implement:

```python
class PanelAdapter(Protocol):
    def render(self, panel_id: str, spec: PanelSpec, style: StyleSpec,
               workdir: Path) -> PanelResult: ...
    def supported_constraints(self) -> list[str]: ...
```

The `PanelResult` contains:

- `svg` — SVG fragment content
- `bbox_mm` — bounding box (x, y, width, height) in millimeters
- `anchors` — named anchor points for annotation targeting
- `semantic_ids` — element IDs exposed for cross-referencing

## Matplotlib Adapter

The Matplotlib adapter supports two execution models for panel scripts.

### Function-based (preferred)

If your script exposes a `make_figure()` function, figio calls it directly:

```python
# panels/psd.py
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(0, 100, 500)
    ax.semilogy(x, np.random.rand(500) * 10)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (dB)")
    return fig
```

### Script-based (fallback)

If no `make_figure()` function is found, the script is executed as a module. The adapter captures the current `plt.gcf()` figure after execution.

### SVG Normalization

The Matplotlib adapter normalizes SVG output before passing it to the composer:

1. **ID prefixing** — all `id=` attributes are prefixed with the panel ID to prevent collisions when panels are combined
2. **viewBox normalization** — converted to millimeter units
3. **Boilerplate removal** — Matplotlib version comments and metadata are stripped

### Style Token Application

Before rendering, the adapter sets `matplotlib.rcParams` from the spec's StyleSpec:

- `font.family` from `font_family`
- `font.size` from `font_size_pt`
- `lines.linewidth` from `line_weight`

These are restored after rendering.

## Script Adapter

The Script adapter runs any program that can write an SVG file. This lets you use R, Julia, shell scripts wrapping Inkscape, or any other tool without adding Python bindings.

### FigureSpec usage

```yaml
panels:
  violin:
    generator: script
    source: panels/violin.R
```

### Script interface

figio invokes the script as:

```
<interpreter> <script> --output <tmp>.svg --width-mm <float> --height-mm <float>
```

- `--output PATH` — the script **must** write a valid SVG to this path
- `--width-mm` and `--height-mm` — dimension hints (the script may ignore them)

For `.py` scripts, `sys.executable` is used as the interpreter. All other scripts are executed directly (they must be executable and have a `#!` shebang, or you can use a wrapper).

### Minimal Python example

```python
#!/usr/bin/env python3
# panels/violin.py
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--width-mm", type=float, default=80.0)
    parser.add_argument("--height-mm", type=float, default=60.0)
    args = parser.parse_args()

    w, h = args.width_mm, args.height_mm
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="none"/></svg>'
    with open(args.output, "w") as fh:
        fh.write(svg)

if __name__ == "__main__":
    main()
```

### Minimal R example

```r
#!/usr/bin/env Rscript
# panels/violin.R
library(svglite)
args <- commandArgs(trailingOnly = TRUE)
# parse --output, --width-mm, --height-mm ...
svglite(output_path, width = width_mm / 25.4, height = height_mm / 25.4)
# ... plotting code ...
dev.off()
```

### Dimension inference

The Script adapter reads `width` and `height` attributes from the SVG root element and converts them to mm using standard CSS units (`mm`, `pt`, `px`, unitless = px). If those attributes are absent it falls back to the `viewBox` dimensions (treated as pixels at 96 dpi). If no size information is present at all, a 100 × 80 mm default is used.

### SVG normalization

After the script exits, the adapter applies the same normalization as the Matplotlib adapter:

1. **ID prefixing** — all `id=` attributes and `url(#…)` references are prefixed with the panel ID
2. **viewBox normalization** — converted to millimeter units

### Supported constraints

`equal_height`, `equal_width`

## Writing a Custom Adapter

To support a new backend, create a class implementing `PanelAdapter`:

1. Put it in `src/figio/adapters/<backend>.py`
2. Implement `render()` to execute the panel source and return SVG + metadata
3. Implement `supported_constraints()` to declare which layout constraints you honor
4. Register it in `build.py:_get_adapter()`
