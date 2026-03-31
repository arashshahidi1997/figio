---
title: "Define FigureSpec YAML schema and Pydantic models"
date: 2026-03-31
timestamp: 20260331-030001-000001
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260331-031920-771846/note.md
completed: 2026-03-31T03:19:22+02:00
actionable: true
project_primary: figio
tags: [task, phase-1]
---
# Define FigureSpec YAML schema and Pydantic models

## Goal

Define the core data model for figio: the FigureSpec YAML schema and corresponding Pydantic models. This is the foundation everything else builds on.

## Context

FigureSpec is a declarative orchestration layer for scientific figures. The YAML manifest is the single source of truth. See the design doc in projio at `docs/log/idea/idea-arash-20260331-022337-352248.md`.

The figio package is scaffolded at `packages/figio/` with an empty `src/figio/__init__.py`. Follow the same patterns as pipeio (`packages/pipeio/`) — Pydantic models, src-layout, etc.

## Prompt

> Implement the FigureSpec data model for figio. This is a code implementation task.
>
> 1. Read the design doc at `/storage2/arash/projects/projio/docs/log/idea/idea-arash-20260331-022337-352248.md` — focus on the YAML schema example and the architecture sections (FigureSpec manifest, Panel adapters contract, Annotations, Style tokens, Targets).
>
> 2. Study how pipeio defines its models:
>    - `packages/pipeio/src/pipeio/config.py` — FlowConfig Pydantic model
>    - `packages/pipeio/src/pipeio/registry.py` — PipelineRegistry, FlowEntry, ModEntry
>    - `packages/pipeio/src/pipeio/__init__.py` — public API exports
>
> 3. Create `src/figio/schema.py` with Pydantic models:
>    - `PanelSpec` — generator backend (enum: matplotlib, vega, mermaid, graphviz, script), source script path, input file list, optional output anchors/semantic IDs
>    - `LayoutConstraint` — typed constraints (equal_height, align_ylabels, shared_colorbar, align_xlabels, equal_width) as a discriminated union or simple typed dict
>    - `LayoutSpec` — type (grid, mosaic), rows, cols, optional mosaic pattern string, list of constraints
>    - `AnnotationSpec` — type enum (panel_label, callout, arrow, bracket, caption), target panel ID, text, optional position offset
>    - `StyleSpec` — font_family, font_size_pt (optional), panel_gap_mm, line_weight, color_roles dict
>    - `TargetProfile` — name (e.g. "nature_single_column"), figure_width_mm, min_font_pt, dpi, max_height_mm (optional), colorblind_check bool
>    - `FigureSpec` — top-level model: id, target (str ref or inline TargetProfile), panels dict[str, PanelSpec], layout LayoutSpec, annotations list[AnnotationSpec], style StyleSpec
>
> 4. Add a `FigureSpec.from_yaml(path)` classmethod and `to_yaml(path)` method (use PyYAML or ruamel.yaml, whichever pipeio uses).
>
> 5. Create `src/figio/targets.py` with built-in target profiles:
>    - `nature_single_column` — width=89mm, min_font=5pt, dpi=300
>    - `nature_double_column` — width=183mm, min_font=5pt, dpi=300
>    - `default` — width=170mm, min_font=6pt, dpi=150
>    Store as a dict of TargetProfile instances. Add a `resolve_target(name_or_profile)` function.
>
> 6. Create a JSON Schema file at `src/figio/figurespec.schema.json` generated from the Pydantic model (use `FigureSpec.model_json_schema()`). Add a small script or test that regenerates it.
>
> 7. Update `src/figio/__init__.py` to export the public API: FigureSpec, PanelSpec, LayoutSpec, AnnotationSpec, StyleSpec, TargetProfile.
>
> 8. Update `pyproject.toml`:
>    - Add dependencies: `pydantic>=2.0`, `pyyaml>=6.0`
>    - Add `project.scripts` entry: `figio = "figio.cli:main"` (cli.py doesn't exist yet, just declare the entry point)
>    - Fill in description: "Build orchestrator for reproducible scientific figures"
>    - Fill in author
>
> 9. Write tests in `tests/test_schema.py`:
>    - Test round-trip: create FigureSpec programmatically → to_yaml → from_yaml → assert equal
>    - Test the example YAML from the design doc parses correctly
>    - Test target resolution (by name and inline)
>    - Test validation errors for invalid specs (missing required fields, unknown generator, etc.)
>
> 10. Run `make test` to verify everything passes.

## Acceptance Criteria

- [ ] Pydantic models defined in `src/figio/schema.py`
- [ ] Built-in target profiles in `src/figio/targets.py`
- [ ] YAML round-trip works
- [ ] JSON Schema generated
- [ ] `__init__.py` exports public API
- [ ] `pyproject.toml` updated with dependencies and entry point
- [ ] Tests pass


## Batch Result

- status: done
- batch queue_id: `735c988b6fbb`
- session: `d48ef8e3-1dbb-443a-a603-941c084a0b14`
- batch duration: 1128.7s
