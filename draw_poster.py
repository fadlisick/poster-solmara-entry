#!/usr/bin/env python3
"""Render the SOLMARA travel poster.

A vintage flat travel poster for an invented place: a white lighthouse with a
golden beam on a crescent cliff over a turquoise bay at golden hour. The only
text in the image is the place name, SOLMARA.

Deterministic: fixed geometry, no randomness, no timestamps. Renders at 2048
and downscales to 1024 for clean anti-aliasing.
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2048                      # working size
OUT = 1024                    # final size

TEAL = (14, 74, 82)           # #0E4A52 deep teal
TURQ = (42, 157, 143)         # #2A9D8F turquoise
AMBER = (244, 162, 89)        # #F4A259 amber
CORAL = (231, 111, 81)        # #E76F51 coral
CREAM = (251, 243, 228)       # #FBF3E4 cream
VIOLET = (91, 75, 138)        # #5B4B8A dusk violet
GOLD = (250, 196, 90)
SUN_CORE = (255, 214, 130)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(size, stops):
    """Vertical gradient image. stops: list of (position 0..1, colour)."""
    w, h = size
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                px[0, y] = lerp(c0, c1, f)
                break
        else:
            px[0, y] = stops[-1][1]
    # fill each row across the width
    row = img.crop((0, 0, 1, h)).resize((w, h))
    return row


def soft_disc(layer, cx, cy, r, colour, alpha):
    """Draw a soft-edged disc on an RGBA layer."""
    tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (alpha,))
    tmp = tmp.filter(ImageFilter.GaussianBlur(r * 0.35))
    layer.alpha_composite(tmp)


def main():
    img = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(img)

    # ---- sky: dusk violet at top, warming to amber at the horizon ----
    horizon = int(S * 0.66)
    sky = vgrad((S, horizon), [
        (0.00, (58, 52, 96)),
        (0.35, VIOLET),
        (0.62, (196, 110, 96)),
        (0.85, AMBER),
        (1.00, (250, 190, 110)),
    ])
    img.paste(sky, (0, 0))

    # ---- sea: turquoise at the horizon deepening to deep teal ----
    sea = vgrad((S, S - horizon), [
        (0.00, (64, 178, 160)),
        (0.30, TURQ),
        (0.70, (22, 110, 118)),
        (1.00, TEAL),
    ])
    img.paste(sea, (0, horizon))

    # ---- sun: huge low disc, centred, sitting on the horizon ----
    sun_cx, sun_cy, sun_r = S // 2, horizon - 120, 280
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    soft_disc(glow, sun_cx, sun_cy, sun_r * 2, (255, 190, 110), 70)
    soft_disc(glow, sun_cx, sun_cy, int(sun_r * 1.45), (255, 205, 120), 90)
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
              fill=SUN_CORE)
    # thin coral ring hugging the sun
    d.ellipse([sun_cx - sun_r - 14, sun_cy - sun_r - 14,
               sun_cx + sun_r + 14, sun_cy + sun_r + 14],
              outline=CORAL, width=10)

    # ---- sun path on the water: shimmering amber dashes under the sun ----
    for i, (w, gap) in enumerate([(380, 26), (320, 30), (260, 34), (210, 38),
                                  (170, 42), (130, 46)]):
        y = horizon + 220 + i * 72
        x0 = sun_cx - w // 2
        d.rounded_rectangle([x0, y, x0 + w, y + 22], radius=11,
                            fill=(255, 196, 110))

    # ---- distant headlands: layered silhouettes left and right ----
    # far left headland
    d.polygon([(0, horizon + 10), (0, horizon - 190), (180, horizon - 250),
               (420, horizon - 170), (560, horizon - 90), (560, horizon + 10)],
              fill=(96, 84, 138))
    # far right headland
    d.polygon([(S, horizon + 10), (S, horizon - 150), (1830, horizon - 230),
               (1620, horizon - 140), (1500, horizon - 60), (1500, horizon + 10)],
              fill=(96, 84, 138))
    # near left headland (darker, lower)
    d.polygon([(0, horizon + 60), (0, horizon - 60), (260, horizon - 120),
               (520, horizon - 40), (640, horizon + 20), (640, horizon + 60)],
              fill=(58, 62, 108))

    # ---- the cliff (right of centre) carrying the lighthouse ----
    cliff = [(1280, horizon + 30), (1330, horizon - 240), (1470, horizon - 300),
             (1640, horizon - 280), (1740, horizon - 180), (1770, horizon - 40),
             (1770, horizon + 30)]
    d.polygon(cliff, fill=(24, 66, 78))
    # cliff highlight edge
    d.line([(1330, horizon - 240), (1470, horizon - 300), (1640, horizon - 280)],
           fill=(42, 110, 118), width=14)
    # cliff base rocks
    d.polygon([(1280, horizon + 30), (1330, horizon - 30), (1450, horizon - 10),
               (1560, horizon + 30)], fill=(18, 56, 66))

    # ---- lighthouse: white tower, coral bands, coral cap, golden lamp ----
    lx = 1520                      # tower centre x
    base_y = horizon - 280         # ground under the tower
    top_y = horizon - 620
    # tower: slight taper
    d.polygon([(lx - 78, base_y), (lx - 52, top_y), (lx + 52, top_y),
               (lx + 78, base_y)], fill=(250, 247, 240))
    # coral bands
    for y0, y1 in [(base_y - 90, base_y - 34), (base_y - 250, base_y - 194)]:
        w0 = 78 - (base_y - y0) * (26 / (base_y - top_y))
        w1 = 78 - (base_y - y1) * (26 / (base_y - top_y))
        d.polygon([(lx - w0, y0), (lx + w0, y0), (lx + w1, y1), (lx - w1, y1)],
                  fill=CORAL)
    # gallery + lamp room
    d.rectangle([lx - 66, top_y - 46, lx + 66, top_y - 8], fill=(30, 60, 70))
    d.rectangle([lx - 46, top_y - 118, lx + 46, top_y - 46], fill=GOLD)
    d.rectangle([lx - 46, top_y - 118, lx + 46, top_y - 46], outline=(30, 60, 70),
                width=6)
    # cap
    d.polygon([(lx - 56, top_y - 118), (lx + 56, top_y - 118), (lx, top_y - 176)],
              fill=CORAL)
    d.ellipse([lx - 10, top_y - 196, lx + 10, top_y - 176], fill=GOLD)
    # door
    d.rounded_rectangle([lx - 20, base_y - 96, lx + 20, base_y], radius=18,
                        fill=(30, 60, 70))

    # ---- golden beam sweeping left and down over the bay ----
    beam = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    lamp_y = top_y - 82
    bd.polygon([(lx, lamp_y), (60, lamp_y + 200), (60, lamp_y + 380)],
               fill=(255, 214, 120, 110))
    bd.polygon([(lx, lamp_y), (60, lamp_y + 250), (60, lamp_y + 330)],
               fill=(255, 226, 150, 150))
    beam = beam.filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(img.convert("RGBA"), beam).convert("RGB")
    d = ImageDraw.Draw(img)
    # bright core of the lamp
    d.ellipse([lx - 16, lamp_y - 16, lx + 16, lamp_y + 16], fill=(255, 240, 200))

    # ---- sailboats on the bay ----
    def sailboat(cx, cy, scale, hull):
        d.polygon([(cx, cy - 74 * scale), (cx, cy), (cx + 52 * scale, cy)],
                  fill=(251, 243, 228))
        d.polygon([(cx - 6, cy - 58 * scale), (cx - 6, cy),
                   (cx - 44 * scale, cy)], fill=(231, 111, 81))
        d.polygon([(cx - 56 * scale, cy), (cx + 62 * scale, cy),
                   (cx + 46 * scale, cy + 20 * scale),
                   (cx - 40 * scale, cy + 20 * scale)], fill=hull)
        d.line([cx, cy - 74 * scale, cx, cy], fill=(30, 60, 70), width=4)

    sailboat(700, horizon + 340, 1.0, (30, 60, 70))
    sailboat(1260, horizon + 520, 0.72, (91, 75, 138))

    # ---- birds ----
    def bird(cx, cy, s):
        d.arc([cx - 22 * s, cy - 14 * s, cx, cy + 14 * s], 200, 340,
              fill=(30, 60, 70), width=7)
        d.arc([cx, cy - 14 * s, cx + 22 * s, cy + 14 * s], 200, 340,
              fill=(30, 60, 70), width=7)

    bird(430, 600, 1.0)
    bird(570, 540, 0.8)
    bird(330, 660, 0.7)
    bird(1750, 620, 0.9)
    bird(1860, 700, 0.7)

    # ---- title: SOLMARA, cream serif, letterspaced, upper third ----
    title = "SOLMARA"
    font = ImageFont.truetype(SERIF_BOLD, 205)
    widths = [d.textlength(ch, font=font) for ch in title]
    tracking = 40
    total = sum(widths) + tracking * (len(title) - 1)
    x = (S - total) // 2
    x_start = x
    x_end = x + total
    y_title = 260
    # soft shadow for legibility
    for ch, w in zip(title, widths):
        d.text((x + 6, y_title + 8), ch, font=font, fill=(58, 52, 96))
        x += w + tracking
    x = (S - total) // 2
    for ch, w in zip(title, widths):
        d.text((x, y_title), ch, font=font, fill=CREAM)
        x += w + tracking
    # thin rules either side of the title, clear of the letters
    rule_y = y_title + 82
    d.line([(130, rule_y), (x_start - 70, rule_y)], fill=CREAM, width=6)
    d.line([(x_end + 70, rule_y), (S - 130, rule_y)], fill=CREAM, width=6)
    # small diamond ornaments on the rules
    for rx in (x_start - 70, x_end + 70):
        d.polygon([(rx, rule_y - 14), (rx + 14, rule_y), (rx, rule_y + 14),
                   (rx - 14, rule_y)], fill=CORAL)

    # ---- cream frame border ----
    d.rectangle([26, 26, S - 27, S - 27], outline=CREAM, width=30)
    d.rectangle([72, 72, S - 73, S - 73], outline=CREAM, width=4)

    # ---- downscale and save ----
    img = img.resize((OUT, OUT), Image.LANCZOS)
    img.save("entry.png", "PNG", optimize=True)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
