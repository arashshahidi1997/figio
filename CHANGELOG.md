# Changelog

## 0.1.0 (2026-03-31)

Initial release — full Phase 1 implementation.

### Added

**Schema & Targets**
- `FigureSpec` Pydantic model with YAML round-trip (flat and wrapped formats)
- Constraint shorthand parsing (`equal_height: [a, b]`)
- JSON Schema generation from Pydantic models
- 13 built-in target profiles: `nature_single_column`, `nature_double_column`, `science_single`, `science_double`, `pnas_single`, `pnas_double`, `elife`, `plos_one`, `cell_single`, `cell_double`, `ieee_single`, `ieee_double`, `default`
- Inline custom target profiles in YAML

**Adapters**
- `MatplotlibAdapter` — function-based (`make_figure()`) and script-based execution
- `ScriptAdapter` — generic SVG-producing scripts with `--output PATH` convention
- SVG normalization: ID prefixing (with `(?<!xlink:)` lookbehind fix), viewBox extraction, boilerplate removal
- `PanelAdapter` protocol and `PanelResult` model with `viewbox` field for original coordinate system

**Composition**
- Grid layout solver with aspect ratio preservation and gap handling
- Nested `<svg>` elements for correct viewBox coordinate mapping (avoids scale transform mismatch between pt and mm coordinate spaces)
- Annotation placement: panel labels, captions, callouts, arrows (with `<marker>` defs), brackets
- Constraints: `equal_height`, `equal_width`, `align_ylabels`, `align_xlabels`, `shared_colorbar` (space reservation)
- Annotation font sizes as bare user units (CairoSVG double-scales `mm`/`pt` CSS units)
- CSS `<style>` scoped to annotation layer only
- Top/bottom margins for panel labels and captions

**Build & Cache**
- SHA-256 content hashing (source + inputs + style)
- File-level caching with automatic invalidation
- Multi-format export: SVG, PDF, PNG via optional CairoSVG

**Validation**
- Figure width check (error, +/-0.5mm tolerance)
- Max height check (warning)
- Panel overflow check (error)
- Min font size check (extracts from panel SVGs, skips annotation layer)
- DPI / PNG dimension check
- Colorblind palette safety (Vienot 1999 deuteranopia simulation, ratio-based detection)

**CLI**
- `figio build` with `--output-dir`, `--panels`, `--force`, `--format`
- `figio validate` with `--target`
- `figio inspect`
- `figio init`

**MCP Tools**
- `figio_figure_list`, `figio_inspect`, `figio_build`, `figio_validate`, `figio_edit_spec` (RFC 7396 merge-patch), `figio_query_output`
- Registered on projio MCP server

**Projio Integration**
- Registered as ecosystem package (`KNOWN_PACKAGES`, `full` profile)
- `agent_instructions()` includes figio tool routing when enabled
- `ecosystem_status()` reports figure count
- `figio-guide` skill for agent discovery

**Documentation**
- Quick start, multi-panel tutorial (with runnable example), spec format reference
- Target profiles and journal submission guide
- Panel adapters guide
- Troubleshooting and FAQ
- CLI and MCP tools reference
- Design spec (`docs/specs/figio-design.md`)
