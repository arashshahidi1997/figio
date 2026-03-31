# Target Profiles and Journal Submission

Target profiles encode journal-specific requirements — figure width, minimum
font size, resolution, and height limits — so figio can validate your figure
before you submit.

## What target profiles are

A **target profile** is a named set of constraints that your figure must satisfy.
Each profile captures the technical requirements of a specific journal or output
format. When you set a target in your spec and run `figio validate`, figio checks
every constraint and reports which ones pass or fail.

Target profiles are defined either as built-in named profiles or as inline
objects directly in your FigureSpec YAML.

## Built-in profiles

| Profile name | Width | Min font | DPI | Max height | Colorblind check |
|---|---|---|---|---|---|
| `nature_single_column` | 89 mm | 5 pt | 300 | — | yes |
| `nature_double_column` | 183 mm | 5 pt | 300 | — | yes |
| `science_single` | 55 mm | 6 pt | 300 | — | no |
| `science_double` | 117 mm | 6 pt | 300 | — | no |
| `pnas_single` | 87 mm | 6 pt | 300 | — | no |
| `pnas_double` | 178 mm | 6 pt | 300 | — | no |
| `elife` | 140 mm | 7 pt | 300 | 225 mm | yes |
| `plos_one` | 173 mm | 8 pt | 300 | — | yes |
| `cell_single` | 85 mm | 5 pt | 300 | — | no |
| `cell_double` | 174 mm | 5 pt | 300 | — | no |
| `ieee_single` | 88 mm | 8 pt | 300 | — | no |
| `ieee_double` | 181 mm | 8 pt | 300 | — | no |
| `default` | 170 mm | 6 pt | 150 | — | no |

### `nature_single_column`

Single-column figure for Nature-family journals (89 mm wide). Use for figures
that occupy one column in the printed layout.

```yaml
figure:
  id: fig1
  target: nature_single_column
  panels: { ... }
```

### `nature_double_column`

Full-width figure for Nature-family journals (183 mm). Use for figures that span
both columns (e.g., multi-panel figures with many subplots).

```yaml
figure:
  id: fig2
  target: nature_double_column
  panels: { ... }
```

### `science_single` / `science_double`

Single-column (55 mm) and double-column (117 mm) profiles for *Science*. Both
enforce 6 pt minimum font and 300 DPI.

### `pnas_single` / `pnas_double`

Single-column (87 mm) and double-column (178 mm) profiles for *PNAS*. Both
enforce 6 pt minimum font and 300 DPI.

### `elife`

Full-width profile for *eLife* (140 mm). Enforces a 225 mm maximum height and
enables colorblind-safe palette checking per eLife's accessibility guidelines.

### `plos_one`

Full-width profile for *PLOS ONE* (173 mm). Enforces 8 pt minimum font and
enables colorblind checking per PLOS accessibility guidelines.

### `cell_single` / `cell_double`

Single-column (85 mm) and double-column (174 mm) profiles for *Cell*-family
journals. Both enforce 5 pt minimum font and 300 DPI.

### `ieee_single` / `ieee_double`

Single-column (88 mm) and double-column (181 mm) profiles for IEEE publications.
Both enforce 8 pt minimum font and 300 DPI.

### `default`

A permissive baseline for development and internal figures. Lower DPI (150),
wider default width (170 mm), no colorblind check. Useful while iterating before
you know the submission target.

## Inline custom profiles

When no built-in profile matches your target journal, define the profile inline
directly in the YAML. Inline profiles accept the same fields as built-in ones.

```yaml
figure:
  id: fig1
  target:
    name: science_single_column
    figure_width_mm: 57.0
    min_font_pt: 5.0
    dpi: 300
    max_height_mm: 234.0
    colorblind_check: true
  panels: { ... }
```

### Profile fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Human-readable label (used in validation output) |
| `figure_width_mm` | float | Required figure width in millimetres |
| `min_font_pt` | float | Minimum font size in points |
| `dpi` | int | Target resolution for raster export (PDF/PNG) |
| `max_height_mm` | float \| null | Maximum figure height; omit if journal has no limit |
| `colorblind_check` | bool | Whether to check for colorblind-safe palette (not yet implemented) |

