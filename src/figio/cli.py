"""Command-line interface for figio.

Usage:
    figio build <spec.yaml> [--output-dir DIR] [--panels p1,p2] [--force] [--format svg,pdf,png]
    figio validate <spec.yaml> [--target PROFILE]
    figio inspect <spec.yaml>
    figio init
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def main(argv: list[str] | None = None) -> None:
    """Entry point for the figio CLI."""
    parser = argparse.ArgumentParser(
        prog="figio",
        description="Build orchestrator for reproducible scientific figures",
    )
    sub = parser.add_subparsers(dest="command")

    # --- build ---
    p_build = sub.add_parser("build", help="Build a figure from a spec file")
    p_build.add_argument("spec", type=Path, help="Path to FigureSpec YAML")
    p_build.add_argument("--output-dir", type=Path, default=None)
    p_build.add_argument("--panels", type=str, default="", help="Comma-separated panel IDs")
    p_build.add_argument("--force", action="store_true", help="Bypass cache")
    p_build.add_argument("--format", type=str, default="svg", help="Comma-separated formats: svg,pdf,png")

    # --- validate ---
    p_val = sub.add_parser("validate", help="Validate a spec against a target profile")
    p_val.add_argument("spec", type=Path)
    p_val.add_argument("--target", type=str, default="", help="Override target profile name")

    # --- inspect ---
    p_insp = sub.add_parser("inspect", help="Print spec summary")
    p_insp.add_argument("spec", type=Path)

    # --- init ---
    sub.add_parser("init", help="Scaffold a minimal figurespec.yaml")

    args = parser.parse_args(argv)

    if args.command == "build":
        _cmd_build(args)
    elif args.command == "validate":
        _cmd_validate(args)
    elif args.command == "inspect":
        _cmd_inspect(args)
    elif args.command == "init":
        _cmd_init()
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_build(args: argparse.Namespace) -> None:
    from figio.build import build

    panels = [p.strip() for p in args.panels.split(",") if p.strip()] or None
    formats = [f.strip() for f in args.format.split(",") if f.strip()]

    result = build(
        spec_path=args.spec,
        output_dir=args.output_dir,
        panels=panels,
        force=args.force,
        formats=formats,
    )

    print(f"Built {result.figure_id}")
    print(f"  SVG: {result.output_svg}")
    if result.output_pdf:
        print(f"  PDF: {result.output_pdf}")
    if result.output_png:
        print(f"  PNG: {result.output_png}")
    if result.cached_panels:
        print(f"  Cached: {', '.join(result.cached_panels)}")
    print(f"  Time: {result.elapsed_seconds:.2f}s")

    for check in result.validation:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{status}] {check.name}: {check.message}")


def _cmd_validate(args: argparse.Namespace) -> None:
    from figio.schema import FigureSpec
    from figio.targets import resolve_target
    from figio.validate import validate_figure
    from figio.composer import compose, ComposedFigure
    from figio.adapters import PanelResult

    spec = FigureSpec.from_yaml(args.spec)
    target_name = args.target or spec.target
    target = resolve_target(target_name)

    # Create synthetic panel results for validation
    panels: dict[str, PanelResult] = {}
    for pid, panel_spec in spec.panels.items():
        panels[pid] = PanelResult(
            svg="<svg></svg>",
            bbox_mm=(0, 0, target.figure_width_mm / spec.layout.cols, 30),
        )

    composed = compose(panels, spec.layout, spec.annotations, spec.style, target)
    checks = validate_figure(composed, target)

    all_passed = True
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        if not check.passed:
            all_passed = False
        print(f"[{status}] {check.name}: {check.message}")

    sys.exit(0 if all_passed else 1)


def _cmd_inspect(args: argparse.Namespace) -> None:
    from figio.schema import FigureSpec
    from figio.targets import resolve_target

    spec = FigureSpec.from_yaml(args.spec)

    print(f"Figure: {spec.id}")
    print(f"Target: {spec.target}")
    if isinstance(spec.target, str):
        try:
            target = resolve_target(spec.target)
            print(f"  Width: {target.figure_width_mm}mm, DPI: {target.dpi}, Min font: {target.min_font_pt}pt")
        except KeyError:
            print(f"  (unknown target profile)")

    print(f"Layout: {spec.layout.type.value} {spec.layout.rows}×{spec.layout.cols}")
    if spec.layout.constraints:
        for c in spec.layout.constraints:
            print(f"  Constraint: {c.type.value} → {c.panels}")

    print(f"Panels ({len(spec.panels)}):")
    for pid, panel in spec.panels.items():
        print(f"  {pid}: {panel.generator.value} ← {panel.source}")
        if panel.inputs:
            print(f"    inputs: {panel.inputs}")

    if spec.annotations:
        print(f"Annotations ({len(spec.annotations)}):")
        for ann in spec.annotations:
            print(f"  {ann.type.value}: {ann.text or ann.target}")

    print(f"Style: font={spec.style.font_family}, gap={spec.style.panel_gap_mm}mm")


def _cmd_init() -> None:
    out = Path("figurespec.yaml")
    if out.exists():
        print(f"{out} already exists", file=sys.stderr)
        sys.exit(1)

    template = {
        "figure": {
            "id": "fig_example",
            "target": "default",
            "panels": {
                "panel_a": {
                    "generator": "matplotlib",
                    "source": "panels/panel_a.py",
                    "inputs": [],
                },
            },
            "layout": {
                "type": "grid",
                "rows": 1,
                "cols": 1,
            },
            "annotations": [
                {"type": "panel_label", "target": "panel_a", "text": "A"},
            ],
            "style": {
                "font_family": "Helvetica",
                "panel_gap_mm": 3,
            },
        }
    }
    with open(out, "w") as fh:
        yaml.safe_dump(template, fh, sort_keys=False, default_flow_style=False)
    print(f"Created {out}")


if __name__ == "__main__":
    main()
