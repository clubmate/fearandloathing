"""Berliner Nacht aus dem Fenster – ein Pixel-Loop.

Erzeugt berlin/fenster.gif (128x96 Pixel, 5x hochskaliert, 120 Bilder, nahtlose Schleife).
Alles ist deterministisch: Jede Bewegung hat eine Periode, die in 120 Bilder aufgeht.

    pip install pillow
    python3 berlin/fenster.py
"""
import math
import random
from pathlib import Path

from PIL import Image

W, H = 128, 96
N = 120          # Bilder pro Schleife
SCALE = 5
MS = 100         # ms pro Bild -> 12 s Loop
OUT = Path(__file__).with_name("fenster.gif")

rnd = random.Random(1989)

# ---------- Palette ----------
SKY = [(8, 9, 28), (12, 13, 38), (17, 17, 48), (24, 21, 58), (34, 26, 66),
       (48, 32, 72), (66, 40, 74), (86, 50, 72)]        # oben -> Horizont (Lichtsmog)
STAR = [(90, 96, 140), (170, 175, 210), (245, 245, 255)]
MOON, MOON_D = (238, 232, 200), (180, 176, 160)
FAR = (28, 24, 56)
FAR_WIN = (70, 60, 70)
MID = (18, 16, 36)
MID_EDGE = (30, 27, 54)
WIN_ON = [(255, 204, 110), (240, 170, 80), (255, 226, 160)]
WIN_OFF = (26, 24, 44)
TV = [(90, 130, 230), (150, 190, 255), (70, 100, 200)]
TOWER = (40, 38, 70)
TOWER_HI = (70, 68, 104)
BALL = (58, 56, 92)
BALL_HI = (110, 108, 150)
RED = (255, 40, 40)
RED_D = (110, 20, 30)
BRICK = (58, 30, 34)
BRICK_D = (38, 20, 26)
ARCH = (12, 10, 20)
SBAHN_R = (170, 30, 32)
SBAHN_Y = (230, 170, 30)
SBAHN_W = (255, 236, 180)
STREET = (20, 18, 28)
LAMP = (255, 190, 90)
GLOW = [(60, 40, 40), (90, 60, 44)]
WALL = (20, 16, 26)
WALL_2 = (24, 19, 30)
FRAME = (52, 44, 58)
FRAME_HI = (82, 70, 84)
FRAME_SH = (32, 26, 38)
SILL = (66, 56, 66)
SILL_HI = (96, 82, 90)
POT = (120, 60, 40)
LEAF = (26, 60, 40)
LEAF_HI = (44, 90, 56)
WAX = (230, 220, 200)
FLAME = [(255, 240, 180), (255, 190, 70), (240, 120, 40)]

# Fensteröffnung (Glasfläche) und Rahmen
WX0, WY0, WX1, WY1 = 16, 8, 111, 76       # innen, inklusiv
MULL_X = (62, 64)                         # Mittelpfosten
TRANS_Y = (20, 22)                        # Kämpfer unter dem Oberlicht


def blink(frame, period, on, phase=0):
    return (frame + phase) % period < on


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ---------- statische Szene vorbereiten ----------
stars = []
for _ in range(38):
    x, y = rnd.randint(WX0, WX1), rnd.randint(WY0, 40)
    stars.append((x, y, rnd.choice([10, 12, 15, 20, 24, 30, 40, 60]), rnd.randrange(120), rnd.random()))

# ferne Silhouette: Höhen pro Spalte
far = []
h = 50
for x in range(W):
    if rnd.random() < 0.18:
        h = rnd.randint(44, 54)
    far.append(h)
far_windows = [(x, y) for x in range(W) for y in range(far[x] + 2, 60, 3)
               if x % 3 == 0 and rnd.random() < 0.12]

