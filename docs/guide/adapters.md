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

## Writing a Custom Adapter

To support a new backend, create a class implementing `PanelAdapter`:

1. Put it in `src/figio/adapters/<backend>.py`
2. Implement `render()` to execute the panel source and return SVG + metadata
3. Implement `supported_constraints()` to declare which layout constraints you honor
4. Register it in `build.py:_get_adapter()`
