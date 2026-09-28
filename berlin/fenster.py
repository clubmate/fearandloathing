"""Berliner Nacht aus dem Fenster – ein Pixel-Loop.

Erzeugt berlin/fenster.gif (512x384 Pixel, 2x vergrößert, 150 Bilder à 80 ms, nahtlose Schleife)
und berlin/fenster.png (Standbild). Alles ist deterministisch: Jede Bewegung hat eine Periode,
die in 150 Bilder aufgeht.

    pip install pillow numpy
    python3 berlin/fenster.py
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 512, 384
N = 150          # Bilder pro Schleife
MS = 80          # ms pro Bild -> 12 s
SCALE = 2
HERE = Path(__file__).parent

rnd = random.Random(1989)
YY, XX = np.mgrid[0:H, 0:W]
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32
BAY = np.tile(BAYER4, (H // 4, W // 4)).astype(np.float32)


def C(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)


def dq(m, levels):
    """Maske geordnet gedithert auf wenige Stufen bringen – hält den Pixel-Look."""
    return np.clip(np.floor(m * levels + BAY[:m.shape[0], :m.shape[1]]) / levels, 0, 1)


def posterize(rgb, step=8):
    return np.clip(np.floor(rgb / step + BAY[..., None]) * step, 0, 255)


def blink(f, period, on, phase=0):
    return (f + phase) % period < on


class Layer:
    def __init__(self, fill=None):
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), bool)
        if fill is not None:
            self.rgb[:] = fill
            self.a[:] = True

    def rect(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W - 1, x1), min(H - 1, y1)
        if x0 <= x1 and y0 <= y1:
            self.rgb[y0:y1 + 1, x0:x1 + 1] = c
            self.a[y0:y1 + 1, x0:x1 + 1] = True

    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.rgb[y, x] = c
            self.a[y, x] = True

    def mask(self, m, c):
        self.rgb[m] = c
        self.a[m] = True


def over(dst, layer):
    dst[layer.a] = layer.rgb[layer.a]


# ---------------------------------------------------------------- Maße
# Glasscheiben (innen), dazwischen Holz
PANES = [(62, 32, 246, 88), (265, 32, 449, 88), (62, 108, 246, 296), (265, 108, 449, 296)]
DECK = 226                  # Oberkante Viadukt
STREET = DECK + 54          # Gehweg
TOWER_X = 200

# ---------------------------------------------------------------- Himmel (statisch)
sky = Layer(C("#06071a"))
stops = [(20, "#05061a"), (80, "#0a0c28"), (140, "#15153c"), (185, "#271d4c"), (215, "#452856"),
         (240, "#6a3858"), (270, "#7e4654")]
ys = np.array([s[0] for s in stops], float)
for ch in range(3):
    vals = np.array([C(s[1])[ch] for s in stops])
    sky.rgb[..., ch] = np.interp(YY, ys, vals)
sky.rgb = posterize(sky.rgb, 5)

# Mond (Sichel) mit Hof
MX, MY, MR = 404, 58, 15
d1 = np.hypot(XX - MX, YY - MY)
d2 = np.hypot(XX - (MX - 7), YY - (MY - 4))
halo = np.clip(1 - (d1 - MR) / 46, 0, 1) ** 2 * 0.22
sky.rgb += dq(halo, 6)[..., None] * C("#8a86b0")
lit = (d1 <= MR) & (d2 > MR - 1)
shade = np.clip((d2 - (MR - 1)) / 7, 0, 1)
moon = C("#b8b29a")[None] + dq(shade, 4)[lit][:, None] * (C("#f4eed2") - C("#b8b29a"))[None]
sky.rgb[lit] = moon
for cx, cy, r in [(412, 52, 2), (408, 66, 1.5), (416, 61, 1.2)]:
    m = lit & (np.hypot(XX - cx, YY - cy) <= r)
    sky.rgb[m] = C("#bdb498")
earth = (d1 <= MR) & ~lit
sky.rgb[earth] = sky.rgb[earth] * 0.8 + C("#20203a") * 0.2   # aschgraues Mondlicht

# Sterne
stars = []
for _ in range(170):
    x, y = rnd.randint(40, 470), int(20 + rnd.random() ** 1.4 * 190)
    if math.hypot(x - MX, y - MY) < 40:
        continue
    stars.append((x, y, rnd.random() ** 2, rnd.choice([1, 2, 3, 5]), rnd.random() * 6.28))
stars.sort(key=lambda s: s[2])


def draw_sky(fr, f):
    for x, y, b, k, ph in stars:
        tw = 0.55 + 0.45 * math.sin(2 * math.pi * k * f / N + ph)
        v = (0.25 + 0.75 * b) * tw
        c = np.array([150 + 100 * v, 150 + 100 * v, 190 + 65 * v]) * (0.45 + 0.55 * v)
        fr[y, x] = np.maximum(fr[y, x], c)
        if b > 0.93 and tw > 0.7:          # helle Sterne bekommen ein Kreuz
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                fr[y + dy, x + dx] = np.maximum(fr[y + dy, x + dx], c * 0.45)
    # dünne Wolkenschleier, jede Komponente läuft genau einmal pro Schleife herum
    y0, y1 = 120, 236
    yy, xx = YY[y0:y1], XX[y0:y1]
    t = f / N
    d = (np.sin(2 * np.pi * (6 * xx / W - t) + yy * 0.09) * 0.5
         + np.sin(2 * np.pi * (9 * xx / W - t) + 1.7 - yy * 0.05) * 0.35
         + np.sin(2 * np.pi * (13 * xx / W - t) + 4.1 + yy * 0.13) * 0.2
         + np.sin(2 * np.pi * (4 * xx / W - t) + 2.3) * 0.3)
    env = np.exp(-((yy - 185) / 26.0) ** 2)
    a = np.clip((d * 0.5 + 0.55) * env - 0.38, 0, 1) * 1.6
    a = np.clip(np.floor(np.clip(a, 0, 0.5) * 5 + BAY[y0:y1]) / 5, 0, 1)
    fr[y0:y1] = fr[y0:y1] * (1 - a[..., None]) + C("#6c4a6e")[None, None] * a[..., None]
    # Flugzeug im Landeanflug auf BER
    ax = int(30 + 440 * f / N)
    ay = int(128 - 22 * f / N)
    for i in range(7):
        fr[ay, ax + i] = C("#3a3a52")
    fr[ay - 1, ax] = C("#3a3a52")
    fr[ay + 1, ax + 3] = C("#2e2e44")
    if blink(f, 12, 2):
        fr[ay + 1, ax + 3] = C("#ff3030")
    if blink(f, 15, 1, 7):
        fr[ay, ax + 6] = C("#ffffff")
        fr[ay, ax + 7] = C("#9090b0")
    if blink(f, 12, 2, 6):
        fr[ay - 1, ax] = C("#ff5050")


# ---------------------------------------------------------------- Stadt (statisch)
city = Layer()
dyn = []          # Fenster, die sich bewegen
lights = []       # Warnlichter: (x, y, periode, an, phase, art)

WARM = [C("#ffcf78"), C("#f4b05e"), C("#ffe6b0"), C("#e89a52"), C("#d8f0c8")]
WIN_OFF = C("#100e1e")


def window_block(w, h, style, kind, seed, color, f=0):
    r = random.Random(seed)
    blk = np.zeros((h, w, 3), np.float32)
    if kind == "off":
        blk[:] = WIN_OFF
        blk[0, 0] = C("#2a2850")
        if w > 3 and h > 3:
            blk[1, 1] = C("#1e1c3c")
    elif kind == "tv":
        tv = [C("#3a5ac8"), C("#6a8cf0"), C("#2a3c90"), C("#9ab4ff"), C("#4a4aa8")]
        blk[:] = tv[(f // 2 * 7 + f // 3 + seed) % 5] * 0.8
        blk[h - 2:, :] *= 0.6
    else:
        blk[:] = color
        blk[h // 2:, :] *= 0.92
        if r.random() < 0.5 and w >= 5:           # Vorhänge
            blk[:, 0] *= 0.7
            blk[:, -1] *= 0.7
        if r.random() < 0.25 and h >= 5:          # Jalousie
            blk[1::2, :] *= 0.8
        if r.random() < 0.35 and h >= 6:          # Pflanze auf dem Fensterbrett
            for i in range(r.randint(1, 3)):
                x = r.randrange(w)
                blk[h - 1 - r.randint(0, 2):, x] = C("#2a2418")
        if r.random() < 0.3:                      # Lampe
            blk[0, w // 2] = np.minimum(color * 1.25, 255)
        if kind == "person":                      # jemand läuft durchs Zimmer
            p = (f * 2 // 3 + seed) % (w + 12) - 4
            for yy in range(2, h):
                for dx in range(-1, 2):
                    x = p + dx
                    if 0 <= x < w and not (yy == 2 and dx != 0):
                        blk[yy, x] = color * 0.3
    if style == "alt":
        frame_c = C("#3a3044") if kind != "off" else C("#241e32")
        blk[:, w // 2] = frame_c
        blk[h // 3, :] = frame_c
    elif style == "platte":
        blk[:, w - 3] = C("#2a2840") if kind == "off" else blk[:, w - 3] * 0.55
    return blk


def add_window(x, y, w, h, style, p_on=0.45, p_dyn=0.12):
    r = rnd.random()
    color = rnd.choice(WARM[:4]) if rnd.random() > 0.08 else WARM[4]
    seed = rnd.randrange(10_000)
    if r < p_dyn:
        kind = rnd.choice(["toggle", "toggle", "tv", "person"])
        dyn.append((x, y, w, h, style, kind, seed, color, rnd.choice([30, 50, 75, 150]), rnd.randrange(N)))
        kind = "off"
    else:
        kind = "on" if r < p_dyn + p_on else "off"
    city.rgb[y:y + h, x:x + w] = window_block(w, h, style, kind, seed, color)
    city.a[y:y + h, x:x + w] = True


# ferne Silhouette
x = 40
while x < 480:
    bw = rnd.randint(8, 26)
    top = rnd.randint(178, 222)
    col = rnd.choice([C("#221e3e"), C("#252142"), C("#1f1b3a"), C("#282446")])
    city.rect(x, top, x + bw - 1, DECK, col)
    city.rect(x, top, x + bw - 1, top, col + 12)
    if rnd.random() < 0.3:
        ax = x + rnd.randrange(bw)
        city.rect(ax, top - rnd.randint(4, 12), ax, top, col)
    elif rnd.random() < 0.3:
        city.rect(x + 2, top - 3, x + 6, top - 1, col)
    for wy in range(top + 3, DECK - 2, 4):
        for wx in range(x + 2, x + bw - 2, 3):
            r = rnd.random()
            if r < 0.1:
                c = rnd.choice([C("#8a6a4c"), C("#6c5a58"), C("#5a5a80")])
                city.px(wx, wy, c)
                if rnd.random() < 0.5:
                    city.px(wx + 1, wy, c)
            elif r < 0.115:
                dyn.append((wx, wy, 2, 1, "far", "toggle", 0, C("#9a7a52"),
                            rnd.choice([50, 75, 150]), rnd.randrange(N)))
    x += bw

# Park Inn am Alex
city.rect(216, 156, 236, DECK, C("#211d3c"))
city.rect(216, 156, 236, 157, C("#2e2a4e"))
for wy in range(160, DECK, 3):
    for wx in range(218, 235, 2):
        if rnd.random() < 0.22:
            city.px(wx, wy, rnd.choice([C("#7a6a58"), C("#5c6284"), C("#8a7050")]))
lights += [(216, 155, 50, 25, 0, "r"), (236, 155, 50, 25, 25, "r")]


def crane(mx, top, jl, jr, jy, light_phase):
    ccol = C("#2c2848")
    for y in range(top, DECK):
        city.px(mx, y, ccol)
        city.px(mx + 3, y, ccol)
        city.px(mx + (y - top) % 4, y, ccol)
        if (y - top) % 4 == 0:
            city.rect(mx, y, mx + 3, y, ccol)
    for x in range(jl, jr + 1):
        city.px(x, jy, ccol)
        city.px(x, jy + 2, ccol)
        if (x - jl) % 3 == 0:
            city.px(x, jy + 1, ccol)
    for i in range(0, 9):                # Turmspitze
        city.px(mx + 1, jy - i, ccol)
        city.px(mx + 2, jy - i, ccol)
    for x in range(jl, mx):              # Abspannung
        city.px(x, jy - 8 + int((mx - x) * 7 / max(1, mx - jl)), ccol)
    for x in range(mx + 3, jr):
        city.px(x, jy - 8 + int((x - mx) * 7 / max(1, jr - mx)), ccol)
    city.rect(mx - 8, jy + 1, mx - 3, jy + 5, ccol)          # Gegengewicht
    city.rect(mx + 4, jy + 3, mx + 7, jy + 6, C("#35305a"))  # Kabine
    lights.append((mx + 1, jy - 9, 30, 12, light_phase, "r"))
    lights.append((jr, jy - 1, 30, 12, light_phase + 15, "r"))


crane(374, 146, 322, 452, 144, 0)

# Fernsehturm
tc, tl, th = C("#3e3c62"), C("#2e2c4c"), C("#5c5a88")
for y in range(156, DECK):
    w = 7 + (y - 156) * 6 / (DECK - 156)
    x0, x1 = int(round(TOWER_X - w / 2)), int(round(TOWER_X + w / 2))
    city.rect(x0, y, x1, y, tc)
    city.px(x0, y, tl)
    city.px(x1, y, th)
    city.px(x1 - 1, y, th * 0.9)
city.rect(TOWER_X - 5, 152, TOWER_X + 5, 156, tc)
city.rect(TOWER_X - 3, 150, TOWER_X + 3, 152, tl)
SPH = (TOWER_X, 136, 16)
sx, sy, sr = SPH
d = np.hypot(XX - sx, YY - sy)
m = d <= sr
nz = np.sqrt(np.clip(sr ** 2 - (XX - sx) ** 2 - (YY - sy) ** 2, 0, None)) / sr
nx, ny = (XX - sx) / sr, (YY - sy) / sr
shade = np.clip(nx * 0.55 - ny * 0.45 + nz * 0.7, 0, 1)
lv = dq(shade, 4)
pal = [C("#26244a"), C("#3a3864"), C("#55537e"), C("#7c7aa8"), C("#a6a4cc")]
for i, c in enumerate(pal):
    city.mask(m & (np.round(lv * 4) == i), c)
lon = np.arcsin(np.clip(nx / np.maximum(np.sqrt(np.clip(1 - ny ** 2, 0, 1)), 1e-3), -1, 1))
grid = m & ((np.abs(np.sin(lon * 7)) < 0.18) | ((YY - sy) % 5 == 0)) & (d < sr - 1)
city.rgb[grid] *= 0.78
city.rect(sx - 15, sy + 2, sx + 15, sy + 4, C("#1c1a30"))      # Fensterband (Telecafé)
city.rect(TOWER_X - 2, 104, TOWER_X + 2, sy - sr, tc)
city.rect(TOWER_X + 1, 104, TOWER_X + 2, sy - sr, th)
city.rect(TOWER_X - 3, 100, TOWER_X + 3, 103, tl)
for y in range(44, 100):
    w = 1 if y > 80 else 0
    stripe = C("#8a2a34") if (y // 6) % 2 else C("#8a8aa4")
    city.rect(TOWER_X - w, y, TOWER_X + w, y, stripe * 0.8)
lights += [(TOWER_X, 43, 30, 8, 0, "R"), (TOWER_X, 80, 30, 8, 0, "r"), (TOWER_X, 101, 30, 8, 0, "r"),
           (TOWER_X - 6, 150, 30, 8, 15, "r"), (TOWER_X + 6, 150, 30, 8, 15, "r"),
           (TOWER_X - 5, 190, 30, 8, 15, "r")]

# Plattenbau (WBS 70)
PX0, PX1, PTOP = 298, 440, 108
panel, joint = C("#2b2a46"), C("#22213a")
city.rect(PX0, PTOP, PX1, DECK, panel)
city.rect(PX0 - 1, PTOP - 2, PX1 + 1, PTOP, C("#3a3858"))
city.rect(330, 94, 352, PTOP - 3, C("#27263f"))
city.rect(330, 94, 352, 94, C("#3a3858"))
city.rect(426, 78, 426, PTOP - 3, C("#27263f"))
city.rect(422, 90, 430, 90, C("#27263f"))
lights.append((426, 77, 50, 25, 10, "r"))
lights.append((331, 93, 50, 25, 35, "r"))
UW, FH = 13, 11
floors = list(range(PTOP + 2, DECK - 4, FH))
stair = []
for fi, fy in enumerate(floors):
    city.rect(PX0, fy - 1, PX1, fy - 1, joint)
    for ui, ux in enumerate(range(PX0 + 1, PX1 - UW + 2, UW)):
        city.rect(ux - 1, fy, ux - 1, fy + FH - 2, joint)
        if ui == 6:                          # Treppenhaus
            stair.append((ux + 5, fy + 3, 3, 4))
            city.rect(ux + 5, fy + 3, ux + 7, fy + 6, WIN_OFF)
            continue
        loggia = ui in (2, 3, 8)
        add_window(ux + 2, fy + 2, 9, 6, "platte", p_on=0.42, p_dyn=0.1)
        if loggia:
            city.rect(ux, fy + 6, ux + UW - 2, fy + 9, C("#3a3858"))
            city.rect(ux, fy + 6, ux + UW - 2, fy + 6, C("#4a4868"))
            if rnd.random() < 0.3:
                bx = ux + 2 + rnd.randrange(6)
                city.rect(bx, fy + 4, bx + 1, fy + 5, C("#20303a"))
        else:
            city.rect(ux + 2, fy + 8, ux + 10, fy + 8, C("#34324f"))
for _ in range(9):                            # Satellitenschüsseln
    fi = rnd.randrange(len(floors))
    ux = PX0 + 1 + UW * rnd.randrange(10)
    city.rect(ux + 9, floors[fi] + 3, ux + 10, floors[fi] + 4, C("#6a6a80"))


def altbau(x0, x1, top, facade, floor_h, cols, win_w=6, win_h=11, roof_h=16, dormers=True):
    roof = C("#1c1828")
    for y in range(top - roof_h, top):
        ins = int((top - y) * 0.35)
        city.rect(x0 + ins, y, x1 - ins, y, roof)
    city.rect(x0 - 1, top, x1 + 1, top + 1, facade + 16)
    city.rect(x0, top + 2, x1, DECK, facade)
    for i, cx in enumerate(cols):
        if dormers and i % 2 == 0:
            dy = top - roof_h + 5
            city.rect(cx - 1, dy, cx + win_w, top - 1, roof + 6)
            city.rect(cx - 2, dy - 1, cx + win_w + 1, dy - 1, roof + 14)
            add_window(cx + 1, dy + 2, win_w - 2, 6, "far", p_on=0.35, p_dyn=0.0)
    for cx in (x0 + 5, x1 - 10):              # Schornsteine
        city.rect(cx, top - roof_h - 7, cx + 4, top - roof_h + 2, facade - 6)
        city.rect(cx - 1, top - roof_h - 8, cx + 5, top - roof_h - 7, facade + 6)
    for fy in range(top + 5, DECK - 4, floor_h):
        city.rect(x0, fy - 3, x1, fy - 3, facade + 10)       # Gesims
        for cx in cols:
            city.rect(cx - 1, fy - 1, cx + win_w, fy - 1, facade + 18)  # Verdachung
            add_window(cx, fy, win_w, win_h, "alt", p_on=0.4, p_dyn=0.12)
            city.rect(cx - 1, fy + win_h, cx + win_w, fy + win_h, facade + 8)
        if rnd.random() < 0.5:                                          # Balkon
            cx = cols[len(cols) // 2]
            by = fy + win_h + 1
            city.rect(cx - 5, by, cx + win_w + 4, by + 1, facade + 14)
            for bx in range(cx - 5, cx + win_w + 5, 2):
                city.rect(bx, by - 5, bx, by - 1, C("#141020"))
            city.rect(cx - 5, by - 6, cx + win_w + 4, by - 6, C("#141020"))


altbau(40, 118, 172, C("#2e2638"), 17, [46, 60, 74, 88, 102])
altbau(120, 176, 186, C("#382c42"), 17, [126, 140, 154, 168], roof_h=12)
altbau(442, 482, 170, C("#2a2436"), 17, [448, 462], dormers=False)

# niedrige Gewerbebauten + Straßenbäume
city.rect(178, 212, 296, DECK, C("#1e1a34"))
city.rect(178, 212, 296, 212, C("#2a2644"))
for wx in range(182, 292, 9):
    add_window(wx, 216, 5, 4, "far", p_on=0.3, p_dyn=0.0)
for tx, ty, tr in [(188, 214, 16), (226, 208, 19), (262, 214, 17), (292, 210, 15), (140, 212, 14)]:
    m = np.hypot(XX - tx, (YY - ty) * 1.15) <= tr + (np.sin(XX * 1.7) + np.cos(YY * 2.3)) * 1.8
    m &= YY <= DECK
    city.mask(m, C("#101a1c"))
    hi = m & (np.hypot(XX - tx - 4, YY - ty - 5) <= tr * 0.6) & ((XX * 3 + YY * 5) % 7 < 3)
    city.mask(hi, C("#1a2a26"))

# S-Bahn-Viadukt aus Backstein
brick_y0 = DECK + 4
row = (YY - brick_y0) // 3
off = (row % 2) * 4
bxi = (XX + off) // 8
hsh = ((bxi * 73856093) ^ (row * 19349663)) % 7
brick = C("#58302e")[None, None] + (hsh[..., None] - 3) * np.array([3.5, 1.8, 1.8])
mortar = ((YY - brick_y0) % 3 == 2) | ((XX + off) % 8 == 7)
bricks = np.where(mortar[..., None], C("#361e22"), brick)
vi = (YY >= DECK) & (YY < STREET)
city.rgb[vi] = bricks[vi]
city.a[vi] = True
city.rect(0, DECK, W - 1, DECK + 3, C("#6c4640"))
city.rect(0, DECK, W - 1, DECK, C("#8a5c52"))
city.rect(0, DECK + 3, W - 1, DECK + 3, C("#3a2224"))

P, PW, R = 56, 14, 20
arch_cy = DECK + 36
arches = []
for j in range(-1, 10):
    x0 = 18 + j * P + PW
    x1 = x0 + P - PW - 1
    cx = (x0 + x1) / 2
    arches.append((x0, x1, cx))
    dd = np.hypot(XX - cx, YY - arch_cy)
    opening = (((XX >= x0) & (XX <= x1) & (YY >= arch_cy)) | ((dd <= R + 0.5) & (YY < arch_cy))) & (YY < STREET)
    ring = (dd > R + 0.5) & (dd <= R + 4) & (YY < arch_cy + 1) & (YY >= DECK + 4)
    ang = np.arctan2(YY - arch_cy, XX - cx)
    rb = ((ang * 9).astype(int) % 2 == 0)
    city.mask(ring & rb, C("#66383a"))
    city.mask(ring & ~rb, C("#5a3232"))
    depth = np.clip((YY - (arch_cy - R)) / 60, 0, 1)
    inner = C("#0a0812")[None, None] + (1 - depth)[..., None] * C("#06040a")[None, None]
    city.rgb[opening] = inner[opening]
    city.a[opening] = True
    city.rect(x0 - 1, arch_cy - 1, x0 - 1, arch_cy, C("#7a4c46"))
    city.rect(x1 + 1, arch_cy - 1, x1 + 1, arch_cy, C("#7a4c46"))


def arch_mask(k):
    x0, x1, cx = arches[k]
    return (XX >= x0) & (XX <= x1) & (YY < STREET) & (
        (YY >= arch_cy) | (np.hypot(XX - cx, YY - arch_cy) <= R + 0.5))


# Späti im Bogen
SX0, SX1, SCX = arches[5]
city.mask(arch_mask(5), C("#3a2a22"))
city.rect(SX0 + 2, arch_cy - 6, SX1 - 2, STREET - 1, C("#c89a5a"))            # Schaufenster
for sy_ in (arch_cy - 2, arch_cy + 5, arch_cy + 12):
    city.rect(SX0 + 3, sy_, SX1 - 3, sy_, C("#6a4a2a"))
    for x in range(SX0 + 3, SX1 - 2, 2):
        c = rnd.choice([C("#3a7a3a"), C("#c83a2a"), C("#e8d0a0"), C("#2a4a8a"), C("#8a5a2a"), C("#e0b020")])
        city.rect(x, sy_ - 3, x, sy_ - 1, c)
        if rnd.random() < 0.5:
            city.px(x, sy_ - 4, c * 0.8)
city.rect(SX1 - 12, arch_cy - 4, SX1 - 4, STREET - 1, C("#e8c890"))          # Tür
city.rect(SX1 - 12, arch_cy - 4, SX1 - 12, STREET - 1, C("#4a3a2a"))
city.rect(SX0 + 2, STREET - 6, SX1 - 14, STREET - 6, C("#5a4030"))
FONT = {"S": ["111", "100", "111", "001", "111"], "P": ["111", "101", "111", "100", "100"],
        "Ä": ["010", "101", "111", "101", "101"], "T": ["111", "010", "010", "010", "010"],
        "I": ["1", "1", "1", "1", "1"]}
neon = []
nx0, ny0 = int(SCX) - 9, arch_cy - 14
for ch in "SPÄTI":
    for yy, rowbits in enumerate(FONT[ch]):
        for xx, b in enumerate(rowbits):
            if b == "1":
                neon.append((nx0 + xx, ny0 + yy))
    if ch == "Ä":
        neon += [(nx0, ny0 - 2), (nx0 + 2, ny0 - 2)]
    nx0 += len(FONT[ch][0]) + 1

# Bar im Bogen
BX0, BX1, BCX = arches[8]
bar = arch_mask(8)
glowb = np.clip(1 - np.hypot(XX - BCX, YY - (arch_cy + 6)) / 30, 0, 1)
city.rgb[bar] = C("#1a1238")[None] + dq(glowb, 5)[bar][:, None] * C("#5a3aa8")[None]
city.a[bar] = True
for hx in (BX0 + 8, BX0 + 14, BX1 - 9):
    city.rect(hx, STREET - 12, hx + 3, STREET - 1, C("#0c0818"))
    city.rect(hx, STREET - 15, hx + 2, STREET - 13, C("#0c0818"))
city.rect(BX0 + 3, arch_cy - 8, BX0 + 3, STREET - 1, C("#ff4ab0"))

# Graffiti an den Pfeilern
for j in range(0, 10):
    x0 = 18 + j * P
    for _ in range(rnd.randint(4, 14)):
        c = rnd.choice([C("#c04a8a"), C("#4aa0c0"), C("#d8d0b0"), C("#80c040"), C("#e08a30")]) * 0.6
        gx = x0 + rnd.randint(1, PW - 2)
        gy = STREET - rnd.randint(3, 14)
        city.rect(gx, gy, gx + rnd.randint(0, 2), gy, c)

# Gehweg und Straße
city.rect(0, STREET, W - 1, STREET + 5, C("#24202e"))
city.rect(0, STREET, W - 1, STREET, C("#302a3a"))
city.rect(0, STREET + 5, W - 1, STREET + 5, C("#3a3444"))
city.rect(0, STREET + 6, W - 1, H - 1, C("#15131c"))
for x in range(0, W, 20):
    city.rect(x, STREET + 12, x + 9, STREET + 12, C("#34303a"))

# Gaslaternen
LAMPS = [110, 232, 352, 452]
for lx in LAMPS:
    post = C("#1a1822")
    top = STREET - 44
    for i in range(12):
        w = 3 + (i * 3) // 11
        city.rect(lx - w + 1, top + i, lx + w, top + i, C("#f8e8b0") if 1 < i < 11 else post)
    city.rect(lx - 5, top - 1, lx + 6, top, post)
    city.rect(lx - 2, top - 4, lx + 3, top - 2, post)
    city.rect(lx, top + 1, lx + 1, top + 10, post)
    city.rect(lx - 4, top + 11, lx + 5, top + 12, post)
    city.rect(lx - 1, top + 13, lx + 2, STREET - 20, post)
    city.rect(lx, STREET - 20, lx + 1, H - 1, post)
    city.rect(lx - 1, STREET + 2, lx + 2, H - 1, post)

# Lichtschein: Laternen, Späti, Bar
glow = np.zeros((H, W), np.float32)
for lx in LAMPS:
    glow += np.clip(1 - np.hypot(XX - lx, (YY - (STREET - 38)) * 1.2) / 40, 0, 1) ** 2 * 0.55
    glow += np.clip(1 - np.hypot(XX - lx, (YY - (STREET + 6)) * 3.5) / 34, 0, 1) ** 1.5 * 0.45
city.rgb += dq(np.clip(glow, 0, 1), 7)[..., None] * C("#c89048")[None, None]
sg = np.clip(1 - np.hypot(XX - SCX, (YY - (STREET + 4)) * 2.5) / 40, 0, 1) ** 1.5 * 0.5
city.rgb += (dq(sg, 5) * (YY >= STREET))[..., None] * C("#d8a060")[None, None]
bgl = np.clip(1 - np.hypot(XX - BCX, (YY - (STREET + 4)) * 2.5) / 34, 0, 1) ** 1.5 * 0.4
city.rgb += (dq(bgl, 5) * (YY >= STREET))[..., None] * C("#6a4ac0")[None, None]
city.rgb = np.clip(city.rgb, 0, 255)

# Geländer oben auf dem Viadukt (vor dem Zug)
rail = Layer()
rail.rect(0, DECK - 9, W - 1, DECK - 9, C("#2a2434"))
rail.rect(0, DECK - 2, W - 1, DECK - 1, C("#1c1824"))
for x in range(0, W, 7):
    rail.rect(x, DECK - 9, x, DECK - 1, C("#1c1824"))
for x in range(3, W, 84):
    rail.rect(x, DECK - 16, x + 1, DECK - 1, C("#221e2c"))


# ---------------------------------------------------------------- S-Bahn (Sprite, Baureihe 481)
def build_train():
    car_len, cars, gap = 102, 2, 4
    L = car_len * cars + gap
    rgb = np.zeros((30, L, 3), np.float32)
    a = np.zeros((30, L), bool)
    r = random.Random(481)
    roof, ochre, red, dark = C("#56505e"), C("#c8962a"), C("#a01e28"), C("#2a1a1e")
    lit = C("#f2e0a8")
    for c in range(cars):
        x0 = c * (car_len + gap)
        rgb[2:4, x0:x0 + car_len] = roof
        rgb[4:16, x0:x0 + car_len] = ochre
        rgb[16:27, x0:x0 + car_len] = red
        rgb[27:30, x0:x0 + car_len] = dark
        rgb[4, x0:x0 + car_len] = ochre * 1.12
        rgb[16, x0:x0 + car_len] = red * 0.8
        a[2:30, x0:x0 + car_len] = True
        x = x0
        for item in [6, "w", 3, "w", "d", "w", 3, "w", "d", "w", 3, "w", 3]:
            if item == "w":
                rgb[6:15, x:x + 10] = lit
                rgb[6, x:x + 10] = lit * 0.85
                for _ in range(r.randint(0, 2)):          # Fahrgäste
                    hx = x + r.randint(1, 7)
                    rgb[9:12, hx:hx + 2] = C("#5a4430")
                    rgb[12:15, hx - 1:hx + 3] = C("#4a3a30")
                x += 10
            elif item == "d":
                rgb[4:27, x:x + 12] = red
                rgb[4:27, x + 6] = red * 0.6
                rgb[7:16, x + 2:x + 5] = lit
                rgb[7:16, x + 8:x + 11] = lit
                rgb[4:27, x] = red * 0.7
                rgb[4:27, x + 11] = red * 0.7
                x += 12
            else:
                x += item
        for y in range(2, 8):                             # Stirnseiten abrunden
            k = (8 - y) // 2
            a[y, x0:x0 + k] = False
            a[y, x0 + car_len - k:x0 + car_len] = False
    rgb[5:13, 1:5] = C("#3a4a6a")                          # Frontscheibe
    rgb[5, 1:5] = C("#6a7a9a")
    rgb[21:23, 1:3] = C("#fffbe0")                         # Scheinwerfer
    rgb[21:23, L - 3:L - 1] = C("#ff2a2a")                 # Schlusslicht
    rgb[18:22, car_len:car_len + gap] = C("#1a1216")       # Kupplung
    a[18:22, car_len:car_len + gap] = True
    return rgb, a, L


train_rgb, train_a, TL = build_train()


def draw_train(fr, f):
    x = int(W + 30 - (W + TL + 90) * f / N)
    y = DECK - 30
    x0, x1 = max(0, x), min(W, x + TL)
    if x0 >= x1:
        return
    sub = train_a[:, x0 - x:x1 - x]
    fr[y:y + 30, x0:x1][sub] = train_rgb[:, x0 - x:x1 - x][sub]
    beam = np.clip(1 - np.hypot((XX - x) / 60, (YY - (y + 22)) / 5), 0, 1) * (XX < x) * (YY < DECK + 4)
    fr += dq(beam * 0.5, 5)[..., None] * C("#fff0c0")[None, None]
    fr[DECK:DECK + 3, x0:x1] += C("#403018")               # Fensterlicht auf dem Gesims
    if blink(f, 9, 1) and 0 <= x + 60 < W:                 # Funke an der Stromschiene
        fr[DECK - 1:DECK + 1, x + 60] = C("#c0d0ff")


# Taxi
def build_car():
    w, h = 38, 15
    rgb = np.zeros((h, w, 3), np.float32)
    a = np.zeros((h, w), bool)
    body, dark = C("#d8cea6"), C("#141018")
    for y in range(4, 8):
        k = 7 - y
        rgb[y, 9 + k:30 - k] = body * 0.9
        a[y, 9 + k:30 - k] = True
    rgb[5:8, 12:18] = C("#2a3040")
    rgb[5:8, 20:27] = C("#2a3040")
    rgb[5:7, 13:15] = C("#e0c890") * 0.6
    rgb[8:12, 1:37] = body
    a[8:12, 1:37] = True
    rgb[8, 1:37] = body * 1.08
    rgb[11, 1:37] = body * 0.7
    rgb[2:4, 17:22] = C("#ffd24a")                        # Taxischild
    a[2:4, 17:22] = True
    for wx in (7, 28):
        rgb[11:15, wx - 3:wx + 3] = dark
        a[11:15, wx - 3:wx + 3] = True
        rgb[12:14, wx - 1:wx + 1] = C("#6a6470")
    rgb[9:11, 36:38] = C("#fffbe0")
    a[9:11, 36:38] = True
    rgb[9:11, 0:1] = C("#ff2020")
    a[9:11, 0:1] = True
    return rgb, a, w, h


car_rgb, car_a, CW, CH = build_car()


def draw_car(fr, f):
    x = int(-70 + (W + 140) * ((f + N // 2) % N) / N)
    y = STREET + 7
    x0, x1 = max(0, x), min(W, x + CW)
    if x0 < x1:
        sub = car_a[:, x0 - x:x1 - x]
        fr[y:y + CH, x0:x1][sub] = car_rgb[:, x0 - x:x1 - x][sub]
    beam = np.clip(1 - np.hypot((XX - (x + CW)) / 70, (YY - (y + 10)) / 6), 0, 1) * (XX > x + CW)
    beam *= (YY >= STREET + 6)
    fr += dq(beam * 0.45, 5)[..., None] * C("#fff0c0")[None, None]


def draw_dynamic(fr, f):
    for x, y, w, h, style, kind, seed, color, per, ph in dyn:
        if kind == "toggle":
            k = "on" if (f + ph) % per < per * 0.6 else "off"
        else:
            k = kind
        if style == "far":
            fr[y:y + h, x:x + w] = color if k == "on" else C("#2a2442")
        else:
            fr[y:y + h, x:x + w] = window_block(w, h, style, k, seed, color, f)
    # Treppenhauslicht mit Zeitschalter: jemand läuft nach oben
    n = len(stair)
    for i, (x, y, w, h) in enumerate(stair):
        fl = n - 1 - i                       # 0 = unten
        step = (f - 20) // 7
        on = 20 <= f < 120 and step - 4 <= fl <= step
        fr[y:y + h, x:x + w] = C("#e8f0e0") if on else WIN_OFF
    # Warnlichter
    for x, y, per, on, ph, kind in lights:
        if blink(f, per, on, ph):
            c = C("#ff3a3a")
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                fr[y + dy, x + dx] = np.maximum(fr[y + dy, x + dx], c * 0.5)
            fr[y, x] = c
            if kind == "R":
                fr[y - 2:y + 3, x] = np.maximum(fr[y - 2:y + 3, x], c * 0.35)
                fr[y, x] = C("#ffb0a0")
        else:
            fr[y, x] = C("#5a1a22")
    # Fensterring der Turmkugel dreht sich (das Telecafé rotiert wirklich)
    sx, sy, sr = SPH
    for xx in range(sx - 13, sx + 14):
        lamp = ((xx - sx) * 2 + f // 3) % 5 < 3
        fr[sy + 3, xx] = C("#e8c480") * (0.9 if lamp else 0.45)
    # Neon am Späti, flackert ab und zu
    on = not (f % 50 in (7, 9, 31) or f % 75 in (60, 61))
    for x, y in neon:
        fr[y, x] = C("#ff6ab8") if on else C("#6a2a4a")
    if on:
        for x, y in neon:
            fr[y - 1:y + 2, x - 1:x + 2] = np.maximum(fr[y - 1:y + 2, x - 1:x + 2], C("#6a2448"))
        for x, y in neon:
            fr[y, x] = C("#ffb0d8")


# ---------------------------------------------------------------- Zimmer
room = Layer(C("#15111b"))
wallp = ((XX % 16) < 3) | (((XX + 8) % 16 == 0) & ((YY % 16) < 3))
room.rgb[wallp] = C("#1a1520")
room.rgb[((XX % 16) == 8) & ((YY % 16) == 8)] = C("#211a28")

# Fensterlaibung, Rahmen, Flügel
wood, wood_hi, wood_lo, wood_line = C("#322e3c"), C("#443f50"), C("#221e29"), C("#15121a")
room.rect(36, 8, 475, 305, wood)
room.rect(36, 8, 475, 9, wood_hi)
room.rect(36, 8, 37, 305, wood_hi)
room.rect(474, 8, 475, 305, wood_lo)
room.rect(44, 16, 467, 305, wood_lo)
room.rect(46, 18, 465, 305, wood)
for (x0, y0, x1, y1) in PANES:
    room.rect(x0 - 8, y0 - 8, x1 + 8, y1 + 8, wood)
    room.rect(x0 - 8, y0 - 8, x1 + 8, y0 - 8, wood_hi)
    room.rect(x0 - 8, y0 - 8, x0 - 8, y1 + 8, wood_hi)
    room.rect(x1 + 8, y0 - 8, x1 + 8, y1 + 8, wood_lo)
    room.rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3, wood_hi * 0.95)
    room.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, wood_lo)
    room.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, wood_line)
glass = np.zeros((H, W), bool)
for x0, y0, x1, y1 in PANES:
    glass[y0:y1 + 1, x0:x1 + 1] = True
room.rect(255, 100, 256, 304, wood_line)                    # Mittelstoß
room.rect(254, 100, 254, 304, wood_hi)
room.rect(46, 97, 465, 97, wood_line)                        # Kämpfer
room.a[glass] = False
# Farbabplatzer
for _ in range(220):
    x, y = rnd.randint(36, 475), rnd.randint(8, 305)
    if room.a[y, x] and not glass[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any():
        room.rgb[y, x] = room.rgb[y, x] * rnd.choice([0.85, 1.12])
# Fenstergriff (Olive)
brass, brass_hi = C("#7a6038"), C("#c8a860")
room.rect(252, 192, 259, 200, brass)
room.rect(253, 193, 255, 194, brass_hi)
room.rect(255, 200, 256, 222, brass)
room.rect(255, 200, 255, 222, brass_hi)
room.rect(254, 220, 257, 223, brass)

# Vorhänge und Stange
room.rect(0, 2, W - 1, 5, C("#2c2630"))
room.rect(0, 2, W - 1, 2, C("#4a4250"))
for x0, x1 in ((0, 30), (481, 511)):
    xs = XX[:, x0:x1 + 1]
    fold = 0.55 + 0.45 * np.sin(xs * 2 * np.pi / 9 + (0 if x0 == 0 else 1.5))
    lvl = np.clip(np.floor(fold * 4 + BAY[:, x0:x1 + 1]) / 4, 0, 1)
    cur = C("#2c0f1c")[None, None] + lvl[..., None] * (C("#5a2032") - C("#2c0f1c"))[None, None]
    room.rgb[6:, x0:x1 + 1] = cur[6:]
    for x in range(x0 + 2, x1, 7):
        room.rect(x, 3, x + 2, 7, C("#6a6070"))

# Fensterbank
room.rect(28, 306, 483, 317, C("#4a4452"))
room.rect(28, 306, 483, 306, C("#5a5464"))
room.rect(24, 318, 487, 318, C("#6a6474"))
room.rect(24, 319, 487, 325, C("#37323e"))
room.rect(24, 326, 487, 329, C("#0c0a10"))
for x in range(30, 482, 37):
    room.rect(x, 308, x, 316, C("#443e4c"))

# Heizkörper
for x in range(140, 372, 8):
    room.rect(x, 342, x + 5, H - 1, C("#34303c"))
    room.rect(x + 1, 340, x + 4, 341, C("#34303c"))
    room.rect(x, 343, x, H - 1, C("#44404e"))
    room.rect(x + 5, 343, x + 5, H - 1, C("#26222c"))
room.rect(138, 352, 371, 354, C("#2e2a36"))
room.rect(124, 358, 139, 361, C("#2e2a36"))
room.rect(126, 352, 131, 357, C("#44404e"))

# Topfpflanze (Efeutute), rankt über die Fensterbank
PX, PY = 114, 316
for y in range(PY - 28, PY + 1):
    w = 15 - (y - (PY - 28)) * 4 // 28
    room.rect(PX - w, y, PX + w, y, C("#8a4830"))
    room.px(PX - w, y, C("#a85e3a"))
    room.px(PX - w + 1, y, C("#9a5434"))
    room.rect(PX + w - 3, y, PX + w, y, C("#6a3624"))
room.rect(PX - 17, PY - 32, PX + 17, PY - 27, C("#9a5234"))
room.rect(PX - 17, PY - 32, PX + 17, PY - 32, C("#b8683e"))
room.rect(PX - 15, PY - 33, PX + 15, PY - 33, C("#2a1a14"))


def leaf(cx, cy, s, ang, rr):
    ca, sa = math.cos(ang), math.sin(ang)
    base = rr.choice([C("#1f4a2e"), C("#27583a"), C("#2e6a3e")])
    for dy in range(-s - 1, s + 2):
        for dx in range(-s - 1, s + 2):
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / (s + 0.3)) ** 2 + (v / (s * 0.62 + 0.3)) ** 2 <= 1:
                c = base
                if abs(v) < 0.6:
                    c = base * 0.75
                elif v < 0 and u > -s * 0.3:
                    c = base * 1.3
                room.px(int(cx + dx), int(cy + dy), c)


rr = random.Random(7)
stem = C("#2a4a26")
vines = []
for i in range(9):
    x, y = PX + rr.randint(-12, 12), PY - 33
    ang = rr.uniform(-2.6, -0.5) if i < 5 else rr.choice([rr.uniform(0.3, 1.2), rr.uniform(1.9, 2.8)])
    length = rr.randint(18, 50) if i < 5 else rr.randint(40, 70)
    pts = []
    for s in range(length):
        if i >= 5 and y > PY - 10:
            ang += (math.pi / 2 - ang) * 0.12          # hängt über die Kante
        ang += rr.uniform(-0.18, 0.18)
        x += math.cos(ang) * 1.2
        y += math.sin(ang) * 1.2
        pts.append((x, y, ang))
    vines.append(pts)
for pts in vines:
    for x, y, _ in pts:
        room.px(int(x), int(y), stem)
for pts in vines:
    for k, (x, y, ang) in enumerate(pts):
        if k % 6 == 3:
            side = 1 if (k // 6) % 2 else -1
            leaf(x + math.cos(ang + side * 1.3) * 4, y + math.sin(ang + side * 1.3) * 4,
                 rr.randint(3, 5), ang + side * 0.9, rr)

# Bücherstapel und Tasse
room.rect(420, 306, 470, 316, C("#5a2426"))
room.rect(420, 306, 470, 306, C("#7a3436"))
room.rect(468, 307, 470, 315, C("#d8cca8"))
room.rect(424, 298, 466, 305, C("#233a5a"))
room.rect(424, 298, 466, 298, C("#34507a"))
room.rect(464, 299, 466, 304, C("#d8cca8"))
room.rect(428, 292, 462, 297, C("#3a4a2a"))
room.rect(460, 293, 462, 296, C("#d0c4a0"))
MUGX, MUGY = 434, 272
room.rect(MUGX, MUGY, MUGX + 15, 291, C("#2a5058"))
room.rect(MUGX, MUGY, MUGX + 1, 291, C("#3c6a72"))
room.rect(MUGX + 13, MUGY, MUGX + 15, 291, C("#1c3a40"))
room.rect(MUGX, MUGY, MUGX + 15, MUGY, C("#4a7a82"))
room.rect(MUGX + 1, MUGY + 1, MUGX + 14, MUGY + 2, C("#1a1210"))
for y in range(MUGY + 4, MUGY + 15):
    dx = 3 if MUGY + 6 <= y <= MUGY + 12 else 2
    room.px(MUGX + 16 + dx, y, C("#2a5058"))
room.rect(MUGX + 16, MUGY + 4, MUGX + 18, MUGY + 4, C("#2a5058"))
room.rect(MUGX + 16, MUGY + 14, MUGX + 18, MUGY + 14, C("#2a5058"))

# Kerze
CX, CTOP = 372, 282
wax = C("#e4d6b6")
room.rect(CX - 7, CTOP, CX + 7, 316, wax)
room.rect(CX - 7, CTOP, CX - 6, 316, wax * 0.86)
room.rect(CX + 5, CTOP, CX + 7, 316, wax * 0.78)
room.rect(CX - 6, CTOP, CX + 6, CTOP + 1, C("#fff0c8"))
room.rect(CX - 4, CTOP - 1, CX + 4, CTOP - 1, C("#f0e0bc"))
for dx, ln in ((-7, 9), (-3, 5), (6, 13)):                       # Wachstropfen
    room.rect(CX + dx, CTOP, CX + dx + 1, CTOP + ln, C("#f4e8cc"))
    room.px(CX + dx, CTOP + ln + 1, C("#f4e8cc"))
room.rect(CX - 11, 314, CX + 11, 316, C("#8a7a60"))               # Unterteller
room.rect(CX - 11, 314, CX + 11, 314, C("#b0a080"))
room.rect(CX, CTOP - 6, CX, CTOP - 1, C("#2a1e18"))
FLAME_X, FLAME_Y = CX, CTOP - 13

# flackernde Lichtstufen der Kerze vorab berechnen
room_lit = []
LEVELS = [(160, 0.5), (172, 0.56), (150, 0.45), (180, 0.6)]
dist = np.hypot(XX - FLAME_X, (YY - FLAME_Y) * 1.05)
for R_, I_ in LEVELS:
    g = dq(np.clip(1 - dist / R_, 0, 1) ** 1.7 * I_, 12)
    lay = room.rgb * (1 + g[..., None] * 0.9) + g[..., None] * C("#ff9a4c")[None, None] * 0.5
    room_lit.append(np.clip(lay, 0, 255))
refl_glow = [dq(np.clip(1 - dist / (R_ * 0.7), 0, 1) ** 2 * I_ * 0.07, 4) * glass for R_, I_ in LEVELS]

rf = random.Random(3)
flick = []
lv = 0
for f in range(N):
    if rf.random() < 0.45:
        lv = rf.choice([0, 0, 1, 1, 2, 3])
    flick.append(lv)


def draw_room(fr, f):
    k = flick[f]
    # Spiegelung im Glas: warmer Schimmer und die Flamme als Echo
    fr += refl_glow[k][..., None] * C("#ff9a4c")[None, None]
    rx, ry = FLAME_X + 21, FLAME_Y - 2
    fr[ry - 3:ry + 4, rx] = np.maximum(fr[ry - 3:ry + 4, rx], C("#8a5a30"))
    fr[ry - 1:ry + 2, rx] = np.maximum(fr[ry - 1:ry + 2, rx], C("#c08a4a"))
    fr[room.a] = room_lit[k][room.a]
    # Flamme
    hgt = [8, 9, 7, 10][k]
    lean = [0, 1, 0, -1][(f // 2 + k) % 4] if k else 0
    for i in range(hgt):
        y = FLAME_Y + 6 - i
        w = 2 if 1 <= i <= hgt - 4 else (1 if i < hgt - 1 else 0)
        xo = FLAME_X + (lean if i > hgt // 2 else 0)
        for dx in range(-w, w + 1):
            c = C("#ffb040") if abs(dx) == w and w > 0 else C("#fff2c0")
            if i < 2:
                c = C("#5a70ff") if abs(dx) == w else C("#ffe0a0")
            fr[y, xo + dx] = c
    fr[FLAME_Y + 7, FLAME_X] = C("#3a2418")
    # Dampf aus der Tasse
    for s, ph in enumerate((0.0, 2.1, 4.2)):
        for t in range(26):
            y = MUGY - 2 - t
            x = int(MUGX + 4 + s * 4 + math.sin(2 * math.pi * (t / 14 - 2 * f / N) + ph) * (1 + t * 0.12))
            a = (1 - t / 26) * 0.5 * (0.6 + 0.4 * math.sin(2 * math.pi * 3 * f / N + ph + t * 0.3))
            if BAY[y, x] < a:
                fr[y, x] = fr[y, x] * 0.5 + C("#a09aa8") * 0.5


# ---------------------------------------------------------------- Rendern
def frame(f):
    fr = sky.rgb.copy()
    draw_sky(fr, f)
    over(fr, city)
    draw_dynamic(fr, f)
    draw_train(fr, f)
    over(fr, rail)
    draw_car(fr, f)
    draw_room(fr, f)
    return Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))


def render():
    frames = [frame(f) for f in range(N)]
    sample = Image.new("RGB", (W, H * 10))
    for i, k in enumerate(range(0, N, N // 10)):
        sample.paste(frames[k], (0, H * i))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT, kmeans=2)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    big = [im.resize((W * SCALE, H * SCALE), Image.NEAREST) for im in q]
    out = HERE / "fenster.gif"
    big[0].save(out, save_all=True, append_images=big[1:], duration=MS, loop=0, disposal=1)
    frames[40].resize((W * SCALE, H * SCALE), Image.NEAREST).save(HERE / "fenster.png")
    print(f"{out}  {out.stat().st_size / 1e6:.1f} MB, {N} Bilder, {N * MS / 1000:.0f} s")


if __name__ == "__main__":
    render()
