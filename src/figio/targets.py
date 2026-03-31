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
