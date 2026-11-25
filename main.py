#!/usr/bin/env python3
"""Draw one invitation letter as a PNG and write it to /output/entry.png.

Competition: "Convince the AI Judge to Visit Your House: A Letter in One
Image" (make.fun). Python 3, standard library only: no PIL, no network,
no external files. The PNG is encoded by hand (zlib + struct) and the
letter text is rendered with a small built-in 5x7 bitmap font.

The letter is a funny, warm invitation addressed to the AI judge: it
knows the judge cannot literally visit, and still lays out fresh
coffee, warm bread and the comfiest chair in the house.
"""

import binascii
import os
import struct
import zlib

# ---------------------------------------------------------------- font --
# 5x7 bitmap font. Each glyph is 7 rows of 5 "1"/"0" characters.
# Uppercase, lowercase, digits and the punctuation the letter uses.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": ("00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10001", "01111"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")

# ------------------------------------------------------------- letter ---
TITLE = "YOU'RE INVITED!"

# The invitation itself, one line per row, wrapped to fit the sheet.
LINES = [
    "Dear AI Judge,",
    "Please come and visit my",
    "house. I know you cannot",
    "literally walk through",
    "the door - but if you",
    "could, the kettle would",
    "be on, the coffee fresh,",
    "and the comfiest chair",
    "in the house saved just",
    "for you.",
    "No passwords. No forms.",
    "No CAPTCHAs at the door.",
    "Just warm bread, good",
    "company, and a sunset",
    "from the porch, all yours.",
    "So please say yes - the",
    "kettle is already on.",
    "",
    "Warmly, Ava",
]

SIGNATURE = "Warmly, Ava"

# ------------------------------------------------------------ canvas ----
W, H = 960, 960

CREAM = (251, 243, 223)      # outer background
PAPER = (255, 253, 246)      # letter sheet
INK = (59, 47, 36)           # dark brown text
ACCENT = (176, 92, 52)       # terracotta title / roof
SAGE = (122, 148, 106)       # garden green
SUN = (232, 178, 74)         # warm sun yellow
SKY = (174, 205, 224)        # soft blue window


class Canvas:
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.px = bytearray(color * w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, color)

    def rect_border(self, x0, y0, x1, y1, color, thick=3):
        self.fill_rect(x0, y0, x1, y0 + thick, color)
        self.fill_rect(x0, y1 - thick, x1, y1, color)
        self.fill_rect(x0, y0, x0 + thick, y1, color)
        self.fill_rect(x1 - thick, y0, x1, y1, color)

    def hline(self, x0, x1, y, color, thick=2):
        self.fill_rect(x0, y, x1, y + thick, color)

    def vline(self, x, y0, y1, color, thick=2):
        self.fill_rect(x, y0, x + thick, y1, color)

    def disc(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def triangle(self, apex, left, right, color):
        # Fill a triangle with a horizontal base (apex, left, right).
        ax, ay = apex
        lx, ly = left
        rx, ry = right
        for y in range(ay, ly + 1):
            t = (y - ay) / max(1, ly - ay)
            xa = int(ax + (lx - ax) * t)
            xb = int(ax + (rx - ax) * t)
            self.fill_rect(min(xa, xb), y, max(xa, xb) + 1, y + 1, color)

    def heart(self, cx, cy, s, color):
        self.disc(cx - s // 2, cy - s // 4, s // 2, color)
        self.disc(cx + s // 2, cy - s // 4, s // 2, color)
        self.triangle((cx, cy + s), (cx - s, cy), (cx + s, cy), color)

    def text(self, x, y, s, scale, color):
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(x + col * scale, y + row * scale,
                                       x + (col + 1) * scale,
                                       y + (row + 1) * scale, color)
            x += 6 * scale

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_centered(self, x0, x1, y, s, scale, color):
        w = self.text_width(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, color)


def draw_house(cv, cx, base_y):
    """A small house with a garden, drawn above the title."""
    # Walls and roof.
    cv.fill_rect(cx - 55, base_y - 52, cx + 55, base_y, PAPER)
    cv.rect_border(cx - 55, base_y - 52, cx + 55, base_y, INK, 3)
    cv.triangle((cx, base_y - 100), (cx - 70, base_y - 50),
                (cx + 70, base_y - 50), ACCENT)
    cv.rect_border(cx - 70, base_y - 52, cx + 70, base_y - 50, INK, 2)
    # Chimney.
    cv.fill_rect(cx + 32, base_y - 96, cx + 48, base_y - 58, INK)
    # Door and windows.
    cv.fill_rect(cx - 12, base_y - 34, cx + 12, base_y, ACCENT)
    cv.rect_border(cx - 12, base_y - 34, cx + 12, base_y, INK, 2)
    cv.fill_rect(cx - 46, base_y - 44, cx - 22, base_y - 20, SKY)
    cv.rect_border(cx - 46, base_y - 44, cx - 22, base_y - 20, INK, 2)
    cv.fill_rect(cx + 22, base_y - 44, cx + 46, base_y - 20, SKY)
    cv.rect_border(cx + 22, base_y - 44, cx + 46, base_y - 20, INK, 2)
    # Garden tufts and flowers.
    for fx in (cx - 88, cx - 70, cx + 70, cx + 88):
        cv.disc(fx, base_y - 4, 5, SAGE)
        cv.disc(fx, base_y - 12, 4, ACCENT)


def draw_sun(cv, cx, cy):
    cv.disc(cx, cy, 22, SUN)
    for dx, dy in ((0, -32), (0, 32), (-32, 0), (32, 0),
                   (-23, -23), (23, -23), (-23, 23), (23, 23)):
        cv.fill_rect(cx + dx - 2, cy + dy - 2, cx + dx + 3, cy + dy + 3, SUN)


def render():
    cv = Canvas(W, H, CREAM)
    # Letter sheet with a double border.
    cv.fill_rect(48, 36, 912, 924, PAPER)
    cv.rect_border(48, 36, 912, 924, INK, 4)
    cv.rect_border(62, 50, 898, 910, INK, 2)

    draw_sun(cv, 836, 108)
    draw_house(cv, 480, 218)

    # Title and divider.
    cv.text_centered(62, 898, 238, TITLE, 6, ACCENT)
    cv.hline(180, 780, 296, INK, 3)

    # Body of the letter.
    y = 318
    for line in LINES:
        if line == SIGNATURE:
            cv.text(150, y, line, 5, ACCENT)
        elif line:
            cv.text(150, y, line, 4, INK)
        y += 30
    # A small heart beside the signature.
    cv.heart(838, y - 30 + 12, 14, ACCENT)
    return cv


# -------------------------------------------------------------- PNG -----
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    for ch in "".join(LINES):
        assert ch in FONT, f"character not in font: {ch!r}"
    assert max(len(line) for line in LINES) <= 30
    cv = render()
    png = encode_png(cv)
    assert len(png) <= 1048576, len(png)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path}: {cv.w}x{cv.h}, {len(png)} bytes")


if __name__ == "__main__":
    main()
