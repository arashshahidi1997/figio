"""Panel adapter protocol and result types.

Each adapter renders a panel script into an SVG fragment with metadata
(bounding box, anchor points, semantic element IDs) that the composer
uses for positioning and annotation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pathlib import Path

from pydantic import BaseModel, Field

from figio.schema import PanelSpec, StyleSpec


class PanelResult(BaseModel):
    """Output of a panel adapter render call."""

    svg: str
    bbox_mm: tuple[float, float, float, float]  # x, y, width, height
    anchors: dict[str, tuple[float, float]] = Field(default_factory=dict)
    semantic_ids: list[str] = Field(default_factory=list)


@runtime_checkable
class PanelAdapter(Protocol):
    """Protocol that all panel adapters must implement."""

    def render(
        self,
        panel_id: str,
        spec: PanelSpec,
        style: StyleSpec,
        workdir: Path,
    ) -> PanelResult: ...

    def supported_constraints(self) -> list[str]: ...
