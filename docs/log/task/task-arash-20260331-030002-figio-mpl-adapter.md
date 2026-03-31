---
title: "Implement Matplotlib panel adapter with SVG normalization"
date: 2026-03-31
timestamp: 20260331-030002-000002
status: done
actionable: true
project_primary: figio
tags: [task, phase-1]
---
# Implement Matplotlib panel adapter with SVG normalization

## Goal

Implement the panel adapter protocol and the first concrete adapter (Matplotlib). The adapter runs a panel script, captures SVG output, extracts metadata (bounding box, axis positions), and normalizes the SVG for composition.

## Context

Depends on the schema task (FigureSpec models must exist). The adapter contract is defined in the design doc: Input = panel script path + data inputs + style tokens → Output = SVG fragment + metadata envelope.

## Prompt

> Implement the Matplotlib panel adapter for figio. This is a code implementation task.
>
> 1. Read the existing schema models in `src/figio/schema.py` to understand PanelSpec and StyleSpec.
>
> 2. Read the design doc section on Panel Adapters at `/storage2/arash/projects/projio/docs/log/idea/idea-arash-20260331-022337-352248.md`.
>
> 3. Study pipeio's adapter pattern at `packages/pipeio/src/pipeio/adapters/` for structural reference (protocol + concrete adapter).
>
> 4. Create `src/figio/adapters/__init__.py` with the adapter protocol:
>    ```python
>    class PanelResult(BaseModel):
>        svg: str                          # SVG fragment content
>        bbox_mm: tuple[float, float, float, float]  # x, y, width, height in mm
>        anchors: dict[str, tuple[float, float]]      # named anchor points (mm)
>        semantic_ids: list[str]           # element IDs exposed for annotation targeting
>
>    class PanelAdapter(Protocol):
>        def render(self, panel_id: str, spec: PanelSpec, style: StyleSpec,
>                   workdir: Path) -> PanelResult: ...
>        def supported_constraints(self) -> list[str]: ...
>    ```
>
> 5. Create `src/figio/adapters/matplotlib.py`:
>    - `MatplotlibAdapter` implementing `PanelAdapter`
>    - `render()` method:
>      a. Execute the panel source script in a subprocess (or import+call if it exposes a `make_figure()` function)
>      b. Capture the figure via `fig.savefig(buf, format='svg')` into a StringIO buffer
>      c. Extract axis bounding boxes from the figure object (`fig.get_tightbbox()`, `ax.get_position()`)
>      d. Convert positions to mm using figure DPI and size
>      e. Normalize the SVG: strip Matplotlib boilerplate comments, deduplicate IDs by prefixing with panel_id, normalize viewBox to mm units, clean up unnecessary metadata
>    - `supported_constraints()` returns `["equal_height", "equal_width", "align_ylabels", "align_xlabels"]`
>    - SVG normalization helper functions (private):
>      - `_prefix_ids(svg: str, prefix: str) -> str` — prefix all id= and url(#...) references
>      - `_normalize_viewbox(svg: str, width_mm: float, height_mm: float) -> str`
>      - `_strip_mpl_boilerplate(svg: str) -> str` — remove Matplotlib version comments, redundant metadata
>
> 6. Handle the two execution models for panel scripts:
>    - **Function-based**: script has `def make_figure(**kwargs) -> matplotlib.figure.Figure` — import and call
>    - **Script-based**: script uses `plt.savefig()` or similar — run as subprocess, capture output file
>    Document the convention: if source script has a `make_figure` function, figio calls it directly; otherwise runs it as a subprocess.
>
> 7. Apply style tokens: before rendering, set `rcParams` for font_family, font sizes, line widths from StyleSpec. Restore after rendering.
>
> 8. Write tests in `tests/test_adapter_mpl.py`:
>    - Test rendering a simple panel script (create a minimal test fixture: `tests/fixtures/panel_simple.py` with `make_figure()` returning a basic plot)
>    - Test SVG normalization (ID prefixing, viewBox)
>    - Test bounding box extraction
>    - Test style token application
>    - Skip tests if matplotlib not installed (use pytest.importorskip)
>
> 9. Update `pyproject.toml` to add `matplotlib>=3.7` as an optional dependency under `[project.optional-dependencies]`: `mpl = ["matplotlib>=3.7"]`
>
> 10. Run tests to verify.

## Acceptance Criteria

- [ ] PanelAdapter protocol defined
- [ ] MatplotlibAdapter renders SVG from panel scripts
- [ ] SVG normalization (ID prefixing, viewBox, boilerplate removal)
- [ ] Bounding box extraction in mm
- [ ] Style token application via rcParams
- [ ] Tests pass with a real matplotlib render


## Batch Result

- status: done
- batch queue_id: `735c988b6fbb`
- session: `d48ef8e3-1dbb-443a-a603-941c084a0b14`
- batch duration: 1128.7s
