"""figio — Build orchestrator for reproducible scientific figures."""

from figio.schema import (
    AnnotationSpec,
    AnnotationType,
    ConstraintType,
    FigureSpec,
    Generator,
    LayoutConstraint,
    LayoutSpec,
    LayoutType,
    PanelSpec,
    StyleSpec,
    TargetProfile,
)
from figio.targets import BUILTIN_TARGETS, resolve_target

__all__ = [
    "AnnotationSpec",
    "AnnotationType",
    "BUILTIN_TARGETS",
    "ConstraintType",
    "FigureSpec",
    "Generator",
    "LayoutConstraint",
    "LayoutSpec",
    "LayoutType",
    "PanelSpec",
    "StyleSpec",
    "TargetProfile",
    "resolve_target",
]
