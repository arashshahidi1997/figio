"""Tests for FigureSpec YAML schema and Pydantic models."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

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


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


def test_round_trip(tmp_path: Path) -> None:
    """Create FigureSpec programmatically, write to YAML, read back, assert equal."""
    spec = FigureSpec(
        id="fig_test",
        target="default",
        panels={
            "a": PanelSpec(generator=Generator.matplotlib, source="panels/a.py"),
            "b": PanelSpec(
                generator=Generator.matplotlib,
                source="panels/b.py",
                inputs=["data/x.csv"],
            ),
        },
        layout=LayoutSpec(
            type=LayoutType.grid,
            rows=1,
            cols=2,
            constraints=[
                LayoutConstraint(
                    type=ConstraintType.equal_height, panels=["a", "b"]
                )
            ],
        ),
        annotations=[
            AnnotationSpec(type=AnnotationType.panel_label, target="a", text="A"),
            AnnotationSpec(type=AnnotationType.panel_label, target="b", text="B"),
        ],
        style=StyleSpec(font_family="Helvetica", panel_gap_mm=3),
    )

    yaml_path = tmp_path / "test.figurespec.yaml"
    spec.to_yaml(yaml_path)
    loaded = FigureSpec.from_yaml(yaml_path)

    assert loaded.id == spec.id
    assert loaded.target == spec.target
    assert set(loaded.panels.keys()) == {"a", "b"}
    assert loaded.panels["a"].generator == Generator.matplotlib
    assert loaded.panels["b"].inputs == ["data/x.csv"]
    assert len(loaded.layout.constraints) == 1
    assert loaded.layout.constraints[0].type == ConstraintType.equal_height
    assert loaded.layout.constraints[0].panels == ["a", "b"]
    assert len(loaded.annotations) == 2
    assert loaded.style.font_family == "Helvetica"
    assert loaded.style.panel_gap_mm == 3.0


def test_design_doc_example(tmp_path: Path) -> None:
    """Parse the example YAML from the design document."""
    example_yaml = textwrap.dedent("""\
        figure:
          id: fig_sleep_psd
          target: nature_single_column

          panels:
            psd:
              generator: matplotlib
              source: panels/psd.py
              inputs: [data/session01_psd.parquet]
            topo:
              generator: matplotlib
              source: panels/topomap.py
              inputs: [data/session01_bandpower.nc]

          layout:
            type: grid
            rows: 1
            cols: 2
            constraints:
              - equal_height: [psd, topo]

          annotations:
            - type: panel_label
              target: psd
              text: A
            - type: panel_label
              target: topo
              text: B

          style:
            font_family: Helvetica
            panel_gap_mm: 3
    """)
    yaml_path = tmp_path / "example.yaml"
    yaml_path.write_text(example_yaml)

    spec = FigureSpec.from_yaml(yaml_path)

    assert spec.id == "fig_sleep_psd"
    assert spec.target == "nature_single_column"
    assert set(spec.panels.keys()) == {"psd", "topo"}
    assert spec.panels["psd"].generator == Generator.matplotlib
    assert spec.panels["psd"].source == "panels/psd.py"
    assert spec.layout.type == LayoutType.grid
    assert spec.layout.rows == 1
    assert spec.layout.cols == 2
    assert len(spec.layout.constraints) == 1
    assert spec.layout.constraints[0].type == ConstraintType.equal_height
    assert spec.annotations[0].text == "A"
    assert spec.style.font_family == "Helvetica"


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


def test_resolve_target_by_name() -> None:
    profile = resolve_target("nature_single_column")
    assert profile.figure_width_mm == 89.0
    assert profile.min_font_pt == 5.0
    assert profile.dpi == 300


def test_resolve_target_inline() -> None:
    inline = TargetProfile(
        name="custom", figure_width_mm=100, min_font_pt=7, dpi=200
    )
    assert resolve_target(inline) is inline


def test_resolve_target_unknown() -> None:
    with pytest.raises(KeyError, match="Unknown target profile"):
        resolve_target("nonexistent_journal")


def test_builtin_targets_complete() -> None:
    assert "nature_single_column" in BUILTIN_TARGETS
    assert "nature_double_column" in BUILTIN_TARGETS
    assert "default" in BUILTIN_TARGETS
    # New profiles added in phase 2c
    for name in (
        "science_single", "science_double",
        "pnas_single", "pnas_double",
        "elife", "plos_one",
        "cell_single", "cell_double",
        "ieee_single", "ieee_double",
    ):
        assert name in BUILTIN_TARGETS, f"Missing built-in profile: {name}"


@pytest.mark.parametrize("name", [
    "science_single", "science_double",
    "pnas_single", "pnas_double",
    "elife", "plos_one",
    "cell_single", "cell_double",
    "ieee_single", "ieee_double",
])
def test_new_profiles_resolve_by_name(name: str) -> None:
    profile = resolve_target(name)
    assert profile.name == name


@pytest.mark.parametrize("name", [
    "science_single", "science_double",
    "pnas_single", "pnas_double",
    "elife", "plos_one",
    "cell_single", "cell_double",
    "ieee_single", "ieee_double",
])
def test_new_profiles_reasonable_dimensions(name: str) -> None:
    profile = resolve_target(name)
    assert profile.figure_width_mm > 50.0
    assert profile.dpi >= 150


def test_elife_has_max_height() -> None:
    profile = resolve_target("elife")
    assert profile.max_height_mm == 225.0


def test_colorblind_check_profiles() -> None:
    for name in ("nature_single_column", "nature_double_column", "elife", "plos_one"):
        assert resolve_target(name).colorblind_check is True


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_missing_required_id() -> None:
    with pytest.raises(Exception):
        FigureSpec.model_validate({"panels": {"a": {"generator": "matplotlib", "source": "a.py"}}})


def test_missing_required_panels() -> None:
    with pytest.raises(Exception):
        FigureSpec.model_validate({"id": "test"})


def test_unknown_generator() -> None:
    with pytest.raises(Exception):
        PanelSpec(generator="photoshop", source="x.py")  # type: ignore[arg-type]


def test_unknown_constraint_type() -> None:
    with pytest.raises(Exception):
        LayoutConstraint(type="magical_alignment", panels=["a"])  # type: ignore[arg-type]


def test_unknown_annotation_type() -> None:
    with pytest.raises(Exception):
        AnnotationSpec(type="sparkle", target="a")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# JSON Schema generation
# ---------------------------------------------------------------------------


def test_json_schema_generation() -> None:
    """FigureSpec can generate a valid JSON schema."""
    schema = FigureSpec.model_json_schema()
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "id" in schema["properties"]
    assert "panels" in schema["properties"]


def test_json_schema_write(tmp_path: Path) -> None:
    """JSON schema can be written to file."""
    import json

    schema = FigureSpec.model_json_schema()
    out = tmp_path / "figurespec.schema.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    loaded = json.loads(out.read_text())
    assert loaded["type"] == "object"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_flat_yaml_format(tmp_path: Path) -> None:
    """Specs without the top-level ``figure:`` wrapper are also accepted."""
    flat = {
        "id": "fig_flat",
        "panels": {
            "x": {"generator": "matplotlib", "source": "x.py"},
        },
    }
    yaml_path = tmp_path / "flat.yaml"
    with open(yaml_path, "w") as fh:
        yaml.safe_dump(flat, fh)

    spec = FigureSpec.from_yaml(yaml_path)
    assert spec.id == "fig_flat"


def test_inline_target_profile(tmp_path: Path) -> None:
    """Inline target profile (dict instead of string) round-trips."""
    spec = FigureSpec(
        id="fig_inline",
        target=TargetProfile(
            name="custom", figure_width_mm=100, min_font_pt=7, dpi=200
        ),
        panels={"a": PanelSpec(generator=Generator.matplotlib, source="a.py")},
    )

    yaml_path = tmp_path / "inline_target.yaml"
    spec.to_yaml(yaml_path)
    loaded = FigureSpec.from_yaml(yaml_path)

    assert isinstance(loaded.target, dict) or isinstance(loaded.target, TargetProfile)


def test_default_style() -> None:
    """StyleSpec has sensible defaults."""
    style = StyleSpec()
    assert style.font_family == "Helvetica"
    assert style.panel_gap_mm == 3.0
    assert style.line_weight == 0.5


def test_default_layout() -> None:
    """LayoutSpec defaults to 1x1 grid."""
    layout = LayoutSpec()
    assert layout.type == LayoutType.grid
    assert layout.rows == 1
    assert layout.cols == 1
