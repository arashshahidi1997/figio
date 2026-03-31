# Agent Activity Log

Recent agent session summaries for handoff context.

## 2026-03-31 03:19 | figio | opus | 1 steps

### Blocked by Permissions
- `datalad save` — conda/datalad binary not in PATH for this session
- `projio/src/projio/mcp/server.py` — tool registration (outside figio package dir)
- `projio/CLAUDE.md` — ecosystem table update (outside figio package dir)
- JSON schema generation script execution

Session: `d48ef8e3` | Task: `task-arash-20260331-030001-figio-schema.md`

## 2026-03-31 17:31 | figio | sonnet | 1 steps

- **`docs/guide/tutorial-multipanel.md`** — full tutorial covering: 4 panel scripts, 2×2 grid layout, `equal_height` constraints, all annotation types (panel_label A–D + caption), style tokens, `nature_double_column` target, `--format svg,pdf,png` build, and validate output interpretation
- **`docs/guide/examples/multipanel/`** — 4 runnable panel scripts (`panel_line.py`, `panel_bar.py`, `panel_heatmap.py`, `panel_scatter.py`) plus `figurespec.yaml`
- **`mkdocs.yml`** — added "Multi-Panel Tut...

Session: `a6e9addc` | Task: `task-arash-20260331-172849-038157.md`

## 2026-03-31 17:33 | figio | sonnet | 1 steps

- **`mkdocs.yml`** — added `Target Profiles: guide/targets.md` to the Guide nav section
- **`docs/index.md`** — added link to the new guide

Session: `dde3278d` | Task: `task-arash-20260331-172854-763682.md`

## 2026-03-31 17:35 | figio | sonnet | 1 steps

Done. Created `docs/guide/troubleshooting.md` with all 8 FAQ entries from the issue, added it to the `mkdocs.yml` nav under Guide, and linked it from `docs/index.md`.

Session: `46b95142` | Task: `task-arash-20260331-172900-393704.md`

## 2026-03-31 17:37 | figio | sonnet | 1 steps

**`docs/guide/spec-format.md`** — Updated the quick-reference built-in profiles table.

Session: `ac734f75` | Task: `task-arash-20260331-172938-128022.md`

## 2026-03-31 17:43 | figio | sonnet | 1 steps

**Modified files:**
- `src/figio/svg_utils.py` — added `extract_viewbox()`, `prefix_ids()`, `normalize_viewbox()` as shared public functions
- `src/figio/adapters/matplotlib.py` — removed duplicate private SVG functions, now imports from `svg_utils`; removed unused `subprocess`/`tempfile` imports
- `src/figio/build.py` — registered `Generator.script` → `ScriptAdapter` in `_get_adapter()`
- `tests/test_adapter_mpl.py` — updated imports to use `svg_utils` for the now-shared functions
- `docs/gu...

Session: `98301022` | Task: `task-arash-20260331-172948-434360.md`

## 2026-03-31 17:48 | figio | opus | 1 steps

**`tests/test_validate.py`** — 20 tests covering:
- Font size parsing (pt, px, bare numbers)
- Font size extraction from inline attributes, style attributes, and `<style>` blocks
- Min font size pass/fail with synthetic SVGs
- PNG dimension check with fake PNG files (correct, wrong, missing)
- Color extraction from SVG
- Colorblind check: red/green fails, blue/orange passes
- Integration tests verifying `validate_figure` includes all new checks

Session: `7278ca5e` | Task: `task-arash-20260331-172919-271700.md`

## 2026-03-31 17:51 | figio | opus | 1 steps

Added 5 new tests:
- `test_arrow_annotation_has_marker_def` — arrow produces both `<line>` and `<marker>` def
- `test_no_marker_def_without_arrows` — no marker when no arrows
- `test_bracket_annotation_shape` — bracket has 3+ L segments and text label
- `test_bracket_no_text` — bracket without text still renders the shape
- `test_shared_colorbar_reserves_space` — panels shrink, `__colorbar` BBox exists, warning emitted

Session: `e5f923f8` | Task: `task-arash-20260331-172930-507969.md`

## 2026-03-31 17:56 | figio | opus | 1 steps

1. **`test_single_panel_nature`** — single matplotlib panel, `nature_single_column` target (89mm width), panel label "A", validation passes
2. **`test_two_panel_comparison`** — 1x2 grid with `equal_height` constraint, labels A/B, caption annotation
3. **`test_four_panel_grid`** — 2x2 grid, per-row `equal_height`, `nature_double_column` target (183mm), all labels
4. **`test_cache_roundtrip`** — builds, verifies caching, modifies one panel, confirms only that panel re-renders, then `--force` by...

Session: `fa11aa47` | Task: `task-arash-20260331-172959-940471.md`
