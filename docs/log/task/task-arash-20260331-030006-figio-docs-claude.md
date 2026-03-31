---
title: "Set up figio documentation and update CLAUDE.md"
date: 2026-03-31
timestamp: 20260331-030006-000006
status: done
actionable: true
project_primary: figio
tags: [task, phase-1]
---
# Set up figio documentation and update CLAUDE.md

## Goal

Set up the documentation structure for figio and update CLAUDE.md files so agents can work with the package effectively.

## Context

Figio is scaffolded with a minimal `mkdocs.yml` and `docs/index.md`. Needs proper documentation structure following the pattern of other projio packages (biblio, pipeio). Also needs CLAUDE.md updates in both figio and projio.

## Prompt

> Set up figio documentation and update CLAUDE.md files. This is a documentation task.
>
> 1. Read the current state:
>    - `packages/figio/mkdocs.yml` — minimal scaffold
>    - `packages/figio/docs/index.md` — placeholder
>    - `packages/figio/CLAUDE.md` — generic projio scaffold
>
> 2. Study documentation patterns from pipeio:
>    - `packages/pipeio/mkdocs.yml`
>    - `packages/pipeio/docs/` directory structure
>    - `packages/pipeio/CLAUDE.md`
>
> 3. Study projio's main CLAUDE.md at `/storage2/arash/projects/projio/CLAUDE.md` — see how pipeio is documented there.
>
> 4. Update `packages/figio/docs/index.md` with:
>    - One-paragraph description of figio
>    - Quick start example (write a spec, run `figio build`)
>    - Link to architecture and API reference sections
>
> 5. Create documentation pages:
>    - `docs/guide/quickstart.md` — step-by-step: install, write first spec, build, validate
>    - `docs/guide/spec-format.md` — complete YAML reference with all fields documented, examples for each section (panels, layout, annotations, style, targets)
>    - `docs/guide/adapters.md` — how panel adapters work, writing panel scripts for matplotlib, the `make_figure()` convention
>    - `docs/reference/` — keep the existing reference dir, add `docs/reference/cli.md` documenting all CLI commands
>    - `docs/reference/mcp-tools.md` — document all 6 MCP tools with examples
>
> 6. Update `packages/figio/mkdocs.yml` with proper nav structure pointing to all docs.
>
> 7. Update `packages/figio/CLAUDE.md`:
>    - Replace the generic projio scaffold with figio-specific content
>    - Add "What figio Is" section (like pipeio's CLAUDE.md)
>    - Add Architecture section: schema → adapters → composer → build → export → MCP
>    - Add source layout section
>    - Add CLI surface section
>    - Add MCP tool surface section with the tool routing table
>    - Add build & test commands
>    - Keep the existing projio workspace and agent tool routing sections
>
> 8. Update projio's main CLAUDE.md at `/storage2/arash/projects/projio/CLAUDE.md`:
>    - Add figio to the Ecosystem Components table: `**figio** | figures | Figure orchestration, SVG composition, panel adapters, journal validation`
>    - Add `mcp/figio.py` to the MCP Server section listing figio tools
>    - Add figio tool entries to the tool list
>
> 9. Verify docs build: `cd packages/figio && mkdocs build --strict` (if mkdocs is available)

## Acceptance Criteria

- [ ] `docs/index.md` has proper content
- [ ] Guide pages created (quickstart, spec-format, adapters)
- [ ] Reference pages created (cli, mcp-tools)
- [ ] `mkdocs.yml` nav updated
- [ ] figio `CLAUDE.md` has architecture, source layout, CLI, MCP tools
- [ ] projio `CLAUDE.md` updated with figio in ecosystem table and MCP listing


## Batch Result

- status: done
- batch queue_id: `735c988b6fbb`
- session: `d48ef8e3-1dbb-443a-a603-941c084a0b14`
- batch duration: 1128.7s
