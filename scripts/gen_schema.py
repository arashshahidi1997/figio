#!/usr/bin/env python
"""Regenerate figurespec.schema.json from the Pydantic model."""
from __future__ import annotations

import json
from pathlib import Path

from figio.schema import FigureSpec

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "src" / "figio" / "figurespec.schema.json"


def main() -> None:
    schema = FigureSpec.model_json_schema()
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
