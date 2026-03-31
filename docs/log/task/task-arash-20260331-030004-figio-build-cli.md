---
title: "Implement build engine and CLI with file-level caching"
date: 2026-03-31
timestamp: 20260331-030004-000004
status: done
actionable: true
project_primary: figio
tags: [task, phase-1]
---
# Implement build engine and CLI with file-level caching

## Goal

Implement `figio build` — the CLI entry point that reads a FigureSpec YAML, runs panel adapters, composes the figure, exports outputs, and caches results for incremental rebuilds.

## Context

Depends on: schema, adapter, composer. The build engine orchestrates the full pipeline: parse spec → resolve target → render panels → compose → validate → export. File-level caching: hash inputs (spec + source scripts + data files), skip unchanged panels.

## Prompt

> Implement the figio build engine and CLI. This is a code implementation task.
>
> 1. Read existing modules: `src/figio/schema.py`, `src/figio/adapters/`, `src/figio/composer.py`.
>
> 2. Study pipeio's CLI pattern: `packages/pipeio/src/pipeio/cli.py` (argparse-based).
>
> 3. Create `src/figio/build.py` — the build engine:
>
>    **`BuildResult` model:**
>    - `figure_id: str`
>    - `output_svg: Path`
>    - `output_pdf: Path | None`
>    - `output_png: Path | None`
>    - `panel_results: dict[str, PanelResult]`
>    - `composed: ComposedFigure`
>    - `validation: list[ValidationCheck]`
>    - `cached_panels: list[str]` — panels that were skipped (cache hit)
>    - `elapsed_seconds: float`
>
>    **`build(spec_path: Path, output_dir: Path | None = None, panels: list[str] | None = None, force: bool = False) -> BuildResult`:**
>    a. Load FigureSpec from YAML
>    b. Resolve target profile (from built-in targets or inline)
>    c. Set up output directory (default: same dir as spec, or `_build/`)
>    d. For each panel in spec (or subset if `panels` specified):
>       - Compute content hash of (source script + input files + style tokens)
>       - Check cache: `_build/.cache/{panel_id}.hash` — if match and SVG exists, skip
>       - Otherwise: instantiate adapter for panel.generator, call render()
>       - Store PanelResult SVG to `_build/panels/{panel_id}.svg`
>       - Update cache hash
>    e. Call `compose()` with all panel results
>    f. Write composed SVG to output
>    g. Export derived formats: PDF (via CairoSVG if available), PNG (rasterize at target DPI)
>    h. Run validation checks against target profile
>    i. Return BuildResult
>
>    **Cache implementation** (`src/figio/cache.py`):
>    - `compute_hash(paths: list[Path], extra: str = "") -> str` — SHA256 of file contents + extra string
>    - `check_cache(cache_dir: Path, panel_id: str, current_hash: str) -> bool`
>    - `update_cache(cache_dir: Path, panel_id: str, hash_val: str)`
>    - Cache dir: `{spec_dir}/_build/.cache/`
>
> 4. Create `src/figio/export.py` — format conversion:
>    - `export_pdf(svg_path: Path, output_path: Path)` — use CairoSVG if available, else warn
>    - `export_png(svg_path: Path, output_path: Path, dpi: int)` — use CairoSVG if available
>    - Make CairoSVG an optional dependency
>
> 5. Create `src/figio/validate.py` — validation checks against target profile:
>    - `ValidationCheck` model: name, passed, message, severity (warning/error)
>    - `validate_figure(composed: ComposedFigure, target: TargetProfile) -> list[ValidationCheck]`
>    - Checks: figure_width matches target, font sizes >= min_font_pt, no bounding box overflow, DPI appropriate for target
>
> 6. Create `src/figio/cli.py` — argparse CLI:
>    - `figio build <spec.yaml> [--output-dir DIR] [--panels p1,p2] [--force] [--format svg,pdf,png]`
>    - `figio validate <spec.yaml> [--target PROFILE]`
>    - `figio inspect <spec.yaml>` — print spec summary (panels, layout, target)
>    - `figio init` — scaffold a minimal figurespec.yaml in current directory
>    - Entry point: `figio = "figio.cli:main"` (already declared in pyproject.toml)
>
> 7. Update `pyproject.toml` optional dependencies:
>    - `export = ["cairosvg>=2.7"]`
>    - `all = ["figio[mpl]", "figio[export]"]`
>
> 8. Write tests in `tests/test_build.py`:
>    - Test full build pipeline with a simple 2-panel spec and test fixtures
>    - Test caching: build twice, second time panels should be cached
>    - Test `--force` flag bypasses cache
>    - Test validation output
>    - Test CLI entry point (subprocess or argparse parse_args)
>
> 9. Run `make test` to verify everything passes.

## Acceptance Criteria

- [ ] `build()` orchestrates full pipeline: parse → render → compose → validate → export
- [ ] File-level caching skips unchanged panels
- [ ] SVG export works; PDF/PNG with optional CairoSVG
- [ ] Validation checks against target profile
- [ ] CLI with build/validate/inspect/init subcommands
- [ ] Tests pass


## Batch Result

- status: done
- batch queue_id: `735c988b6fbb`
- session: `d48ef8e3-1dbb-443a-a603-941c084a0b14`
- batch duration: 1128.7s
