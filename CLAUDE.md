# figio

## What figio Is

figio is a declarative build orchestrator for reproducible scientific figures. It coordinates existing plotting libraries (Matplotlib, Vega-Lite, etc.) through a YAML manifest (FigureSpec) that describes panels, layout, annotations, and style tokens — then assembles them into a single, validated SVG suitable for journal submission.

figio is an **orchestration system**, not a rendering engine. Panels are opaque — figio doesn't reach inside them. It coordinates their output into a composed figure with validated positioning, annotations, and journal compliance checks.

## Architecture

```
FigureSpec (YAML) → Adapters → Panel SVGs → Composer → Composed SVG → Export (PDF/PNG)
```

| Layer | Module | Responsibility |
|-------|--------|---------------|
| Schema | `schema.py` | Pydantic models: FigureSpec, PanelSpec, LayoutSpec, AnnotationSpec, StyleSpec, TargetProfile |
| Targets | `targets.py` | Built-in journal profiles (Nature, default), target resolution |
| Adapters | `adapters/` | Protocol + backends: `matplotlib.py` renders panels via Matplotlib |
| Composer | `composer.py` | Grid solver, constraint application, SVG assembly, annotation placement |
| SVG Utils | `svg_utils.py` | Defs merging, content extraction, document building, style injection |
| Build | `build.py` | Orchestrates render → compose → export pipeline with file-level caching |
| Cache | `cache.py` | SHA-256 content hashing, cache check/update |
| Validate | `validate.py` | Checks against target profile (width, height, font size, overflow) |
| Export | `export.py` | SVG → PDF/PNG via CairoSVG (optional dependency) |
| CLI | `cli.py` | `figio build/validate/inspect/init` commands |
| MCP | `mcp.py` | Tool functions for projio MCP server integration |

## Source Layout

- `src/figio/schema.py` — FigureSpec Pydantic models, YAML round-trip
- `src/figio/targets.py` — Built-in target profiles, `resolve_target()`
- `src/figio/adapters/__init__.py` — `PanelResult`, `PanelAdapter` protocol
- `src/figio/adapters/matplotlib.py` — Matplotlib adapter with SVG normalization
- `src/figio/composer.py` — SVG composition engine: grid solver, annotations, constraints
- `src/figio/svg_utils.py` — SVG manipulation helpers (stdlib xml.etree)
- `src/figio/build.py` — Build engine with caching
- `src/figio/cache.py` — Content hash caching
- `src/figio/validate.py` — Target profile validation
- `src/figio/export.py` — PDF/PNG export via CairoSVG
- `src/figio/cli.py` — argparse CLI entry point
- `src/figio/mcp.py` — MCP tool functions (called by projio wrapper)
- `src/figio/figurespec.schema.json` — JSON Schema (generated from Pydantic)

## CLI Surface

```bash
figio build <spec.yaml> [--output-dir DIR] [--panels p1,p2] [--force] [--format svg,pdf,png]
figio validate <spec.yaml> [--target PROFILE]
figio inspect <spec.yaml>
figio init
```

## MCP Tool Surface

| Intent | MCP tool |
|--------|----------|
| List all figures | `figio_figure_list()` |
| Inspect a figure | `figio_inspect(figure_id)` |
| Build a figure | `figio_build(figure_id, panels, force)` |
| Validate against target | `figio_validate(figure_id, target)` |
| Edit spec via merge-patch | `figio_edit_spec(figure_id, patch)` |
| Query build output | `figio_query_output(figure_id, query)` |

## Build & Test

```bash
make test     # run pytest
make build    # build wheel
make clean    # remove artifacts
```

Single test: `PYTHONPATH=src python -m pytest tests/test_schema.py -q`

## Projio workspace

This project uses **projio** — a project-centric research assistance ecosystem.
All project knowledge (papers, notes, code libraries, search indexes) is managed
through MCP tools. **Always use MCP tools instead of direct file manipulation**
for projio-managed resources.

**Tool preference:** When an MCP tool exists for an operation, always prefer it
over the Bash equivalent — even for simple commands like `git status` or
`datalad status`. MCP tools return structured output and resolve environment
variables (Python paths, conda envs) that differ from the MCP server's own env.
Only fall back to Bash when no MCP tool covers the operation.

At the start of a session, call `project_context()` to understand the workspace
and `runtime_conventions()` to see available Makefile targets.

## Agent tool routing

