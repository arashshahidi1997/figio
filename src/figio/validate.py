"""Validation checks against target profile constraints."""

from __future__ import annotations

from pydantic import BaseModel

from figio.composer import ComposedFigure
from figio.schema import TargetProfile


class ValidationCheck(BaseModel):
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    severity: str = "warning"  # "warning" or "error"


def validate_figure(
    composed: ComposedFigure,
    target: TargetProfile,
) -> list[ValidationCheck]:
    """Run validation checks against a target profile.

    Returns a list of checks with pass/fail status.
    """
    checks: list[ValidationCheck] = []

    # Width check
    checks.append(ValidationCheck(
        name="figure_width",
        passed=abs(composed.width_mm - target.figure_width_mm) < 0.5,
        message=(
            f"Figure width {composed.width_mm:.1f}mm "
            f"{'matches' if abs(composed.width_mm - target.figure_width_mm) < 0.5 else 'does not match'} "
            f"target {target.figure_width_mm:.1f}mm"
        ),
        severity="error",
    ))

    # Max height check
    if target.max_height_mm:
        over = composed.height_mm > target.max_height_mm
        checks.append(ValidationCheck(
            name="max_height",
            passed=not over,
            message=(
                f"Figure height {composed.height_mm:.1f}mm "
                f"{'exceeds' if over else 'within'} "
                f"max {target.max_height_mm:.1f}mm"
            ),
            severity="warning",
        ))

    # Panel overflow check
    for panel_id, pos in composed.panel_positions.items():
        overflow = pos.x + pos.width > composed.width_mm + 0.1
        checks.append(ValidationCheck(
            name=f"panel_overflow_{panel_id}",
            passed=not overflow,
            message=(
                f"Panel {panel_id!r} "
                f"{'overflows' if overflow else 'fits within'} "
                f"figure width"
            ),
            severity="error" if overflow else "warning",
        ))

    # DPI check
    checks.append(ValidationCheck(
        name="dpi",
        passed=True,
        message=f"Target DPI is {target.dpi} (checked at export time)",
    ))

    return checks
