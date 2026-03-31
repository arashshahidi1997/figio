"""FigureSpec declarative schema — Pydantic models for figure orchestration.

Defines the YAML manifest that coordinates panel backends, layout, annotations,
style tokens, and journal target profiles into a single reproducible build.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Generator(str, Enum):
    """Supported panel generator backends."""

    matplotlib = "matplotlib"
    vega = "vega"
    mermaid = "mermaid"
    graphviz = "graphviz"
    script = "script"


class LayoutType(str, Enum):
    grid = "grid"
    mosaic = "mosaic"


class AnnotationType(str, Enum):
    panel_label = "panel_label"
    callout = "callout"
    arrow = "arrow"
    bracket = "bracket"
    caption = "caption"


class ConstraintType(str, Enum):
    equal_height = "equal_height"
    equal_width = "equal_width"
    align_ylabels = "align_ylabels"
    align_xlabels = "align_xlabels"
    shared_colorbar = "shared_colorbar"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class PanelSpec(BaseModel):
    """A single panel: references a generator backend and source script."""

    generator: Generator
    source: str
    inputs: list[str] = Field(default_factory=list)
    anchors: dict[str, list[float]] = Field(default_factory=dict)
    semantic_ids: list[str] = Field(default_factory=list)


class LayoutConstraint(BaseModel):
    """A typed layout constraint applied to a set of panels."""

    type: ConstraintType
    panels: list[str]


class LayoutSpec(BaseModel):
    """Layout specification: grid or mosaic arrangement of panels."""

    type: LayoutType = LayoutType.grid
    rows: int = 1
    cols: int = 1
    mosaic: str | None = None
    constraints: list[LayoutConstraint] = Field(default_factory=list)


class AnnotationSpec(BaseModel):
    """A typed annotation attached to a panel or figure region."""

    type: AnnotationType
    target: str = ""
    text: str = ""
    position: list[float] = Field(default_factory=list)
    start: str = ""
    end: str = ""


class StyleSpec(BaseModel):
    """Style tokens applied at composition time."""

    font_family: str = "Helvetica"
    font_size_pt: float | None = None
    panel_gap_mm: float = 3.0
    line_weight: float = 0.5
    color_roles: dict[str, str] = Field(default_factory=dict)


class TargetProfile(BaseModel):
    """Journal/output target profile with dimension and quality constraints."""

    name: str = "default"
    figure_width_mm: float = 170.0
    min_font_pt: float = 6.0
    dpi: int = 150
    max_height_mm: float | None = None
    colorblind_check: bool = False


# ---------------------------------------------------------------------------
# Top-level FigureSpec
# ---------------------------------------------------------------------------

class FigureSpec(BaseModel):
    """Top-level figure specification — the orchestration manifest."""

    id: str
    target: str | TargetProfile = "default"
    panels: dict[str, PanelSpec]
    layout: LayoutSpec = Field(default_factory=LayoutSpec)
    annotations: list[AnnotationSpec] = Field(default_factory=list)
    style: StyleSpec = Field(default_factory=StyleSpec)

    @classmethod
    def from_yaml(cls, path: Path | str) -> FigureSpec:
        """Load a FigureSpec from a YAML file.

        Supports both top-level ``figure:`` wrapper and flat format.
        """
        path = Path(path)
        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}
        # Support wrapped format: ``figure: { ... }``
        if "figure" in raw and isinstance(raw["figure"], dict):
            raw = raw["figure"]
        # Parse constraints shorthand: ``{equal_height: [a, b]}`` → typed
        if "layout" in raw and "constraints" in raw["layout"]:
            raw["layout"]["constraints"] = _parse_constraints(
                raw["layout"]["constraints"]
            )
        return cls.model_validate(raw)

    def to_yaml(self, path: Path | str) -> None:
        """Serialize the FigureSpec to a YAML file."""
        path = Path(path)
        data = {"figure": _dump_model(self)}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_constraints(raw_list: list[Any]) -> list[dict[str, Any]]:
    """Convert shorthand constraint dicts to typed LayoutConstraint dicts.

    Accepts both:
      - ``{equal_height: [psd, topo]}``  (shorthand from YAML)
      - ``{type: equal_height, panels: [psd, topo]}``  (explicit)
    """
    result: list[dict[str, Any]] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        if "type" in item and "panels" in item:
            result.append(item)
        else:
            for key, panels in item.items():
                result.append({"type": key, "panels": panels})
    return result


def _dump_model(obj: BaseModel) -> dict[str, Any]:
    """Recursively dump a Pydantic model to a plain dict suitable for YAML."""
    data = obj.model_dump(mode="python", exclude_none=True)
    # Convert enums to their string values
    return _convert_enums(data)


def _convert_enums(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _convert_enums(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_enums(v) for v in obj]
    return obj
