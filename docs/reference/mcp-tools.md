# MCP Tools Reference

figio exposes 6 MCP tools through the projio MCP server for agent-driven figure operations.

## `figio_figure_list`

List all figurespec YAML files in the project.

**Returns:** figure IDs, paths, panel counts, build status.

## `figio_inspect`

Inspect a figure's structure.

**Args:**
- `figure_id` (str, optional) — figure to inspect; if empty, lists all figures.

**Returns:** panel IDs and generators, layout structure, constraints, annotations, resolved style tokens.

**Example use:** orient before making changes to a spec.

## `figio_build`

Build a figure from its spec.

**Args:**
- `figure_id` (str) — figure to build
- `panels` (str, optional) — comma-separated panel subset
- `force` (bool, optional) — bypass cache

**Returns:** output paths (SVG, PDF, PNG), validation checks, cached panels, elapsed time.

## `figio_validate`

Validate a figure spec against a target profile.

**Args:**
- `figure_id` (str) — figure to validate
- `target` (str, optional) — override target profile name

**Returns:** per-check pass/fail results, all_passed flag.

## `figio_edit_spec`

Apply a JSON merge-patch to a figure spec.

**Args:**
- `figure_id` (str) — figure to edit
- `patch` (dict) — RFC 7396 merge-patch object

**Returns:** confirmation, diff description.

**Example patches:**
```json
{"panels": {"psd": {"source": "panels/psd_v2.py"}}}
{"layout": {"constraints": [{"equal_height": ["psd", "topo"]}]}}
{"style": {"font_family": "Arial"}}
```

## `figio_query_output`

Query structured data from the last build.

**Args:**
- `figure_id` (str) — figure to query
- `query` (str) — e.g., "bounding_box of panel psd", "dimensions", "all panels"

**Returns:** structured data from build metadata.

## Agent Workflow

1. `figio_inspect` — understand current figure state
2. `figio_edit_spec` — apply a change
3. `figio_build` — recompile
4. `figio_validate` — check against target
5. `figio_query_output` — verify results