## Common journal requirements

Use these specs when defining inline profiles. All widths and heights are in mm;
DPI is for raster export.

| Journal | Single column | Double column | Max height | Min font | DPI |
|---|---|---|---|---|---|
| **Nature** | 89 mm | 183 mm | 247 mm | 5 pt | 300 |
| **Science** | 57 mm | 120 mm | 234 mm | 5 pt | 300 |
| **PNAS** | 87 mm | 178 mm | 231 mm | 6 pt | 300 |
| **eLife** | 83 mm | 170 mm | — | 8 pt | 300 |
| **PLOS ONE** | 82 mm | 168 mm | — | 8 pt | 300 |

> These are representative values based on published author guidelines. Always
> confirm with the current author instructions before final submission, as
> journals update their specifications.

## Validation workflow

### 1. Build the figure

```bash
figio build figurespec.yaml
```

This renders all panels and composes the SVG. The output goes to `output/` by
default.

### 2. Run validation

```bash
figio validate figurespec.yaml --target nature_double_column
```

You can specify a different target on the command line to check against a
profile not set in the spec itself.

### 3. Interpret the output

Each check prints a name, status (`PASS` / `FAIL`), and a message:

```
figure_width       PASS   Figure width 183.0mm matches target 183.0mm
max_height         PASS   Figure height 120.3mm within max 247.0mm
panel_overflow_A   PASS   Panel 'A' fits within figure width
panel_overflow_B   PASS   Panel 'B' fits within figure width
dpi                PASS   Target DPI is 300 (checked at export time)
```

A failing run looks like:

```
figure_width       FAIL   Figure width 170.0mm does not match target 183.0mm
```

### What each check means

| Check | Severity | What it tests |
|---|---|---|
| `figure_width` | error | Actual composed width vs. `figure_width_mm` in the profile (tolerance ±0.5 mm) |
| `max_height` | warning | Composed height vs. `max_height_mm`; only runs if the profile sets a limit |
| `panel_overflow_<id>` | error | Whether each panel's right edge stays within the figure boundary |
| `dpi` | info | Reports the target DPI; actual raster DPI is enforced at export time |

**Errors** indicate a definite constraint violation. **Warnings** are advisory.
The `dpi` check is informational — it confirms the target resolution but cannot
inspect the SVG content for raster images embedded inside panels.

### 4. Fix and rebuild

Common fixes:

- **`figure_width` fails** — the `target` in your spec may not match the target
  you're validating against. Make sure they agree, or explicitly set the width
  via an inline profile.
- **`panel_overflow`** — a panel script is producing SVG wider than the column
  it was allocated. Reduce the panel's content margins or tighten the layout
  `cols` ratio.
- **`max_height` fails** — reduce the number of rows, shrink panel aspect
  ratios, or reduce `panel_gap_mm` in the style block.

### 5. Iterate example

Starting from a default-width figure and targeting `nature_double_column`:

```yaml
# figurespec.yaml — initial, failing
figure:
  id: fig2
  target: default          # 170 mm — wrong for Nature double column
  panels: { ... }
```

```bash
$ figio validate figurespec.yaml --target nature_double_column
figure_width  FAIL  Figure width 170.0mm does not match target 183.0mm
```

Fix: change the target in the spec.

```yaml
# figurespec.yaml — fixed
figure:
  id: fig2
  target: nature_double_column   # 183 mm ✓
  panels: { ... }
```

```bash
$ figio build figurespec.yaml && figio validate figurespec.yaml
figure_width  PASS  Figure width 183.0mm matches target 183.0mm
```

## See also

- [Spec Format Reference](spec-format.md) — full YAML schema including `target` field
- [Multi-Panel Tutorial](tutorial-multipanel.md) — worked example using `nature_double_column`
- [CLI Reference](../reference/cli.md) — `figio validate` options
