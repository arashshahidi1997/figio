"""Built-in target profiles for common journal and output formats."""

from __future__ import annotations

from .schema import TargetProfile

BUILTIN_TARGETS: dict[str, TargetProfile] = {
    "nature_single_column": TargetProfile(
        name="nature_single_column",
        figure_width_mm=89.0,
        min_font_pt=5.0,
        dpi=300,
        colorblind_check=True,
    ),
    "nature_double_column": TargetProfile(
        name="nature_double_column",
        figure_width_mm=183.0,
        min_font_pt=5.0,
        dpi=300,
        colorblind_check=True,
    ),
    "science_single": TargetProfile(
        name="science_single",
        figure_width_mm=55.0,
        min_font_pt=6.0,
        dpi=300,
    ),
    "science_double": TargetProfile(
        name="science_double",
        figure_width_mm=117.0,
        min_font_pt=6.0,
        dpi=300,
    ),
    "pnas_single": TargetProfile(
        name="pnas_single",
        figure_width_mm=87.0,
        min_font_pt=6.0,
        dpi=300,
    ),
    "pnas_double": TargetProfile(
        name="pnas_double",
        figure_width_mm=178.0,
        min_font_pt=6.0,
        dpi=300,
    ),
    "elife": TargetProfile(
        name="elife",
        figure_width_mm=140.0,
        min_font_pt=7.0,
        dpi=300,
        max_height_mm=225.0,
        colorblind_check=True,
    ),
    "plos_one": TargetProfile(
        name="plos_one",
        figure_width_mm=173.0,
        min_font_pt=8.0,
        dpi=300,
        colorblind_check=True,
    ),
    "cell_single": TargetProfile(
        name="cell_single",
        figure_width_mm=85.0,
        min_font_pt=5.0,
        dpi=300,
    ),
    "cell_double": TargetProfile(
        name="cell_double",
        figure_width_mm=174.0,
        min_font_pt=5.0,
        dpi=300,
    ),
    "ieee_single": TargetProfile(
        name="ieee_single",
        figure_width_mm=88.0,
        min_font_pt=8.0,
        dpi=300,
    ),
    "ieee_double": TargetProfile(
        name="ieee_double",
        figure_width_mm=181.0,
        min_font_pt=8.0,
        dpi=300,
    ),
    "default": TargetProfile(
        name="default",
        figure_width_mm=170.0,
        min_font_pt=6.0,
        dpi=150,
    ),
}


def resolve_target(name_or_profile: str | TargetProfile) -> TargetProfile:
    """Resolve a target by name (from built-in profiles) or pass through an inline profile.

    Raises ``KeyError`` if *name_or_profile* is a string that does not match
    any built-in target profile.
    """
    if isinstance(name_or_profile, TargetProfile):
        return name_or_profile
    if name_or_profile in BUILTIN_TARGETS:
        return BUILTIN_TARGETS[name_or_profile]
    raise KeyError(
        f"Unknown target profile: {name_or_profile!r}. "
        f"Known: {', '.join(BUILTIN_TARGETS)}"
    )