# vordere Häuser: (x0, x1, dach_y, typ)
houses = [
    (8, 30, 40, "alt"), (31, 44, 46, "alt"), (72, 104, 30, "platte"), (105, 122, 42, "alt"),
]
windows = []   # (x, y, w, h, modus, periode, phase, farbe)
for x0, x1, top, kind in houses:
    if kind == "platte":
        cols = range(x0 + 2, x1 - 1, 3)
        rows = range(top + 3, 62, 3)
        ww, wh = 2, 1
    else:
        cols = range(x0 + 2, x1 - 2, 4)
        rows = range(top + 4, 62, 5)
        ww, wh = 2, 3
    for cx in cols:
        for cy in rows:
            r = rnd.random()
            if r < 0.45:
                mode = "off"
            elif r < 0.80:
                mode = "on"
            elif r < 0.95:
                mode = "toggle"
            else:
                mode = "tv"
            windows.append((cx, cy, ww, wh, mode, rnd.choice([40, 60, 120]),
                            rnd.randrange(120), rnd.choice(WIN_ON)))

lamps = [22, 52, 84, 112]


def scene(f):
    img = [[SKY[0]] * W for _ in range(H)]

    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            img[y][x] = c

    def rect(x0, y0, x1, y1, c):
        for yy in range(max(0, y0), min(H, y1 + 1)):
            for xx in range(max(0, x0), min(W, x1 + 1)):
                img[yy][xx] = c

    # Himmel in Bändern (Dithering an den Übergängen)
    for y in range(H):
        t = min(1.0, max(0.0, (y - WY0) / 58)) * (len(SKY) - 1)
        i = int(t)
        frac = t - i
        for x in range(W):
            j = i + 1 if (frac > 0.5) ^ ((x + y) % 2 == 0 and abs(frac - 0.5) < 0.25) else i
            img[y][x] = SKY[min(j, len(SKY) - 1)]

    # Sterne
    for x, y, per, ph, b in stars:
        k = (f + ph) % per
        if k == 0:
            c = STAR[2]
        elif k < 3 or b > 0.7:
            c = STAR[1]
        else:
            c = STAR[0]
        px(x, y, c)

    # Mond (Sichel)
    mx, my = 94, 13
    for y in range(my - 5, my + 6):
        for x in range(mx - 5, mx + 6):
            if (x - mx) ** 2 + (y - my) ** 2 <= 22 and (x - mx + 3) ** 2 + (y - my + 1) ** 2 > 18:
                px(x, y, MOON if (x - mx) > 1 else MOON_D)

    # Flugzeug (Tegel ist zu, also fliegt es nach BER)
    ax = int(-8 + (W + 16) * f / N)
    ay = 22 - (f * 6) // N
    px(ax, ay, (60, 60, 80))
    px(ax + 1, ay, (60, 60, 80))
    if blink(f, 10, 2):
        px(ax, ay, RED)
    if blink(f, 10, 1, 5):
        px(ax + 1, ay, (255, 255, 255))

    # ferne Stadt
    for x in range(W):
        for y in range(far[x], 66):
            img[y][x] = FAR
    for x, y in far_windows:
        if blink(f, 120, 90, x * 7 + y):
            px(x, y, FAR_WIN)

    # Fernsehturm
    tx = 50
    for y in range(30, 56):
        w = 1 if y < 38 else (2 if y < 50 else 3)
        for dx in range(-(w // 2), w - w // 2):
            px(tx + dx, y, TOWER if dx < 0 or w == 1 else TOWER_HI)
    for y in range(25, 30):
        px(tx, y, TOWER)
    for y in range(22, 25):
        px(tx, y, TOWER_HI)
    by = 33
    for y in range(by - 4, by + 5):
        for x in range(tx - 4, tx + 5):
            d = (x - tx) ** 2 + (y - by) ** 2
            if d <= 18:
                px(x, y, BALL_HI if (x - tx) + (y - by) < -3 else BALL)
    # Fensterring der Kugel, läuft langsam um
    for i in range(-3, 4):
        on = (i + f // 20) % 3 != 0
        px(tx + i, by + 1, (200, 170, 110) if on else (120, 100, 90))
    # Warnlicht
    px(tx, 21, RED if blink(f, 24, 6) else RED_D)
    px(tx, 44, RED if blink(f, 24, 6, 12) else RED_D)

    # vordere Häuser
    for x0, x1, top, kind in houses:
        rect(x0, top, x1, 66, MID)
        rect(x0, top, x1, top, MID_EDGE)
        if kind == "alt":
            # Dachkante, Schornstein
            rect(x0 + 3, top - 3, x0 + 4, top - 1, MID)
            rect(x0 - 1, top, x1 + 1, top, MID_EDGE)
        else:
            rect(x0 + 10, top - 4, x0 + 13, top - 1, MID)  # Aufzugshaus
            px(x0 + 11, top - 5, RED if blink(f, 40, 20) else RED_D)
    for cx, cy, ww, wh, mode, per, ph, col in windows:
        if mode == "on":
            c = col
        elif mode == "off":
            c = WIN_OFF
        elif mode == "toggle":
            c = col if (f + ph) % per < per * 2 // 3 else WIN_OFF
        else:  # Fernseher flackert
            c = TV[((f + ph) // 3 * 7 + (f // 5)) % 3]
        rect(cx, cy, cx + ww - 1, cy + wh - 1, c)

    # Straße
    rect(0, 67, W - 1, H - 1, STREET)

    # S-Bahn-Viadukt (Backstein mit Bögen)
    rect(0, 62, W - 1, 64, BRICK)
    rect(0, 62, W - 1, 62, (80, 44, 44))
    for x in range(W):
        if x % 4 == 0:
            px(x, 63, BRICK_D)
    for x in range(W):
        rel = x % 16
        for y in range(65, 72):
            if rel < 3:
                px(x, y, BRICK if rel != 2 else BRICK_D)
            elif y >= 67 or (y == 66 and 4 < rel < 14) or (y == 65 and 6 < rel < 12):
                px(x, y, ARCH if y < 71 else STREET)
            else:
                px(x, y, BRICK_D)

    # S-Bahn fährt von rechts nach links
    L = 44
    sx = int(W + 10 - (W + L + 40) * f / N)
    for i in range(L):
        x = sx + i
        seg = i % 15
        if seg == 14:
            continue  # Wagenübergang
        px(x, 55, SBAHN_Y if 0 < i < L - 1 else SBAHN_R)
        for y in range(56, 58):
            px(x, y, SBAHN_W if seg % 3 != 0 and 0 < i < L - 1 else SBAHN_Y)
        for y in range(58, 61):
            px(x, y, SBAHN_R)
        px(x, 61, (30, 20, 20))
    # Funke an der Stromschiene
    if 0 <= sx + 30 < W and blink(f, 7, 1):
        px(sx + 30, 62, (180, 200, 255))

    # Auto auf der Straße, von links nach rechts
    kx = int(-30 + (W + 60) * ((f + 60) % N) / N)
    for i in range(9):
        px(kx + i, 74, (40, 40, 60))
        if 2 <= i <= 6:
            px(kx + i, 73, (32, 32, 50))
    px(kx + 9, 74, (255, 250, 210))           # Scheinwerfer
    for i in range(1, 7):
        if i % 2 or i < 3:
            px(kx + 9 + i, 75 if i > 3 else 74, (120, 110, 90))
    px(kx - 1, 74, RED)                       # Rücklicht

    # Laternen vor dem Viadukt
    for lx in lamps:
        for y in range(63, 77):
            px(lx, y, (44, 40, 56))
        px(lx + 1, 63, (44, 40, 56))
        px(lx + 2, 64, LAMP)
        for dx in range(-2, 7):
            y = 76 if abs(dx - 2) > 2 else 75
            if img[y][max(0, min(W - 1, lx + dx))] == STREET:
                px(lx + dx, y, GLOW[0] if abs(dx - 2) > 1 else GLOW[1])

    return img


def room(img, f):
    """Zimmer, Fensterrahmen, Fensterbank, Kerze darübermalen."""
    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            img[y][x] = c

    flick = [0, 1, 0, 2, 1, 0, 0, 1, 2, 1, 0, 1][f % 12] if f % 30 < 25 else 2
    cx, cy = 96, 84   # Kerze

    for y in range(H):
        for x in range(W):
            inside = WX0 <= x <= WX1 and WY0 <= y <= WY1
            mull = MULL_X[0] <= x <= MULL_X[1] and WY0 <= y <= WY1
            trans = TRANS_Y[0] <= y <= TRANS_Y[1] and WX0 <= x <= WX1
            frame = (WX0 - 5 <= x <= WX1 + 5 and WY0 - 5 <= y <= WY1 + 1) and not inside
            d = math.hypot(x - cx, (y - cy) * 1.3)
            warm = max(0.0, 1 - d / (34 + flick * 2))
            if mull or trans:
                c = FRAME_HI if x in (MULL_X[0],) or y == TRANS_Y[0] else FRAME
            elif frame:
                edge = x in (WX0 - 1, WX1 + 1) or y in (WY0 - 1,)
                c = FRAME_SH if edge else (FRAME_HI if x == WX0 - 5 or y == WY0 - 5 else FRAME)
            elif inside:
                # Spiegelung auf der Scheibe
                if (x - y) % 37 == 0 and (x < 34 or 74 < x < 86) and 30 < y < 58:
                    c = lerp(img[y][x], (120, 120, 150), 0.15)
                else:
                    continue
            else:
                c = WALL_2 if (x * 3 + y * 5) % 11 == 0 else WALL
            if warm > 0 and not inside:
                c = lerp(c, (150, 90, 50), warm * 0.5)
                c = tuple((v // 6) * 6 for v in c)   # Farbstufen, damit es pixelig bleibt
            img[y][x] = c

    # Fensterbank
    for y in range(WY1 + 2, WY1 + 7):
        for x in range(WX0 - 8, WX1 + 9):
            base = SILL_HI if y == WY1 + 2 else (SILL if y < WY1 + 6 else FRAME_SH)
            d = math.hypot(x - cx, (y - cy) * 1.3)
            warm = max(0.0, 1 - d / (30 + flick * 2))
            c = lerp(base, (200, 130, 70), warm * 0.55)
            img[y][x] = tuple((v // 6) * 6 for v in c)

    # Topfpflanze links
    for y in range(72, 78):
        w = 3 if y < 76 else 2
        for x in range(28 - w, 29 + w):
            px(x, y, POT)
    leaves = [(28, 71), (27, 70), (29, 70), (26, 69), (30, 69), (25, 67), (31, 68), (28, 68), (28, 67),
              (27, 66), (29, 65), (24, 66), (32, 66), (28, 64), (26, 64), (30, 63), (23, 65), (33, 64)]
    sway = 1 if (f // 30) % 2 else 0
    for i, (x, y) in enumerate(leaves):
        px(x + (sway if y < 67 else 0), y, LEAF_HI if i % 3 == 0 else LEAF)

    # Kerze
    for y in range(cy - 7, cy - 1):
        for x in range(cx - 1, cx + 2):
            px(x, y, WAX if x < cx + 1 else (200, 190, 170))
    px(cx, cy - 8, (40, 30, 30))
    fy = cy - 9
    px(cx, fy, FLAME[1])
    px(cx, fy - 1, FLAME[0] if flick != 2 else FLAME[1])
    if flick != 1:
        px(cx, fy - 2, FLAME[2])
    if flick == 1:
        px(cx - 1, fy - 1, FLAME[2])
    if flick == 2:
        px(cx + 1, fy - 1, FLAME[2])


def render():
    frames = []
    for f in range(N):
        img = scene(f)
        room(img, f)
        im = Image.new("RGB", (W, H))
        im.putdata([c for row in img for c in row])
        frames.append(im)

    # gemeinsame Palette aus allen Bildern, damit nichts flimmert
    sheet = Image.new("RGB", (W, H * 8))
    for i, k in enumerate(range(0, N, N // 8)):
        sheet.paste(frames[k], (0, H * i))
    pal = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    out = [fr.quantize(palette=pal, dither=Image.Dither.NONE)
           .resize((W * SCALE, H * SCALE), Image.NEAREST) for fr in frames]
    out[0].save(OUT, save_all=True, append_images=out[1:], duration=MS, loop=0, optimize=False, disposal=1)
    frames[0].resize((W * SCALE, H * SCALE), Image.NEAREST).save(OUT.with_suffix(".png"))
    print(f"{OUT}  ({N} Bilder, {N * MS / 1000:.0f} s)")


if __name__ == "__main__":
    render()