| Intent | MCP tool | Do NOT |
|--------|----------|--------|
| Understand the project | `project_context()` | Read config files directly |
| See available commands | `runtime_conventions()` | Parse the Makefile manually |
| Search project knowledge | `rag_query(query)` | Grep through docs manually |
| Multi-facet search | `rag_query_multi(queries)` | Run multiple greps |
| Check indexed sources | `corpus_list()` | Inspect Chroma store directly |
| Rebuild search index | `indexio_build()` | Run `indexio build` in terminal |
| Check indexed sources | `indexio_sources_list()` | Inspect config files directly |
| Sync all subsystem sources | `indexio_sources_sync(build=True)` | Run sync commands manually |
| Ingest papers by DOI | `biblio_ingest(dois)` | Write BibTeX by hand |
| Look up a paper | `citekey_resolve(citekeys)` | Read .bib files directly |
| Get full paper context | `paper_context(citekey)` | Read docling/GROBID outputs directly |
| Find unresolved refs | `paper_absent_refs(citekey)` | Parse references.json manually |
| Check paper status | `library_get(citekey)` | Read library.yml directly |
| Update paper status | `biblio_library_set(citekeys)` | Edit library.yml directly |
| Merge bibliography | `biblio_merge()` | Run `biblio merge` in terminal |
| Extract full text | `biblio_docling(citekey)` | Run `biblio docling` in terminal |
| Extract references | `biblio_grobid(citekey)` | Run `biblio grobid` in terminal |
| Check GROBID server | `biblio_grobid_check()` | Curl the GROBID API manually |
| Sync biblio sources to index | `biblio_rag_sync()` | Run `biblio rag sync` in terminal |
| Create a note/task/idea | `note_create(note_type)` | Create markdown files directly |
| List recent notes | `note_list()` | List files in notes/ directory |
| Read a note | `note_read(path)` | Read the file directly |
| Find note by ID/timestamp | `note_resolve(note_id)` | Grep filenames or semantic search |
| Search notes | `note_search(query)` | Grep through notes/ |
| Update note metadata | `note_update(path, fields)` | Edit frontmatter directly |
| See note types | `note_types()` | Read notio.toml directly |
| Rebuild note indexes | `notio_reindex(note_type?)` | Regenerate index.md manually |
| Add a library | `codio_add_urls(urls)` | Edit YAML registry files |
| Find libraries by capability | `codio_discover(query)` | Grep catalog.yml |
| Inspect a library | `codio_get(name)` | Read catalog + profiles manually |
| List all libraries | `codio_list()` | Parse registry files directly |
| Check registry vocabulary | `codio_vocab()` | Read schema docs |
| Validate registry | `codio_validate()` | Run consistency checks manually |
| Register a library | `codio_add(name, kind)` | Edit YAML registry files |
| Sync codio sources to index | `codio_rag_sync()` | Run `codio rag sync` in terminal |
| List figures | `figio_figure_list()` | Scan for YAML files manually |
| Inspect a figure | `figio_inspect(figure_id)` | Read spec files directly |
| Build a figure | `figio_build(figure_id)` | Run `figio build` in terminal |
| Validate a figure | `figio_validate(figure_id)` | Run `figio validate` in terminal |
| Edit a figure spec | `figio_edit_spec(figure_id, patch)` | Edit YAML directly |
| Query build output | `figio_query_output(figure_id, query)` | Parse SVG directly |
| Build doc site | `site_build()` | Run `make docs` or `mkdocs build` |
| Deploy to pages | `site_deploy(target)` | Run `make deploy` or push manually |
| Check git status | `git_status()` | Run `git status` in Bash |
| Save dataset changes | `datalad_save(message)` | Run `make save` or `datalad save` |
| Check dataset status | `datalad_status()` | Run `make status` or `datalad status` |
| Push to sibling | `datalad_push(sibling)` | Run `make push` or `datalad push` |
| Pull from sibling | `datalad_pull(sibling)` | Run `make pull` or `datalad update` |
| List siblings | `datalad_siblings()` | Run `datalad siblings` manually |

## Workflow conventions

1. **Search first** — check existing knowledge before creating new content
2. **Ingest pipeline** — after `biblio_ingest`, run `biblio_merge` → `biblio_docling` → `biblio_grobid` → `indexio_build`
3. **Record decisions** — create notes to capture analysis and decisions

## Cross-project dispatch

When filing observations for another project via worklog MCP:

**Model selection:** haiku (trivial/typo) · sonnet (single-module, clear scope) · opus (default, multi-package, architectural)

**Dispatch decision:**
- Well-scoped bug with clear fix → `worklog_note(text, project_id, kind="issue", auto_dispatch=True, model="sonnet")`
- Complex/architectural issue → `worklog_note(text, project_id, kind="issue", auto_dispatch=True)` (opus is default)
- Observation, no immediate action → `worklog_note(text, project_id)` (no auto_dispatch)
- Need result now → `run_prompt(project, prompt)` (synchronous)

Queue timeout is 30 minutes. Use `tail_task(queue_id)` to monitor running tasks.
Use `note_resolve(note_id)` to find notes by timestamp/capture ID.

**Task promotion:** `promote_to_task` only uses LLM enrichment for voice captures.
Agent-written notes get a template prompt pointing at the source — no LLM call needed.

## Development

```bash
make         # see available targets
make save    # datalad save
make push    # datalad push
```

Agents should prefer the MCP tools `datalad_save()`, `datalad_push()`, `datalad_pull()`,
and `datalad_status()` over running make/datalad commands directly.
