from __future__ import annotations


def test_import() -> None:
    import figio

    assert figio.__name__ == "figio"
