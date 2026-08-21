import os
from PIL import Image, ImageDraw, ImageFont

# 吉他和弦指法定義 (6弦到1弦, -1=x, 0=空弦, 1..4=品位)
CHORD_DATA = {
    "C": {"frets": [-1, 3, 2, 0, 1, 0], "fingers": ["x", "3", "2", "0", "1", "0"], "name": "C Major"},
    "G": {"frets": [3, 2, 0, 0, 3, 3], "fingers": ["2", "1", "0", "0", "3", "4"], "name": "G Major"},
    "Am": {"frets": [-1, 0, 2, 2, 1, 0], "fingers": ["x", "0", "2", "3", "1", "0"], "name": "A minor"},
    "Em": {"frets": [0, 2, 2, 0, 0, 0], "fingers": ["0", "2", "3", "0", "0", "0"], "name": "E minor"},
    "F": {"frets": [1, 3, 3, 2, 1, 1], "fingers": ["1", "3", "4", "2", "1", "1"], "name": "F Major"},
    "D": {"frets": [-1, -1, 0, 2, 3, 2], "fingers": ["x", "x", "0", "1", "3", "2"], "name": "D Major"},
    "Dm": {"frets": [-1, -1, 0, 2, 3, 1], "fingers": ["x", "x", "0", "2", "3", "1"], "name": "D minor"},
}

def generate_chord_chart(chord_name: str, output_path: str = None) -> str:
    chord = CHORD_DATA.get(chord_name.upper()) or CHORD_DATA.get(chord_name) or CHORD_DATA["C"]
    
    width, height = 360, 420
    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((width // 2, 40), f"🎸 {chord['name']} ({chord_name})", fill="#38bdf8", anchor="mm")

    # Draw Fretboard Grid
    start_x, start_y = 60, 90
    fret_w, fret_h = 48, 55
    strings = 6
    frets = 5

    # Nut (top thick bar)
    draw.rectangle([start_x, start_y, start_x + (strings - 1) * fret_w, start_y + 8], fill="#94a3b8")

    # Fret lines (horizontal)
    for i in range(frets + 1):
        y = start_y + i * fret_h
        draw.line([(start_x, y), (start_x + (strings - 1) * fret_w, y)], fill="#334155", width=2)

    # String lines (vertical)
    for i in range(strings):
        x = start_x + i * fret_w
        thickness = 1 + (5 - i) // 2
        draw.line([(x, start_y), (x, start_y + frets * fret_h)], fill="#64748b", width=thickness)

    # Draw Finger Dots & Open/Mute markers
    for str_idx, fret in enumerate(chord["frets"]):
        x = start_x + str_idx * fret_w
        finger = chord["fingers"][str_idx]

        if fret == -1:
            draw.text((x, start_y - 20), "✕", fill="#ef4444", anchor="mm")
        elif fret == 0:
            draw.text((x, start_y - 20), "○", fill="#38bdf8", anchor="mm")
        else:
            y = start_y + (fret - 0.5) * fret_h
            radius = 16
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill="#3b82f6", outline="#60a5fa", width=2)
            draw.text((x, y), str(finger), fill="#ffffff", anchor="mm")

    if output_path is None:
        output_path = f"/tmp/chord_{chord_name}.png"
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path)
    return output_path
