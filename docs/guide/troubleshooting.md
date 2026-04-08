# Troubleshooting & FAQ

## "Panel shows only top-left corner"

**Symptom:** The composed figure renders only a small region of a panel — typically the top-left corner — instead of the full panel content.

**Cause:** A coordinate mismatch between the SVG's `viewBox` and its declared `width`/`height`. Matplotlib exports SVG coordinates in points (72 pt = 1 inch), while figio works in millimetres. If the `viewBox` is not correctly mapped, figio uses the wrong bounding box when placing the panel.

**Fix:** figio automatically normalises the `viewBox` during SVG assembly. If you encounter this issue with a custom adapter:

1. Ensure your adapter returns a valid SVG with a `viewBox` attribute on the root `<svg>` element.
2. The `viewBox` must cover the full content area: `viewBox="0 0 <width_pt> <height_pt>"`.
3. The `width` and `height` attributes should include units (e.g. `width="180pt"`). figio reads these to compute the mm conversion factor.

Matplotlib's default SVG export sets these correctly. If you post-process the SVG (e.g. with Inkscape or `svgutils`), verify the root element attributes are preserved.


## "Panels overlap"

**Symptom:** Two or more panels are drawn on top of each other in the composed output.

**Likely causes and fixes:**

- **`panel_gap_mm` too small or zero.** Add or increase the gap in the style block:
  ```yaml
  style:
    panel_gap_mm: 3
  ```
- **Layout dimensions smaller than panel content.** Check that `figure_width_mm` / `figure_height_mm` (from the target profile or spec) can accommodate all panels at their minimum size. Run `figio validate` to surface dimension violations.
- **Explicit `x`/`y` offsets in a `free` layout collide.** Switch to a `grid` layout and let figio compute positions automatically.


## "Validation fails on figure_width"

**Symptom:** `figio validate` exits with an error such as:
```
figure_width 200.0 mm exceeds target max 89.0 mm
```

**Cause:** The figure dimensions exceed the constraints of the selected target profile. Each built-in profile (e.g. `nature_single_column`, `nature_double_column`) enforces a maximum width and height.

**Fix options:**

1. Switch to a wider target profile:
   ```bash
   figio validate figurespec.yaml --target nature_double_column
   ```
2. Reduce the number of columns or panel sizes so the figure fits.
3. Define a custom inline target profile in your spec:
   ```yaml
   figure:
     id: fig1
     target:
       name: my_journal
       figure_width_mm: 175
       min_font_pt: 6
       dpi: 300
     panels: { ... }
   ```


## "CairoSVG not found"

**Symptom:**
```
ImportError: figio export requires cairosvg. Install with: pip install figio[export]
```

**Cause:** PDF and PNG export depend on [CairoSVG](https://cairosvg.org/), which is an optional dependency not installed by default.

**Fix:**
```bash
pip install "figio[export]"
```

CairoSVG itself requires the Cairo C library. On common platforms:

| Platform | Install command |
|----------|----------------|
| Ubuntu/Debian | `sudo apt install libcairo2` |
| macOS (Homebrew) | `brew install cairo` |
| Conda | `conda install -c conda-forge cairo` |

If you only need SVG output, omit `--format pdf,png` and the dependency is not required.


## "make_figure not found" / panel script errors

**Symptom:** The build fails with:
```
AttributeError: module 'panels.my_panel' has no attribute 'make_figure'
```
or the panel script runs but produces no output file.

**Cause:** figio's Matplotlib adapter expects each panel script to expose a `make_figure()` function that **returns** a Matplotlib `Figure` object. If the function is missing or has the wrong signature, the adapter falls back to script-based execution (capturing `plt.gcf()`), which may fail if no figure was created.

**Fix:** Structure every panel script as a callable module:

```python
import matplotlib.pyplot as plt

def make_figure(**kwargs):
    fig, ax = plt.subplots()
    # ... draw content ...
    return fig
```

The adapter calls `make_figure()`, captures the returned figure as SVG, and closes it. Do not call `plt.show()` or `fig.savefig()` inside `make_figure` — figio handles SVG export internally.


## "Cache not invalidating" / stale output

**Symptom:** You edited a panel script or data file but `figio build` reuses the old cached SVG.

**How the cache works:** figio caches each panel's rendered SVG keyed by a SHA-256 hash of:
- The panel source file content
- All declared `inputs` file contents
- The style tokens passed to the panel

A cache hit means **none of these changed**. The cache does **not** track:
- Environment variables
- Conda/pip package versions
- Files not listed in `inputs`

**Force a full rebuild:**
```bash
figio build figurespec.yaml --force
```

**Invalidate a single panel** by touching its source file or adding `--panels my_panel --force`.

**Best practice:** List all data files your panel reads under `inputs` in the spec so the cache key captures them:
```yaml
panels:
  psd:
    generator: matplotlib
    source: panels/psd.py
    inputs: [data/session01.parquet, data/session02.parquet]
```


## "SVG IDs conflict" / garbled composed output

**Symptom:** The composed SVG has visual glitches, missing elements, or elements from one panel appear in another.

**Cause:** SVG element `id` attributes must be unique within a document. When multiple panels share the same internal IDs (e.g. `clip0`, `path1`), merging them produces an invalid document.

**How figio handles it:** The SVG assembly layer prefixes every `id` and cross-reference (`href`, `xlink:href`, `clip-path`, `fill`, `url(#...)`) with a panel-specific namespace (e.g. `p0_`, `p1_`). This is automatic.

**Edge cases where conflicts can still occur:**
- Inline `<style>` blocks with class selectors — figio does not rewrite CSS class names. Avoid global class names in panel SVGs; prefer inline styles or element-level attributes.
- Hard-coded URLs inside Matplotlib path effects — use unique IDs in custom patches.

If you suspect an ID clash, inspect the raw panel SVG with:
```bash
grep 'id=' output/panels/my_panel.svg | sort | uniq -d
```
Duplicate IDs within a single panel SVG indicate a Matplotlib or adapter bug, not a figio issue.


## "Fonts don't match" / inconsistent typography

**Symptom:** The rendered figure uses a different font than specified in the style block, or fonts differ between panels.

**How style tokens map to Matplotlib rcParams:**

| figio style key | Matplotlib rcParam |
|---|---|
| `font_family` | `font.family` |
| `font_size_pt` | `font.size` |
| `line_weight` | `lines.linewidth` |

figio injects these as `rcParams` before calling `make_figure`. However, Matplotlib resolves font names against the fonts installed on the system. If the requested font is not available, Matplotlib silently falls back to DejaVu Sans.

**Fixes:**

1. **Verify the font is installed:**
   ```python
   import matplotlib.font_manager as fm
   print([f.name for f in fm.fontManager.ttflist if "Helvetica" in f.name])
   ```
2. **Rebuild the font cache** after installing new fonts:
   ```python
   import matplotlib.font_manager as fm
   fm._rebuild()
   ```
3. **Use a universally available substitute** such as `Arial` (Windows/macOS) or `Liberation Sans` (Linux) if Helvetica is unavailable.
4. **Embed fonts in the SVG** by setting `svg.fonttype: path` in your panel's rcParams — this converts text to paths, ensuring exact reproduction at the cost of non-selectable text.
