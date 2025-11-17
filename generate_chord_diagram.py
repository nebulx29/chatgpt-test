"""Generate guitar chord diagrams as PNG images.

Usage:
    python generate_chord_diagram.py "Cmaj7" --output Cmaj7.png

The script looks up a predefined chord dictionary and renders a diagram
similar to common chord charts.  See CHORD_SHAPES for the available chords.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class ChordShape:
    """Represents the fingering for a chord.

    Attributes:
        frets: A six element list describing the frets for
            EADGBE strings. -1 = muted, 0 = open, positive values
            indicate the fret number to press.
        label: Optional text displayed under the diagram to describe
            the voicing, e.g. "E-shape barre".
    """

    frets: List[int]
    label: str | None = None

    def __post_init__(self) -> None:  # type: ignore[override]
        if len(self.frets) != 6:
            msg = "Chord definitions must have exactly 6 string values"
            raise ValueError(msg)


# fmt: off
CHORD_SHAPES: Dict[str, ChordShape] = {
    "C": ChordShape([-1, 3, 2, 0, 1, 0], "Open C"),
    "Cdim7": ChordShape([-1, 3, 4, 2, 4, 2], "C diminished 7"),
    "D#m": ChordShape([-1, 6, 8, 8, 7, 6], "6th fret barre"),
    "D#": ChordShape([-1, 6, 8, 8, 8, 6]),
    "Eb": ChordShape([-1, 6, 8, 8, 8, 6]),
    "E": ChordShape([0, 2, 2, 1, 0, 0]),
    "Em": ChordShape([0, 2, 2, 0, 0, 0]),
    "Em7": ChordShape([0, 2, 2, 0, 3, 0]),
    "Bm7b5": ChordShape([-1, 2, 3, 2, 3, -1], "Half-diminished"),
    "F9": ChordShape([1, -1, 1, 2, 1, 3]),
    "F13": ChordShape([1, -1, 1, 2, 3, 3]),
    "G": ChordShape([3, 2, 0, 0, 0, 3]),
}
# fmt: on


def determine_base_fret(frets: List[int]) -> int:
    positive = [f for f in frets if f > 0]
    if not positive:
        return 1
    min_fret = min(positive)
    max_fret = max(positive)
    if max_fret <= 3:
        return 1
    if min_fret <= 1:
        return 1
    return min_fret


def draw_chord_diagram(chord_name: str, shape: ChordShape, output_path: Path) -> None:
    width, height = 500, 600
    background_color = "white"
    fret_color = "black"
    image = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(image)
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

    margin_x = 70
    top_margin = 140
    string_spacing = (width - 2 * margin_x) / 5
    fret_spacing = 70
    total_frets_to_draw = 5  # draws nut + 4 frets

    # Draw chord title
    draw.text((width / 2 - 20, 40), chord_name, fill=fret_color, font=font_large)

    base_fret = determine_base_fret(shape.frets)

    # Draw strings
    string_x_positions = [margin_x + i * string_spacing for i in range(6)]
    fret_y_positions = [top_margin + i * fret_spacing for i in range(total_frets_to_draw)]

    for x in string_x_positions:
        draw.line([(x, fret_y_positions[0]), (x, fret_y_positions[-1])], fill=fret_color, width=3)

    for i, y in enumerate(fret_y_positions):
        width_override = 8 if i == 0 and base_fret == 1 else 3
        draw.line([(string_x_positions[0], y), (string_x_positions[-1], y)], fill=fret_color, width=width_override)

    if base_fret > 1:
        text = f"Fret {base_fret}"
        draw.text((string_x_positions[-1] + 10, fret_y_positions[0] - fret_spacing / 2), text, fill=fret_color, font=font_small)

    # draw markers for open/muted strings
    indicator_y = top_margin - 30
    for idx, fret in enumerate(shape.frets):
        x = string_x_positions[idx]
        if fret == -1:
            draw.text((x - 6, indicator_y - 10), "X", fill=fret_color, font=font_small)
        elif fret == 0:
            radius = 10
            draw.ellipse(
                (x - radius, indicator_y - radius, x + radius, indicator_y + radius),
                outline=fret_color,
                width=3,
            )

    # draw finger dots
    for idx, fret in enumerate(shape.frets):
        if fret <= 0:
            continue
        if base_fret == 1:
            relative = fret
        else:
            relative = fret - base_fret + 1
        if relative < 0 or relative > total_frets_to_draw:
            continue
        y = top_margin + (relative - 0.5) * fret_spacing
        x = string_x_positions[idx]
        radius = 18
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fret_color)

    if shape.label:
        draw.text((margin_x, fret_y_positions[-1] + 30), shape.label, fill=fret_color, font=font_small)

    image.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a guitar chord diagram")
    parser.add_argument("chord", help="Chord name, e.g. C, Em7, Bm7b5")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output PNG path. Defaults to '<CHORD>.png' in the current directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chord_name = args.chord.strip()
    shape = CHORD_SHAPES.get(chord_name)
    if shape is None:
        available = ", ".join(sorted(CHORD_SHAPES))
        msg = f"Chord '{chord_name}' is not defined. Available: {available}"
        raise SystemExit(msg)

    output_path = args.output or Path(f"{chord_name}.png")
    draw_chord_diagram(chord_name, shape, output_path)
    print(f"Saved diagram for {chord_name} to {output_path}")


if __name__ == "__main__":
    main()
