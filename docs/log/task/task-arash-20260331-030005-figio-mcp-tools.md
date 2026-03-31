---
title: "Implement figio MCP tools and projio integration"
date: 2026-03-31
timestamp: 20260331-030005-000005
status: done
actionable: true
project_primary: figio
tags: [task, phase-1]
---
# Implement figio MCP tools and projio integration

## Goal

Expose figio operations as MCP tools through projio's MCP server, following the same pattern as pipeio. This makes figures agent-operable.

## Context

Depends on: all previous figio modules (schema, adapter, composer, build, validate). Two layers:
1. `packages/figio/src/figio/mcp.py` — tool functions (like pipeio/mcp.py)
2. `projio/src/projio/mcp/figio.py` — projio wrapper (like projio/mcp/pipeio.py)
3. Registration in `projio/src/projio/mcp/server.py`

## Prompt

> Implement MCP tools for figio and integrate with projio's MCP server. This is a code implementation task.
>
> 1. Read the MCP tool surface from the design doc at `/storage2/arash/projects/projio/docs/log/idea/idea-arash-20260331-022337-352248.md` — section "MCP server — the agent interface".
>
> 2. Study the pipeio MCP pattern:
>    - `packages/pipeio/src/pipeio/mcp.py` — tool functions that accept `root: Path` and return `dict[str, Any]`
>    - `src/projio/mcp/pipeio.py` — projio wrapper that resolves root path and forwards
>    - `src/projio/mcp/server.py` — `@server.tool()` registrations
>    - `src/projio/mcp/common.py` — shared helpers (`_root()`, error formatting)
>
> 3. Create `src/figio/mcp.py` with tool functions:
>
>    **`mcp_inspect(root: Path, figure_id: str = "") -> dict`**
>    - If figure_id given: load that spec, return panel IDs, layout structure, constraints, annotation list, resolved style tokens, last build status
>    - If no figure_id: scan for all `*.figurespec.yaml` or `figurespec.yaml` files under root, list them
>    - Return structured dict
>
>    **`mcp_build(root: Path, figure_id: str, panels: str = "", force: bool = False) -> dict`**
>    - Find the spec file for figure_id
>    - Call `build()` from build.py
>    - Return: build result summary, validation warnings, output paths, cached panels
>
>    **`mcp_validate(root: Path, figure_id: str, target: str = "") -> dict`**
>    - Load spec, optionally override target profile
>    - Run validation checks
>    - Return pass/fail per check
>
>    **`mcp_edit_spec(root: Path, figure_id: str, patch: dict) -> dict`**
>    - Load spec, apply JSON merge-patch
>    - Validate resulting spec (Pydantic validation)
>    - Save updated YAML
>    - Return updated spec summary + diff description
>
>    **`mcp_query_output(root: Path, figure_id: str, query: str) -> dict`**
>    - Load last build metadata (panel positions, resolved constraints, warnings)
>    - Answer structured queries: "bounding_box of panel X", "font sizes", "all panels", "figure dimensions"
>    - Return structured data
>
>    **`mcp_figure_list(root: Path) -> dict`**
>    - Scan for all figurespec YAML files
>    - Return list with figure_id, path, panel count, last build time
>
>    Helper: `_find_spec(root: Path, figure_id: str) -> Path | None` — locate spec file by figure_id (check `figures/{figure_id}.yaml`, `{figure_id}.figurespec.yaml`, etc.)
>
> 4. Create `src/projio/mcp/figio.py` — projio wrapper layer:
>    - Follow exact pattern from `src/projio/mcp/pipeio.py`
>    - Each function takes the same args as figio.mcp.* but without `root` (resolved via `_root()`)
>    - Docstrings for each tool (these become MCP tool descriptions)
>    - Graceful error handling when figio is not installed
>
> 5. Register tools in `src/projio/mcp/server.py`:
>    - Add `from . import figio as figio_mcp` to imports
>    - Register tools: `figio_inspect`, `figio_build`, `figio_validate`, `figio_edit_spec`, `figio_query_output`, `figio_figure_list`
>    - Follow the exact registration pattern used for pipeio tools
>
> 6. Update `src/projio/mcp/config_gen.py` (if it generates Claude settings) to include `mcp__projio__figio_*` in allowed tool patterns.
>
> 7. Write tests in `packages/figio/tests/test_mcp.py`:
>    - Test mcp_inspect with a fixture spec
>    - Test mcp_build end-to-end (with simple fixture)
>    - Test mcp_validate
>    - Test mcp_edit_spec (apply a patch, verify spec changed)
>    - Test mcp_figure_list (scan)
>
> 8. Run tests in both packages:
>    - `cd packages/figio && make test`
>    - `cd /storage2/arash/projects/projio && make test`

## Acceptance Criteria

- [ ] `figio/mcp.py` with 6 tool functions
- [ ] `projio/mcp/figio.py` wrapper layer
- [ ] Tools registered in `projio/mcp/server.py`
- [ ] Tool permissions in config_gen.py
- [ ] Tests pass for figio MCP tools
- [ ] Projio tests still pass


## Batch Result

- status: done
- batch queue_id: `735c988b6fbb`
- session: `d48ef8e3-1dbb-443a-a603-941c084a0b14`
- batch duration: 1128.7s
