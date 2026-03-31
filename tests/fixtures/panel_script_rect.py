#!/usr/bin/env python3
"""Fixture script for ScriptAdapter tests.

Accepts --output PATH (required), --width-mm FLOAT, --height-mm FLOAT.
Writes a minimal SVG with a labelled rect at the given dimensions.
"""
import argparse

SVG_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{w}mm" height="{h}mm"
     viewBox="0 0 {w} {h}">
  <rect id="bg" x="0" y="0" width="{w}" height="{h}" fill="#eee"/>
  <rect id="bar" x="5" y="5" width="{bw}" height="{bh}" fill="steelblue"/>
  <text id="label" x="{cx}" y="{cy}" text-anchor="middle">panel</text>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--width-mm", type=float, default=80.0)
    parser.add_argument("--height-mm", type=float, default=60.0)
    args = parser.parse_args()

    w = args.width_mm
    h = args.height_mm
    svg = SVG_TEMPLATE.format(
        w=w,
        h=h,
        bw=w - 10,
        bh=h - 20,
        cx=w / 2,
        cy=h / 2,
    )
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(svg)


if __name__ == "__main__":
    main()
