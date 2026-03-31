"""MCP tool functions for figio.

Each function accepts a ``root: Path`` (the project root) and returns a
plain dict suitable for JSON serialization. These are called by the projio
MCP wrapper layer (``projio.mcp.figio``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def mcp_figure_list(root: Path) -> dict[str, Any]:
    """Scan for all figurespec YAML files under root."""
    specs: list[dict[str, Any]] = []
    for pattern in ["**/*.figurespec.yaml", "**/figurespec.yaml"]:
        for p in root.glob(pattern):
            if "_build" in p.parts:
                continue
            try:
                from figio.schema import FigureSpec
                spec = FigureSpec.from_yaml(p)
                # Check for last build
                build_dir = p.parent / "_build"
                svg_path = build_dir / f"{spec.id}.svg"
                specs.append({
                    "figure_id": spec.id,
                    "path": str(p.relative_to(root)),
                    "panel_count": len(spec.panels),
                    "last_built": svg_path.exists(),
                })
            except Exception as exc:
                specs.append({
                    "path": str(p.relative_to(root)),
                    "error": str(exc),
                })
    return {"figures": specs, "count": len(specs)}


def mcp_inspect(root: Path, figure_id: str = "") -> dict[str, Any]:
    """Inspect a figure spec or list all specs if no figure_id given."""
    if not figure_id:
        return mcp_figure_list(root)

    spec_path = _find_spec(root, figure_id)
    if spec_path is None:
        return {"error": f"No spec found for figure_id={figure_id!r}"}

    from figio.schema import FigureSpec
    from figio.targets import resolve_target

    spec = FigureSpec.from_yaml(spec_path)

    # Resolve target
    target_info: dict[str, Any] = {}
    try:
        target = resolve_target(spec.target)
        target_info = target.model_dump()
    except (KeyError, Exception):
        target_info = {"ref": str(spec.target)}

    return {
        "figure_id": spec.id,
        "path": str(spec_path.relative_to(root)),
        "target": target_info,
        "panels": {
            pid: {
                "generator": p.generator.value,
                "source": p.source,
                "inputs": p.inputs,
            }
            for pid, p in spec.panels.items()
        },
        "layout": {
            "type": spec.layout.type.value,
            "rows": spec.layout.rows,
            "cols": spec.layout.cols,
            "constraints": [
                {"type": c.type.value, "panels": c.panels}
                for c in spec.layout.constraints
            ],
        },
        "annotations": [
            {"type": a.type.value, "target": a.target, "text": a.text}
            for a in spec.annotations
        ],
        "style": spec.style.model_dump(),
    }


def mcp_build(
    root: Path,
    figure_id: str,
    panels: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """Build a figure from its spec."""
    spec_path = _find_spec(root, figure_id)
    if spec_path is None:
        return {"error": f"No spec found for figure_id={figure_id!r}"}

    from figio.build import build

    panel_list = [p.strip() for p in panels.split(",") if p.strip()] or None

    try:
        result = build(
            spec_path=spec_path,
            panels=panel_list,
            force=force,
        )
        return {
            "figure_id": result.figure_id,
            "output_svg": result.output_svg,
            "output_pdf": result.output_pdf,
            "output_png": result.output_png,
            "cached_panels": result.cached_panels,
            "elapsed_seconds": result.elapsed_seconds,
            "validation": [
                {"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity}
                for c in result.validation
            ],
            "warnings": result.composed.warnings if result.composed else [],
        }
    except Exception as exc:
        return {"error": str(exc)}


def mcp_validate(
    root: Path,
    figure_id: str,
    target: str = "",
) -> dict[str, Any]:
    """Validate a figure spec against a target profile."""
    spec_path = _find_spec(root, figure_id)
    if spec_path is None:
        return {"error": f"No spec found for figure_id={figure_id!r}"}

    from figio.schema import FigureSpec
    from figio.targets import resolve_target
    from figio.validate import validate_figure
    from figio.composer import compose
    from figio.adapters import PanelResult

    spec = FigureSpec.from_yaml(spec_path)
    target_profile = resolve_target(target or spec.target)

    # Create synthetic panels for validation
    panel_results: dict[str, PanelResult] = {}
    for pid in spec.panels:
        panel_results[pid] = PanelResult(
            svg="<svg></svg>",
            bbox_mm=(0, 0, target_profile.figure_width_mm / max(spec.layout.cols, 1), 30),
        )

    composed = compose(
        panel_results, spec.layout, spec.annotations, spec.style, target_profile
    )
    checks = validate_figure(composed, target_profile)

    return {
        "figure_id": spec.id,
        "target": target_profile.model_dump(),
        "checks": [
            {"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity}
            for c in checks
        ],
        "all_passed": all(c.passed for c in checks),
    }


def mcp_edit_spec(
    root: Path,
    figure_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    """Apply a JSON merge-patch to a figure spec."""
    spec_path = _find_spec(root, figure_id)
    if spec_path is None:
        return {"error": f"No spec found for figure_id={figure_id!r}"}

    # Load raw YAML
    with open(spec_path) as f:
        raw = yaml.safe_load(f) or {}

    # Unwrap figure: wrapper if present
    if "figure" in raw and isinstance(raw["figure"], dict):
        data = raw["figure"]
        wrapped = True
    else:
        data = raw
        wrapped = False

    # Apply merge-patch
    _merge_patch(data, patch)

    # Validate
    from figio.schema import FigureSpec, _parse_constraints
    if "layout" in data and "constraints" in data["layout"]:
        data["layout"]["constraints"] = _parse_constraints(data["layout"]["constraints"])

    try:
        spec = FigureSpec.model_validate(data)
    except Exception as exc:
        return {"error": f"Validation failed after patch: {exc}"}

    # Save
    if wrapped:
        raw["figure"] = data
    else:
        raw = data
    with open(spec_path, "w") as f:
        yaml.safe_dump(raw, f, sort_keys=False, default_flow_style=False)

    return {
        "figure_id": spec.id,
        "path": str(spec_path.relative_to(root)),
        "updated": True,
        "patch_applied": patch,
    }


def mcp_query_output(
    root: Path,
    figure_id: str,
    query: str,
) -> dict[str, Any]:
    """Answer structured queries about the last build's output."""
    spec_path = _find_spec(root, figure_id)
    if spec_path is None:
        return {"error": f"No spec found for figure_id={figure_id!r}"}

    build_dir = spec_path.parent / "_build"
    from figio.schema import FigureSpec
    spec = FigureSpec.from_yaml(spec_path)
    svg_path = build_dir / f"{spec.id}.svg"

    if not svg_path.exists():
        return {"error": "No build output found. Run figio_build first."}

    q = query.lower().strip()

    if "bounding_box" in q or "bbox" in q:
        # Try to extract panel name
        for pid in spec.panels:
            if pid in q:
                panel_svg = build_dir / "panels" / f"{pid}.svg"
                return {
                    "panel_id": pid,
                    "panel_svg_exists": panel_svg.exists(),
                    "query": query,
                }
        return {"panels": list(spec.panels.keys()), "query": query}

    elif "dimension" in q or "size" in q:
        return {
            "figure_id": spec.id,
            "svg_path": str(svg_path),
            "svg_size_bytes": svg_path.stat().st_size,
        }

    elif "panel" in q or "all" in q:
        return {"panels": list(spec.panels.keys())}

    return {"query": query, "hint": "Try: bounding_box, dimensions, panels"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_spec(root: Path, figure_id: str) -> Path | None:
    """Locate a figurespec file by figure_id."""
    candidates = [
        root / f"{figure_id}.figurespec.yaml",
        root / f"{figure_id}.yaml",
        root / "figures" / f"{figure_id}.yaml",
        root / "figures" / f"{figure_id}.figurespec.yaml",
        root / "figurespec.yaml",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Scan for matching figure ID in YAML files
    for pattern in ["**/*.figurespec.yaml", "**/figurespec.yaml"]:
        for p in root.glob(pattern):
            if "_build" in p.parts:
                continue
            try:
                with open(p) as f:
                    raw = yaml.safe_load(f) or {}
                data = raw.get("figure", raw)
                if data.get("id") == figure_id:
                    return p
            except Exception:
                continue
    return None


def _merge_patch(target: dict, patch: dict) -> None:
    """Apply RFC 7396 JSON Merge Patch in-place."""
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_patch(target[key], value)
        elif value is None:
            target.pop(key, None)
        else:
            target[key] = value
