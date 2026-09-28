"""Fight Club – die letzte Szene als Pixel-Animation im Computerspiel-Look.

Zwei Figuren von hinten, Hand in Hand vor der Glasfront eines dunklen Büros im obersten Stock.
Draußen werden die Hochhäuser gesprengt. Irisblende auf, Irisblende zu – dann beginnt es von vorn.
Gleicher Stil wie berlin/fenster.gif: Endesga-32-Palette, Konturen, harte Lichtstufen.
Kein Text, keine Dialoge; die Figuren sind die eigenen Entwürfe aus fightclub.html.

Erzeugt finale/finale.gif (512x384 Pixel, 2x vergrößert, 200 Bilder à 80 ms = 16 s)
und finale/finale.png (Standbild).

    pip install pillow numpy
    python3 finale/finale.py
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

W, H = 512, 384
N = 200
MS = 80
SCALE = 2
HERE = Path(__file__).parent
YY, XX = np.mgrid[0:H, 0:W]
CHECK = ((YY + XX) % 2).astype(np.float32)
rnd = random.Random(1999)

# ---------------------------------------------------------------- Palette (Endesga 32)
HEX = """be4a2f d77643 ead4aa e4a672 b86f50 733e39 3e2731 a22633 e43b44 f77622 feae34 fee761 63c74d 3e8948
265c42 193c3e 124e89 0099db 2ce8f5 ffffff c0cbdc 8b9bb4 5a6988 3a4466 262b44 181425 ff0044 68386c
b55088 f6757a e8b796 c28569""".split()
PAL = np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in HEX], np.float32)
I = {h: i for i, h in enumerate(HEX)}


def C(h):
    return PAL[I[h.lstrip("#")]]


def ramp(pairs):
    m = np.arange(len(HEX))
    for p in pairs.split():
        a, b = p.split(":")
        m[I[a]] = I[b]
    return m


# Licht: jede Farbe hat eine wärmere, hellere Nachbarin; Dunkel: eine dunklere
LIGHT = ramp("""181425:3e2731 262b44:3e2731 3e2731:733e39 3a4466:733e39 68386c:733e39 5a6988:b86f50
733e39:b86f50 8b9bb4:c28569 b86f50:c28569 c28569:e4a672 e4a672:ead4aa 193c3e:265c42 265c42:3e8948
3e8948:63c74d 124e89:5a6988 be4a2f:d77643 a22633:be4a2f c0cbdc:e8b796 e8b796:ead4aa b55088:f6757a
d77643:f77622 f77622:feae34 feae34:fee761 fee761:ffffff ead4aa:ffffff""")
DARK = ramp("""ffffff:c0cbdc c0cbdc:8b9bb4 8b9bb4:5a6988 5a6988:3a4466 3a4466:262b44 262b44:181425
3e2731:181425 68386c:3e2731 b55088:68386c 733e39:3e2731 b86f50:733e39 c28569:b86f50 e4a672:c28569
ead4aa:e4a672 e8b796:c28569 fee761:feae34 feae34:f77622 f77622:be4a2f d77643:be4a2f be4a2f:733e39
e43b44:a22633 a22633:3e2731 ff0044:a22633 f6757a:b55088 63c74d:3e8948 3e8948:265c42 265c42:193c3e
193c3e:181425 2ce8f5:0099db 0099db:124e89 124e89:262b44""")
RIM = ramp("""181425:262b44 262b44:3a4466 3a4466:5a6988 5a6988:8b9bb4 3e2731:68386c 68386c:b55088
733e39:b86f50 b86f50:c28569 c0cbdc:ffffff ead4aa:ffffff 8b9bb4:c0cbdc""")


def to_index(fr):
    wts = np.array([0.30, 0.59, 0.11], np.float32) ** 0.5
    flat = fr.reshape(-1, 3) * wts
    d = ((flat[:, None, :] - PAL[None] * wts) ** 2).sum(-1)
    return d.argmin(1).reshape(fr.shape[:2])


def dq(m, levels):
    """Harte Farbstufen, am Übergang ein Schachbrettmuster."""
    v = m * levels
    base = np.floor(v)
    frac = v - base
    ck = CHECK[:m.shape[0], :m.shape[1]]
    return np.clip((base + ((frac > 0.7) | ((frac > 0.4) & (ck > 0)))) / levels, 0, 1)


def dilate(a):
    n = a.copy()
    n[1:] |= a[:-1]
    n[:-1] |= a[1:]
    n[:, 1:] |= a[:, :-1]
    n[:, :-1] |= a[:, 1:]
    return n


def outline(rgb, a, color):
    edge = dilate(a) & ~a
    rgb[edge] = color
    a |= edge


def disc(rgb, a, cx, cy, r, color):
    if r <= 0:
        return
    x0, x1 = max(0, int(cx - r - 1)), min(W, int(cx + r + 2))
    y0, y1 = max(0, int(cy - r - 1)), min(H, int(cy + r + 2))
    if x0 >= x1 or y0 >= y1:
        return
    m = (XX[y0:y1, x0:x1] - cx) ** 2 + (YY[y0:y1, x0:x1] - cy) ** 2 <= r * r
    rgb[y0:y1, x0:x1][m] = color
    if a is not None:
        a[y0:y1, x0:x1][m] = True


def from_pil(img):
    arr = np.array(img)
    return arr[..., :3].astype(np.float32), arr[..., 3] > 0


def hexrgb(h):
    return tuple(int(v) for v in C(h))


# ---------------------------------------------------------------- Maße
GLASS_TOP, SILL = 26, 296          # Glasfront
BASE = 262                          # Fußlinie der Türme (hinter der Stadt versteckt)
MULLIONS = [18, 148, 364, 494]

# ---------------------------------------------------------------- Außen: Himmel und Stadt (statisch)
outside = np.zeros((H, W, 3), np.float32)
bands = [C("181425"), C("262b44"), C("3a4466"), C("68386c"), C("b55088")]
tq = dq(np.interp(YY, [60, 105, 140, 165, 185], [0, 1, 2, 3, 4]) / 4, 4)
outside[:] = np.stack(bands)[np.round(tq * 4).astype(int)]
for _ in range(60):
    x, y = rnd.randrange(W), rnd.randint(GLASS_TOP, 110)
    outside[y, x] = C("8b9bb4") if rnd.random() < 0.8 else C("c0cbdc")

# ferne Silhouette
far = np.zeros((H, W), bool)
x = 0
while x < W:
    bw, top = rnd.randint(6, 22), rnd.randint(150, 178)
    col = rnd.choice([C("262b44"), C("3a4466")])
    outside[top:SILL, x:x + bw] = col
    far[top:SILL, x:x + bw] = True
    if rnd.random() < 0.25:
        ax = x + rnd.randrange(bw)
        h = rnd.randint(4, 12)
        outside[top - h:top, ax] = col
        far[top - h:top, ax] = True
    for wy in range(top + 3, SILL, 4):
        for wx in range(x + 1, min(W, x + bw - 1), 3):
            if rnd.random() < 0.18:
                outside[wy, wx] = rnd.choice([C("feae34"), C("e4a672"), C("8b9bb4")])
    x += bw
fr_a = far.copy()
outline(outside, fr_a, C("181425"))

# nahe Stadt vor den Turmsockeln
near_rgb = np.zeros((H, W, 3), np.float32)
near_a = np.zeros((H, W), bool)
x = 0
while x < W:
    bw, top = rnd.randint(14, 40), rnd.randint(232, 262)
    col = rnd.choice([C("262b44"), C("3a4466"), C("262b44")])
    near_rgb[top:SILL, x:x + bw] = col
    near_a[top:SILL, x:x + bw] = True
    near_rgb[top, x:x + bw] = C("5a6988")
    if rnd.random() < 0.4:                                # Dachaufbau
        rx = x + rnd.randint(2, max(3, bw - 8))
        near_rgb[top - 4:top, rx:rx + 6] = col
        near_a[top - 4:top, rx:rx + 6] = True
    for wy in range(top + 4, SILL, 5):
        for wx in range(x + 3, min(W - 2, x + bw - 3), 4):
            r = rnd.random()
            if r < 0.35:
                near_rgb[wy:wy + 2, wx:wx + 2] = rnd.choice([C("fee761"), C("feae34"), C("ead4aa")])
            elif r < 0.5:
                near_rgb[wy:wy + 2, wx:wx + 2] = C("181425")
    x += bw
outline(near_rgb, near_a, C("181425"))
STREET_Y = 276
near_rgb[STREET_Y - 2:STREET_Y + 4] = C("181425")
near_a[STREET_Y - 2:STREET_Y + 4] = True
for sx in range(4, W, 14):
    near_rgb[STREET_Y - 3, sx] = C("f77622")
cars = [(rnd.randrange(W), rnd.choice([1, -1]), rnd.uniform(1.2, 2.6)) for _ in range(14)]


# ---------------------------------------------------------------- Hochhäuser, die fallen
def build_tower(w, h, style, seed):
    r = random.Random(seed)
    extra = 40
    rgb = np.zeros((h + extra, w + 2, 3), np.float32)
    a = np.zeros((h + extra, w + 2), bool)
    top = extra
    x0, x1 = 1, w + 1
    body = C("262b44")
    if style == "stepped":
        segs = [(0, w, top + 30), (5, w - 5, top + 12), (11, w - 11, top)]
    elif style == "crown":
        segs = [(0, w, top + 8), (3, w - 3, top)]
    else:
        segs = [(0, w, top)]
    for sl, sr, sy in segs:
        rgb[sy:, x0 + sl:x0 + sr] = body
        a[sy:, x0 + sl:x0 + sr] = True
        rgb[sy:, x0 + sl] = C("3a4466")
        rgb[sy:, x0 + sl + 1] = C("3a4466")
    for yy in range(top + 3, h + extra - 2, 4):
        for xx in range(x0 + 3, x1 - 3, 4):
            if a[yy, xx] and a[yy - 3, xx]:
                q = r.random()
                c = C("fee761") if q < 0.2 else C("feae34") if q < 0.33 else C("ead4aa") if q < 0.4 else C("181425")
                rgb[yy:yy + 2, xx:xx + 2] = c
    cx = x0 + w // 2
    if style == "spire":
        for i in range(24):
            hw = max(0, (24 - i) * (w // 2) // 24)
            rgb[top - i, cx - hw:cx + hw + 1] = body
            a[top - i, cx - hw:cx + hw + 1] = True
        rgb[top - 36:top - 24, cx] = C("5a6988")
        a[top - 36:top - 24, cx] = True
    elif style == "antenna":
        rgb[top - 30:top, cx] = C("5a6988")
        a[top - 30:top, cx] = True
        rgb[top - 14:top, cx - 6] = C("5a6988")
        a[top - 14:top, cx - 6] = True
    elif style == "crown":
        rgb[top + 1:top + 4, x0 + 4:x1 - 4] = C("feae34")
        rgb[top + 10:top + 12, x0 + 1:x1 - 1] = C("fee761")
    oa = np.pad(a, 1)
    orgb = np.pad(rgb, ((1, 1), (1, 1), (0, 0)))
    outline(orgb, oa, C("181425"))
    return orgb, oa, extra + 1


# (Mitte x, Breite, Oberkante, Stil, Zündzeitpunkt)
TOWERS = [(74, 44, 64, "spire", 58), (142, 32, 96, "flat", 70), (256, 30, 96, "crown", 82),
          (360, 50, 52, "stepped", 94), (446, 36, 86, "antenna", 106)]
towers = []
for i, (cx, w, top, style, t0) in enumerate(TOWERS):
    rgb, a, extra = build_tower(w, BASE - top, style, i)
    towers.append(dict(cx=cx, w=w, top=top, h=BASE - top, rgb=rgb, a=a, extra=extra, t0=t0,
                       tc=t0 + 10, g=2 * (BASE - top + 40) / 44 ** 2,
                       charges=[(t0 + 2 * j, 0.18 + 0.2 * j, (-1) ** j) for j in range(4)],
                       puffs=[(random.Random(i * 100 + k).uniform(-1.3, 1.3),
                               random.Random(i * 100 + k + 50).uniform(0.2, 1.0),
                               random.Random(i * 100 + k + 70).randint(0, 22),
                               random.Random(i * 100 + k + 90).uniform(6, 13)) for k in range(60)]))


def tower_offset(t, f):
    if f < t["tc"]:
        return 0.0
    return 0.5 * t["g"] * (f - t["tc"]) ** 2


def draw_towers(fr, f):
    for t in towers:
        off = tower_offset(t, f)
        if off > t["h"] + t["extra"] + 4:
            continue
        rgb, a = t["rgb"], t["a"]
        hh, ww = a.shape
        x0 = t["cx"] - ww // 2
        y0 = BASE - hh + t["extra"] + 1 + int(off)
        # leichtes Zittern beim Einsturz
        if t["tc"] <= f:
            x0 += (1 if (f // 2) % 2 else -1)
        for yy in range(hh):
            y = y0 + yy
            if y < 0 or y >= BASE:
                continue
            row = a[yy]
            xs = slice(max(0, x0), min(W, x0 + ww))
            rs = slice(xs.start - x0, xs.stop - x0)
            m = row[rs]
            fr[y, xs][m] = rgb[yy, rs][m]
        # Lichter gehen stockwerksweise aus, sobald er fällt
        if f >= t["tc"]:
            k = min(1.0, (f - t["tc"]) / 10)
            ys = slice(max(0, y0), BASE)
            reg = fr[ys, max(0, x0):min(W, x0 + ww)]
            lit = (reg[..., 0] > 200) & (reg[..., 2] < 180)
            kill = lit & (np.random.default_rng(f).random(lit.shape) < k)
            reg[kill] = C("3e2731")


def fireball(rgb, a, cx, cy, age):
    if age < 0 or age > 13:
        return
    if age <= 7:
        r = 2 + age * 1.9
        for rr, col in ((r, "be4a2f"), (r * 0.78, "f77622"), (r * 0.55, "feae34"), (r * 0.3, "ffffff")):
            disc(rgb, a, cx, cy, rr, C(col))
    else:
        r = 11 - (age - 7) * 1.3
        disc(rgb, a, cx, cy, r, C("5a6988"))
        disc(rgb, a, cx - r * 0.15, cy - r * 0.25, r * 0.75, C("8b9bb4") if age > 9 else C("d77643"))


def draw_explosions(fr, f):
    """Feuerbälle, Staubwolken. Liefert die Blitzstärke für das Licht im Raum."""
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.zeros((H, W), bool)
    flash = 0.0
    glow = []
    for t in towers:
        off = tower_offset(t, f)
        for tj, frac, side in t["charges"]:
            age = f - tj
            y = BASE - frac * t["h"] + off
            if y < BASE:
                fireball(rgb, a, t["cx"] + side * (t["w"] // 2 + 2), y, age)
                fireball(rgb, a, t["cx"] - side * (t["w"] // 2 - 4), y + 3, age - 1)
            if frac < 0.2 and 0 <= age < 3:
                flash = max(flash, 1 - age / 3)
        age = f - t["tc"]
        if age >= 0:
            for dx, rise, delay, rmax in t["puffs"]:
                pa = age - delay
                if pa < 0:
                    continue
                grow = 1 - math.exp(-pa / 9)
                r = rmax * grow * (1 + 0.3 * min(1, pa / 60))
                px = t["cx"] + dx * t["w"] * (0.5 + grow)
                py = BASE - 2 - rise ** 2 * t["h"] * 0.45 * grow - pa * 0.06
                warm = pa < 14
                disc(rgb, a, px, py, r, C("be4a2f") if warm else C("5a6988"))
                disc(rgb, a, px - r * 0.15, py - r * 0.25, r * 0.8, C("d77643") if warm else C("8b9bb4"))
            if age < 60:
                glow.append((t["cx"], BASE - 6, 55 * (1 - age / 60)))
    outline(rgb, a, C("262b44"))
    fr[a] = rgb[a]
    return flash, glow


# ---------------------------------------------------------------- Innen: Büro (statisch)
room = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(room)
d.rectangle([0, 0, W - 1, GLASS_TOP - 1], fill=hexrgb("181425"))                  # Decke
for x in range(0, W, 64):
    d.line([x, 0, x, GLASS_TOP - 8], fill=hexrgb("262b44"))
d.rectangle([0, GLASS_TOP - 8, W - 1, GLASS_TOP - 1], fill=hexrgb("262b44"))
d.line([0, GLASS_TOP - 8, W, GLASS_TOP - 8], fill=hexrgb("3a4466"))
d.rectangle([0, SILL, W - 1, SILL + 6], fill=hexrgb("262b44"))                     # Brüstung
d.line([0, SILL, W, SILL], fill=hexrgb("5a6988"))
for mx in MULLIONS:
    d.rectangle([mx - 4, GLASS_TOP - 8, mx + 4, SILL + 6], fill=hexrgb("262b44"))
    d.line([mx - 4, GLASS_TOP - 8, mx - 4, SILL + 6], fill=hexrgb("5a6988"))
    d.line([mx + 4, GLASS_TOP - 8, mx + 4, SILL + 6], fill=hexrgb("181425"))
# umgekippter Bürostuhl: Lehne am Boden, Fuß mit Rollen ragt in die Luft
d.rounded_rectangle([34, 340, 66, 374], radius=6, fill=hexrgb("262b44"))                 # Lehne
d.rounded_rectangle([60, 358, 118, 374], radius=5, fill=hexrgb("3a4466"))               # Sitz
d.line([(66, 352), (72, 360)], fill=hexrgb("5a6988"), width=3)
d.line([(90, 358), (104, 330)], fill=hexrgb("5a6988"), width=4)                          # Gasfeder
for ang in range(5):
    a_ = -1.1 + ang * 0.62
    ex, ey = 104 + math.cos(a_) * 20, 330 + math.sin(a_) * 9 - 6
    d.line([(104, 330), (ex, ey)], fill=hexrgb("5a6988"), width=3)
    d.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=hexrgb("181425"))
# schiefe Topfpflanze
d.polygon([(438, 348), (470, 348), (466, 376), (442, 376)], fill=hexrgb("733e39"))
d.rectangle([436, 344, 472, 349], fill=hexrgb("b86f50"))
d.line([(454, 344), (458, 320), (470, 300), (486, 294)], fill=hexrgb("265c42"), width=3)
for lx, ly, ang in ((458, 324, -0.6), (466, 308, 0.5), (478, 298, -0.3), (488, 296, 0.9), (450, 334, 0.4)):
    d.polygon([(lx, ly), (lx + 14 * math.cos(ang), ly + 14 * math.sin(ang) + 4),
               (lx + 6 * math.cos(ang) + 3, ly + 10)], fill=hexrgb("3e8948"))
room_rgb, room_a = from_pil(room)
props = np.zeros((H, W), bool)
props[300:, :] = room_a[300:, :]
outline(room_rgb, room_a, C("181425"))
glass = np.zeros((H, W), bool)
glass[GLASS_TOP:SILL, :] = True
glass &= ~room_a


# ---------------------------------------------------------------- Figuren (von hinten)
def people(bn, bm, lean, cig_on):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = hexrgb
    # --- Der Erzähler (links): lang, dünn, Unterhemd, braune Stachelhaare
    dy = -bn
    hx = 214 + lean
    d.polygon([(201, 300), (213, 300), (212, 366), (202, 366)], fill=c("3a4466"))       # Hose
    d.polygon([(215, 300), (228, 300), (226, 366), (216, 366)], fill=c("3a4466"))
    d.line([(214, 304), (214, 360)], fill=c("262b44"))
    d.rectangle([198, 366, 213, 372], fill=c("181425"))
    d.rectangle([215, 366, 230, 372], fill=c("181425"))
    d.rectangle([200, 297, 229, 301], fill=c("262b44"))                                  # Gürtel
    d.ellipse([193, 238 + dy, 235, 256 + dy], fill=c("b86f50"))                          # Schultern
    d.polygon([(194, 246 + dy), (201, 248 + dy), (199, 300), (192, 300)], fill=c("b86f50"))  # linker Arm
    d.ellipse([189, 297, 199, 309], fill=c("c28569"))
    d.polygon([(228, 246 + dy), (235, 250 + dy), (257, 297), (250, 302)], fill=c("b86f50"))  # rechter Arm
    d.polygon([(199, 247 + dy), (229, 247 + dy), (231, 299), (199, 299)], fill=c("c0cbdc"))  # Unterhemd
    d.rectangle([203, 238 + dy, 207, 248 + dy], fill=c("c0cbdc"))
    d.rectangle([221, 238 + dy, 225, 248 + dy], fill=c("c0cbdc"))
    d.line([(214, 256 + dy), (214, 296)], fill=c("8b9bb4"))
    d.line([(207, 262 + dy), (206, 294)], fill=c("8b9bb4"))
    d.rectangle([208, 226 + dy, 220, 242 + dy], fill=c("b86f50"))                         # Hals
    d.ellipse([hx - 16, 214 + dy, hx - 10, 224 + dy], fill=c("b86f50"))                   # Ohren
    d.ellipse([hx + 10, 214 + dy, hx + 16, 224 + dy], fill=c("b86f50"))
    d.ellipse([hx - 13, 202 + dy, hx + 13, 232 + dy], fill=c("733e39"))                   # Hinterkopf
    for pts in [[(-12, 212), (-17, 198), (-7, 205)], [(-8, 206), (-6, 190), (0, 203)],
                [(-2, 204), (4, 188), (6, 203)], [(4, 205), (13, 193), (11, 210)], [(10, 210), (18, 204), (13, 216)]]:
        d.polygon([(hx + px, py + dy) for px, py in pts], fill=c("733e39"))
    d.line([(hx - 6, 212 + dy), (hx - 3, 226 + dy)], fill=c("3e2731"))
    d.line([(hx + 4, 210 + dy), (hx + 6, 224 + dy)], fill=c("3e2731"))
    # --- Marla (rechts): knochig, Wuschelmähne, dunkles Kleid, Zigarette
    dy = -bm
    mx = 300 - lean
    d.rectangle([291, 350, 297, 372], fill=c("181425"))                                  # Stiefel
    d.rectangle([302, 350, 308, 372], fill=c("181425"))
    d.rectangle([292, 318, 296, 350], fill=c("3e2731"))                                  # Strumpfhose
    d.rectangle([303, 318, 307, 350], fill=c("3e2731"))
    d.polygon([(260, 298), (284, 256 + dy), (290, 260 + dy), (268, 304)], fill=c("e8b796"))  # Arm zu ihm
    d.polygon([(312, 256 + dy), (318, 258 + dy), (323, 300), (316, 302)], fill=c("e8b796"))
    d.polygon([(284, 252 + dy), (316, 252 + dy), (322, 322), (278, 322)], fill=c("68386c"))  # Kleid
    d.line([(292, 262 + dy), (288, 320)], fill=c("3e2731"))
    d.line([(308, 262 + dy), (313, 320)], fill=c("3e2731"))
    d.ellipse([315, 297, 324, 306], fill=c("e8b796"))
    if cig_on is not None:
        d.line([(323, 302), (330, 299)], fill=c("ead4aa"), width=1)
        d.point((331, 299), fill=c("f77622") if cig_on else c("be4a2f"))
    # Mähne: viele Locken
    for ox, oy, r in [(-10, 0, 10), (10, 0, 10), (0, -8, 12), (-13, 14, 8), (13, 14, 8), (-7, -14, 7), (7, -14, 7),
                      (-16, 26, 6), (16, 26, 6), (0, 8, 12), (-5, 22, 7), (6, 22, 7)]:
        d.ellipse([mx + ox - r, 232 + oy + dy - r, mx + ox + r, 232 + oy + dy + r], fill=c("3e2731"))
    for ox, oy in [(-9, -6), (6, -12), (11, 4), (-12, 12), (2, 16), (-4, 0), (14, 20), (-15, 24)]:
        d.arc([mx + ox - 4, 232 + oy + dy - 4, mx + ox + 4, 232 + oy + dy + 4], 200, 340, fill=c("68386c"))
    # die verschränkten Hände
    d.ellipse([249, 294, 265, 306], fill=c("c28569"))
    d.line([(253, 298), (262, 298)], fill=c("b86f50"))
    d.line([(253, 301), (262, 301)], fill=c("b86f50"))
    rgb, a = from_pil(img)
    # Gegenlicht: innere Kante heller
    inner = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    idx = to_index(rgb)
    rgb[inner] = PAL[RIM[idx[inner]]]
    outline(rgb, a, C("181425"))
    return rgb, a


_people_cache = {}


def get_people(f):
    bn = 1 if math.sin(2 * math.pi * f / 50) > 0.3 else 0
    bm = 1 if math.sin(2 * math.pi * f / 44 + 1.3) > 0.3 else 0
    lean = 0 if f < 150 else min(3, (f - 150) // 5)
    cig = (f // 6) % 3 != 0
    key = (bn, bm, lean, cig)
    if key not in _people_cache:
        _people_cache[key] = people(bn, bm, lean, cig)
    return _people_cache[key]


# ---------------------------------------------------------------- Bild zusammensetzen
def iris(f):
    """Radius der Irisblende: auf am Anfang, zu am Ende."""
    if f < 14:
        return 330 * (f / 14) ** 1.6
    if f >= 188:
        return 0
    if f >= 168:
        return 330 * (1 - (f - 168) / 20) ** 1.6
    return 1000


def frame(f):
    fr = outside.copy()
    draw_towers(fr, f)
    fr[near_a] = near_rgb[near_a]
    for x0, dirn, sp in cars:                            # Verkehr
        x = int(x0 + dirn * sp * f) % W
        y = STREET_Y if dirn > 0 else STREET_Y + 2
        fr[y, x:x + 2] = C("fee761") if dirn > 0 else C("e43b44")
    flash, glow = draw_explosions(fr, f)
    # Scheibenspiegelung: ein paar diagonale Glanzlinien
    shine = glass & (((XX - YY) % 113 == 0) | ((XX - YY) % 113 == 3)) & (YY < 200)
    fr[shine] = fr[shine] * 0.7 + C("5a6988") * 0.3
    fr[room_a] = room_rgb[room_a]
    # Boden: gespiegelte Stadt in poliertem Stein
    floor = np.zeros((H, W, 3), np.float32)
    k = np.arange(SILL + 7, H)
    src = np.clip(2 * (SILL + 6) - k, GLASS_TOP, SILL - 1)
    floor[SILL + 7:] = fr[src]
    fl = np.zeros((H, W), bool)
    fl[SILL + 7:] = True
    fl &= ~room_a
    fr[fl] = floor[fl]
    prgb, pa = get_people(f)
    fr[pa] = prgb[pa]
    # Zigarettenrauch
    for t in range(22):
        y = 296 - t * 2
        x = int(332 + math.sin(t * 0.5 - f * 0.3) * (1 + t * 0.2))
        if (t + f // 2) % 3 and 0 <= y < H:
            fr[y, x] = C("8b9bb4") if t < 10 else C("5a6988")

    idx = to_index(fr)
    # Boden dunkler, jede zweite Zeile noch dunkler (poliert)
    idx[fl] = DARK[DARK[idx[fl]]]
    stripe = fl & (YY % 2 == 1)
    idx[stripe] = DARK[idx[stripe]]
    # Feuerschein am Himmel hinter den Wolken
    steps = np.zeros((H, W), np.int32)
    for gx, gy, gr in glow:
        if gr > 0:
            m = np.clip(1 - np.hypot(XX - gx, (YY - gy) * 1.3) / gr, 0, 1)
            steps = np.maximum(steps, np.round(dq(m, 1)).astype(np.int32) * (~room_a) * (~pa) * (YY < SILL))
    # Blitz der Sprengladungen erhellt alles, auch den Raum
    if flash > 0.3:
        steps += 1
    for s in (1, 2, 3):
        m = steps >= s
        idx[m] = LIGHT[idx[m]]
    # Irisblende
    r = iris(f)
    if r < 1000:
        idx[np.hypot(XX - 256, YY - 262) > r] = I["181425"]
    return idx


def render():
    pal = [int(v) for rgbv in PAL for v in rgbv] + [0] * (768 - 3 * len(PAL))
    out = []
    for f in range(N):
        im = Image.fromarray(frame(f).astype(np.uint8), "P")
        im.putpalette(pal)
        out.append(im.resize((W * SCALE, H * SCALE), Image.NEAREST))
    gif = HERE / "finale.gif"
    out[0].save(gif, save_all=True, append_images=out[1:], duration=MS, loop=0, disposal=1)
    out[118].convert("RGB").save(HERE / "finale.png")
    print(f"{gif}  {gif.stat().st_size / 1e6:.1f} MB, {N} Bilder, {N * MS / 1000:.0f} s")


if __name__ == "__main__":
    render()
