# CLI Reference

## `figio build`

Build a figure from a FigureSpec YAML file.

```bash
figio build <spec.yaml> [--output-dir DIR] [--panels p1,p2] [--force] [--format svg,pdf,png]
```

| Option | Description |
|--------|-------------|
| `spec.yaml` | Path to FigureSpec YAML file |
| `--output-dir` | Output directory (default: `_build/` next to spec) |
| `--panels` | Comma-separated panel IDs to render (default: all) |
| `--force` | Bypass cache, re-render all panels |
| `--format` | Comma-separated output formats: `svg`, `pdf`, `png` (default: `svg`) |

## `figio validate`

Validate a spec against a target profile.

```bash
figio validate <spec.yaml> [--target PROFILE]
```

| Option | Description |
|--------|-------------|
| `spec.yaml` | Path to FigureSpec YAML file |
| `--target` | Override target profile name (default: spec's target) |

## `figio inspect`

Print a summary of a FigureSpec.

```bash
figio inspect <spec.yaml>
```

Shows: figure ID, target profile, layout structure, panels with generators and sources, annotations, and style tokens.

## `figio init`

Scaffold a minimal `figurespec.yaml` in the current directory.

```bash
figio init
```

Creates a template spec with one panel, grid layout, and default target.
