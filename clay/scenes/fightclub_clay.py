"""Projekt Knete: die letzte Szene von "Fight Club" als stummer Claymation-Kurzfilm.

Eigene Knetfiguren (keine Portraits der Schauspieler), ohne Text.
blender -b -P clay/scenes/fightclub_clay.py -- [--still F] [--range A B] [--res W H] [--samples N] [--out DIR]
"""
import bpy, sys, os, math, random
from mathutils import Vector
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from claylib import *

OPTS = cli('fightclub')
F = 288  # 24 s bei 12 fps

reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=F)
sc.cycles.use_denoising = False  # Ubuntu-Build ohne OIDN; entrauscht wird beim Encodieren
sc.cycles.max_bounces = 4
sc.view_settings.exposure = -0.6
world((0.02, 0.025, 0.06), 0.25)
rnd = random.Random(7)

# ================================================================== Materialien
M = {}
def mat(name, col, **kw):
    kw.setdefault('scale', 0.2)
    kw.setdefault('bumpdist', 1.6)
    M[name] = clay(name, col, **kw)
    return M[name]

mat('tealA', (0.05, 0.28, 0.30), rough=0.7, scale=0.5)
mat('tealB', (0.10, 0.45, 0.46), rough=0.7, scale=0.5)
mat('wall', (0.20, 0.09, 0.34), rough=0.8, scale=0.4)
mat('wall2', (0.28, 0.13, 0.45), rough=0.8, scale=0.4)
mat('frame', (0.05, 0.03, 0.08), rough=0.6, scale=0.4)
mat('sky', (0.02, 0.04, 0.12), rough=0.95, sss=0.0, bump=0.15, thumb=0.0, scale=0.1)
_p = M['sky'].node_tree.nodes['Principled BSDF']
_p.inputs['Emission Color'].default_value = (0.03, 0.05, 0.16, 1)
_p.inputs['Emission Strength'].default_value = 0.8
for i, c in enumerate([(0.06, 0.07, 0.20), (0.12, 0.06, 0.22), (0.04, 0.10, 0.22), (0.16, 0.08, 0.30)]):
    mat(f'bld{i}', c, rough=0.75, scale=0.35)
mat('skin', (0.80, 0.55, 0.38), sss=0.12)
mat('skin_pale', (0.88, 0.76, 0.68), sss=0.12)
mat('skin_tan', (0.72, 0.45, 0.28), sss=0.12)
mat('shirt', (0.90, 0.88, 0.80), sss=0.08)
mat('trousers', (0.25, 0.25, 0.32))
mat('shoe', (0.10, 0.06, 0.04), coat=0.2)
mat('hair_brown', (0.22, 0.11, 0.05))
mat('hair_blond', (0.95, 0.78, 0.25))
mat('hair_black', (0.03, 0.02, 0.05))
mat('jacket', (0.62, 0.05, 0.05), coat=0.25, rough=0.45)
mat('jacket_dk', (0.32, 0.02, 0.03), coat=0.2)
mat('loud', (0.20, 0.70, 0.70))
mat('dots', (0.95, 0.80, 0.15))
mat('pants_dk', (0.12, 0.06, 0.20))
mat('dress', (0.28, 0.12, 0.42))
mat('shadow', (0.35, 0.18, 0.50))
mat('lips', (0.70, 0.06, 0.10), coat=0.4)
mat('black_cloth', (0.035, 0.03, 0.05))
mat('eyewhite', (0.93, 0.92, 0.88), rough=0.35, coat=0.3)
mat('gun', (0.20, 0.20, 0.24), rough=0.35, coat=0.4)
mat('smoke', (0.35, 0.33, 0.38), rough=0.9, sss=0.05)
mat('smoke2', (0.22, 0.20, 0.26), rough=0.9, sss=0.05)
mat('pot', (0.55, 0.22, 0.08))
mat('leaf', (0.18, 0.45, 0.10))
mat('sweat', (0.55, 0.75, 0.95), rough=0.1, coat=0.8, sss=0.2)
mat('wound', (0.55, 0.03, 0.05), coat=0.5)
EYE = glossy_black()
WIN_ON = emissive('win_on', (1.0, 0.78, 0.35), 6.0)
MOON = emissive('moon', (1.0, 0.92, 0.65), 4.0)
STAR = emissive('star', (0.9, 0.85, 1.0), 8.0)
FIRE = emissive('fire', (1.0, 0.40, 0.06), 7.0)
FIRE_CORE = emissive('fire_core', (1.0, 0.75, 0.30), 12.0)
TUBE = emissive('tube', (0.85, 0.9, 1.0), 3.0)
FLASH = emissive('flash', (1.0, 0.9, 0.6), 18.0)

HIDE = (1e-4,) * 3

# ================================================================== Set: Boden, Wand, Fenster
TW = 0.075
for i in range(-7, 7):
    for j in range(-6, 5):
        rounded_box(f'tile{i}_{j}', (TW * 0.98, TW * 0.98, 0.012), loc=((i + 0.5) * TW, (j + 0.5) * TW, -0.006),
                    bevel=0.003, mat=M['tealA' if (i + j) % 2 else 'tealB'])

WY = 0.32  # Fensterwand
rounded_box('sill', (1.1, 0.05, 0.05), loc=(0, WY, 0.025), bevel=0.006, mat=M['wall'], lumpy=0.002)
rounded_box('sill_top', (1.1, 0.07, 0.012), loc=(0, WY - 0.005, 0.054), bevel=0.004, mat=M['wall2'])
rounded_box('lintel', (1.1, 0.05, 0.06), loc=(0, WY, 0.52), bevel=0.006, mat=M['wall'])
# gewölbte Säulen links und rechts (leicht schief wie in einem Cartoon-Set)
for side in (-1, 1):
    p = rounded_box(f'pillar{side}', (0.08, 0.07, 0.52), loc=(side * 0.43, WY - 0.01, 0.26), bevel=0.01,
                    mat=M['wall2'], rot=(0, side * 0.03, 0), lumpy=0.003)
# schiefe Fensterstreben
for k, x in enumerate([-0.27, -0.09, 0.09, 0.27]):
    rounded_box(f'mullion{k}', (0.012, 0.018, 0.47), loc=(x, WY - 0.012, 0.29), bevel=0.003, mat=M['frame'],
                rot=(0, (k - 1.5) * 0.035, 0))
rounded_box('transom', (0.9, 0.018, 0.012), loc=(0, WY - 0.012, 0.30), bevel=0.003, mat=M['frame'], rot=(0, 0.02, 0))
# Deckenröhren (Praktikable)
for k, x in enumerate([-0.2, 0.0, 0.2]):
    cylinder(f'tube{k}', 0.004, 0.12, loc=(x, 0.1, 0.48), verts=16, mat=TUBE, rot=(0, math.pi / 2, 0))

# Topfpflanze links vorn
cylinder('pot', 0.018, 0.035, loc=(-0.25, -0.05, 0.0175), verts=24, mat=M['pot'])
for k in range(7):
    a = k / 7 * math.tau
    lf = sphere(f'leaf{k}', 0.012, (-0.25 + math.cos(a) * 0.012, -0.05 + math.sin(a) * 0.012, 0.05 + (k % 3) * 0.01),
                scale=(0.5, 1.6, 0.35), mat=M['leaf'], segs=16, rings=8)
    lf.rotation_euler = (0.6, 0, a + math.pi / 2)

# ================================================================== Hintergrund: Himmel, Mond, Skyline
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.2, 0.3), rotation=(math.pi / 2, 0, 0))
bd = bpy.context.active_object; bd.name = 'backdrop'; bd.scale = (3.0, 1.4, 1); assign(bd, M['sky'])
sphere('moon', 0.05, (0.32, 1.18, 0.52), scale=(1, 0.2, 1), mat=MOON, segs=32, rings=16)
for i in range(60):
    sphere(f'star{i}', rnd.uniform(0.0015, 0.003), (rnd.uniform(-0.9, 0.9), 1.17, rnd.uniform(0.25, 0.85)), mat=STAR, segs=8, rings=4)

BLD = []
xs = [-0.52, -0.40, -0.29, -0.17, -0.05, 0.07, 0.19, 0.30, 0.42, 0.54]
for i, x in enumerate(xs):
    y = 0.62 + rnd.uniform(-0.06, 0.12)
    w = rnd.uniform(0.07, 0.10)
    h = rnd.uniform(0.45, 0.72)
    base = -0.25
    root = empty(f'bld_root{i}', (x, y, base))
    b = rounded_box(f'bld{i}', (w, 0.07, h), loc=(x, y, base + h / 2), bevel=0.006, mat=M[f'bld{i % 4}'], lumpy=0.004)
    parent(b, root)
    top = base + h
    if i % 3 == 0:
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w * 0.7, radius2=0.0, depth=0.06, location=(x, y, top + 0.03), rotation=(0, 0, math.pi / 4))
        c = bpy.context.active_object; c.name = f'roof{i}'; assign(c, M[f'bld{(i + 1) % 4}']); parent(c, root)
    elif i % 3 == 1:
        c = cylinder(f'ant{i}', 0.002, 0.07, loc=(x, y, top + 0.035), verts=8, mat=M['frame']); parent(c, root)
        c = sphere(f'antlamp{i}', 0.004, (x, y, top + 0.072), mat=emissive(f'red{i}', (1, 0.1, 0.05), 15), segs=8, rings=4); parent(c, root)
    wins = []
    cols = max(2, int(w / 0.02))
    for r in range(int(h / 0.028)):
        zz = base + 0.02 + r * 0.028
        if zz < 0.02:
            continue
        for cidx in range(cols):
            if rnd.random() < 0.45:
                continue
            xx = x - w / 2 + (cidx + 0.5) * w / cols
            wo = rounded_box(f'win{i}_{r}_{cidx}', (0.009, 0.004, 0.013), loc=(xx, y - 0.036, zz), bevel=0.001, mat=WIN_ON)
            parent(wo, root)
            wins.append(wo)
    BLD.append(dict(root=root, x=x, y=y, h=h, wins=wins, target=(i % 4 != 2), dir=rnd.choice((-1, 1))))

# Sprengreihenfolge: eins nach dem anderen
targets = [b for b in BLD if b['target']]
order = [4, 1, 6, 2, 7, 0, 5, 3]
for k, idx in enumerate(order[:len(targets)]):
    targets[idx]['t0'] = 206 + k * 5

# Feuerbälle und Rauch pro Zielgebäude
for b in targets:
    fb = sphere(f'fire_{b["x"]:.2f}', 1.0, (b['x'], b['y'] - 0.04, 0.04), mat=FIRE, segs=24, rings=12, lumpy=0.15)
    core = sphere(f'core_{b["x"]:.2f}', 1.0, (b['x'], b['y'] - 0.05, 0.04), mat=FIRE_CORE, segs=16, rings=8)
    fb.scale = core.scale = HIDE
    b['fire'], b['core'] = fb, core
    b['puffs'] = []
    for p in range(9):
        pf = sphere(f'puff_{b["x"]:.2f}_{p}', 1.0, (0, 0, 0), mat=M['smoke' if p % 2 else 'smoke2'], segs=20, rings=10, lumpy=0.2)
        pf.scale = HIDE
        b['puffs'].append((pf, rnd.uniform(-0.05, 0.05), rnd.uniform(-0.03, 0.02), rnd.uniform(0.02, 0.045), rnd.uniform(0.004, 0.01)))
    b['light'] = point_light(f'boom_{b["x"]:.2f}', (b['x'], b['y'] - 0.1, 0.06), 0.0, radius=0.03, color=(1.0, 0.45, 0.12))

# ================================================================== Figuren-Baukasten
def part(name, loc, scale, m, par, lump=0.02, segs=32, rot=None):
    o = sphere(name, 1.0, loc, scale=scale, mat=m, segs=segs, rings=segs // 2, lumpy=lump)
    o.parent = par
    o['s0'] = list(scale)
    if rot:
        o.rotation_euler = rot
    return o


def spikes(prefix, par, m, pts):
    for k, (x, y, z, rx, ry, L, r) in enumerate(pts):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r, radius2=0.0006, depth=L, location=(x, y, z), rotation=(rx, ry, 0))
        c = bpy.context.active_object; c.name = f'{prefix}{k}'; smooth(c); assign(c, m); c.parent = par


def eyes(prefix, par, pos, white_scale, pupil_r, lid_m):
    """Große Glubschaugen: Weiß + Pupille (verschiebbar) + Lid-Ersatzteil für Blinzeln."""
    out = []
    for side, (x, y, z) in zip((-1, 1), pos):
        piv = empty(f'{prefix}eye{side}', (x, y, z), par)
        part(f'{prefix}white{side}', (0, 0, 0), white_scale, M['eyewhite'], piv, lump=0, segs=24)
        pu = part(f'{prefix}pupil{side}', (0, -white_scale[1] * 0.85, 0), (pupil_r, pupil_r * 0.6, pupil_r * 1.15), EYE, piv, lump=0, segs=16)
        lid = part(f'{prefix}lid{side}', (0, -0.0002, 0), tuple(s * 1.08 for s in white_scale), lid_m, piv, lump=0, segs=24)
        lid.scale = HIDE
        out.append(dict(piv=piv, pupil=pu, lid=lid, lid_scale=tuple(s * 1.08 for s in white_scale), base=pu.location.copy(), ws=white_scale))
    return out


def arm(prefix, par, side, shoulder, L, r, m, hand_m, hand_r):
    piv = empty(f'{prefix}arm{side}', shoulder, par)
    part(f'{prefix}upper{side}', (0, 0, -L * 0.5), (r, r, L * 0.55), m, piv, lump=0.01)
    hand = empty(f'{prefix}hand{side}', (0, 0, -L), piv)
    part(f'{prefix}handball{side}', (0, 0, 0), (hand_r, hand_r * 0.8, hand_r * 1.1), hand_m, hand, lump=0.01)
    return piv, hand


# ------------------------------------------------------------------ Der Erzähler (lang, dünn, Hängenase)
def build_narrator():
    root = empty('n_root'); body = empty('n_body', parent=root)
    for s in (-1, 1):
        part(f'n_leg{s}', (s * 0.0055, 0, 0.022), (0.0055, 0.0055, 0.023), M['trousers'], body)
        part(f'n_shoe{s}', (s * 0.0058, -0.004, 0.003), (0.0055, 0.0095, 0.0032), M['shoe'], body)
    part('n_torso', (0, 0, 0.058), (0.0125, 0.0085, 0.02), M['shirt'], body)
    part('n_stain', (0.004, -0.0082, 0.052), (0.003, 0.0006, 0.0022), M['dots'], body, lump=0)
    part('n_neck', (0, 0, 0.081), (0.003, 0.003, 0.007), M['skin'], body)
    head = empty('n_head', (0, 0, 0.086), body)
    part('n_skull', (0, 0, 0.012), (0.0105, 0.010, 0.0145), M['skin'], head)
    for s in (-1, 1):
        part(f'n_ear{s}', (s * 0.0105, 0.001, 0.012), (0.002, 0.003, 0.0035), M['skin'], head)
    part('n_nose', (0.0, -0.0125, 0.0075), (0.0032, 0.0075, 0.0034), M['skin'], head, rot=(0.45, 0, 0))
    part('n_mouth', (0.0, -0.0098, 0.0005), (0.0035, 0.0012, 0.0008), M['lips'], head, lump=0)
    part('n_wound', (0.0065, -0.0082, 0.004), (0.0018, 0.0012, 0.0015), M['wound'], head, lump=0).scale = HIDE
    for s in (-1, 1):
        part(f'n_bag{s}', (s * 0.0046, -0.0092, 0.0112), (0.0035, 0.0012, 0.0014), M['shadow'], head, lump=0)
    ey = eyes('n_', head, [(-0.0046, -0.0088, 0.0168), (0.0046, -0.0088, 0.0168)], (0.0038, 0.0022, 0.0048), 0.0015, M['skin'])
    spikes('n_hair', head, M['hair_brown'], [
        (-0.006, 0.002, 0.026, 0.1, -0.6, 0.014, 0.005), (0.0, 0.0, 0.028, -0.1, 0.1, 0.016, 0.0055),
        (0.006, 0.002, 0.026, 0.1, 0.6, 0.014, 0.005), (-0.003, 0.006, 0.025, 0.7, -0.3, 0.013, 0.005),
        (0.004, 0.006, 0.025, 0.7, 0.3, 0.013, 0.005), (0.0, -0.004, 0.025, -0.6, 0, 0.012, 0.0045)])
    part('n_hairbase', (0, 0.001, 0.022), (0.0105, 0.0102, 0.006), M['hair_brown'], head)
    sweat = [part(f'n_sweat{k}', (x, -0.0095, z), (0.0012, 0.0008, 0.0017), M['sweat'], head, lump=0, segs=12)
             for k, (x, z) in enumerate([(-0.008, 0.02), (0.0085, 0.021)])]
    armL, handL = arm('n_', body, -1, (-0.0145, 0, 0.073), 0.036, 0.0028, M['skin'], M['skin'], 0.0036)
    armR, handR = arm('n_', body, 1, (0.0145, 0, 0.073), 0.036, 0.0028, M['skin'], M['skin'], 0.0036)
    g = empty('n_gun', (0, -0.002, -0.002), handR)
    rounded_box('n_gunbody', (0.004, 0.016, 0.005), loc=(0, 0, 0), bevel=0.001, mat=M['gun']).parent = g
    bpy.data.objects['n_gunbody'].location = (0, -0.006, 0.002)
    rounded_box('n_gungrip', (0.0038, 0.005, 0.009), loc=(0, 0, 0), bevel=0.001, mat=M['gun']).parent = g
    bpy.data.objects['n_gungrip'].location = (0, 0.0, -0.002)
    return dict(root=root, body=body, head=head, eyes=ey, armL=armL, armR=armR, gun=g, sweat=sweat,
                wound=bpy.data.objects['n_wound'], mouth=bpy.data.objects['n_mouth'])


# ------------------------------------------------------------------ Der Andere (Keil-Oberkörper, Riesenkinn, rote Jacke)
def build_tyler():
    root = empty('t_root'); body = empty('t_body', parent=root)
    for s in (-1, 1):
        part(f't_leg{s}', (s * 0.007, 0, 0.024), (0.0065, 0.0065, 0.025), M['pants_dk'], body)
        part(f't_shoe{s}', (s * 0.007, -0.006, 0.003), (0.006, 0.012, 0.0032), M['black_cloth'], body)
    part('t_waist', (0, 0, 0.052), (0.011, 0.009, 0.008), M['jacket'], body)
    part('t_chest', (0, 0, 0.067), (0.021, 0.011, 0.016), M['jacket'], body)
    part('t_shoulders', (0, 0, 0.078), (0.026, 0.011, 0.008), M['jacket'], body)
    part('t_shirt', (0, -0.0095, 0.071), (0.0055, 0.003, 0.011), M['loud'], body, lump=0)
    for k, (x, z) in enumerate([(-0.002, 0.075), (0.0025, 0.07), (-0.001, 0.065), (0.002, 0.078)]):
        part(f't_dot{k}', (x, -0.0123, z), (0.0011, 0.0006, 0.0011), M['dots'], body, lump=0, segs=8)
    for s in (-1, 1):
        part(f't_lapel{s}', (s * 0.0075, -0.0095, 0.072), (0.004, 0.002, 0.011), M['jacket_dk'], body, rot=(0, s * 0.35, 0))
    part('t_neck', (0, 0, 0.087), (0.0045, 0.0045, 0.006), M['skin_tan'], body)
    head = empty('t_head', (0, 0, 0.091), body)
    part('t_skull', (0, 0, 0.014), (0.0105, 0.0105, 0.014), M['skin_tan'], head)
    part('t_jaw', (0, -0.003, 0.004), (0.0115, 0.0095, 0.0075), M['skin_tan'], head)
    part('t_chin', (0, -0.009, 0.0015), (0.006, 0.004, 0.004), M['skin_tan'], head)
    part('t_nose', (0, -0.011, 0.012), (0.002, 0.003, 0.003), M['skin_tan'], head)
    part('t_grin', (0, -0.0102, 0.0055), (0.006, 0.0014, 0.0017), M['eyewhite'], head, lump=0)
    part('t_mouth_o', (0, -0.0104, 0.0052), (0.004, 0.0015, 0.0032), M['lips'], head, lump=0).scale = HIDE
    ey = eyes('t_', head, [(-0.004, -0.0092, 0.0165), (0.004, -0.0092, 0.0165)], (0.0028, 0.0016, 0.0019), 0.001, M['skin_tan'])
    for s in (-1, 1):
        part(f't_brow{s}', (s * 0.004, -0.0098, 0.0195), (0.003, 0.0009, 0.0008), M['hair_blond'], head, lump=0, rot=(0, s * 0.3, 0))
    spikes('t_hair', head, M['hair_blond'], [
        (-0.0075, 0.0, 0.029, 0.0, -0.5, 0.017, 0.004), (-0.003, -0.002, 0.031, -0.2, -0.15, 0.02, 0.0042),
        (0.002, 0.0, 0.032, 0.0, 0.1, 0.022, 0.0042), (0.007, 0.0, 0.029, 0.0, 0.5, 0.017, 0.004),
        (-0.004, 0.006, 0.028, 0.6, -0.3, 0.016, 0.004), (0.004, 0.006, 0.028, 0.6, 0.3, 0.016, 0.004)])
    part('t_hairbase', (0, 0.001, 0.024), (0.0105, 0.0105, 0.006), M['hair_blond'], head)
    armL, handL = arm('t_', body, -1, (-0.024, 0, 0.078), 0.038, 0.0045, M['jacket'], M['skin_tan'], 0.0045)
    armR, handR = arm('t_', body, 1, (0.024, 0, 0.078), 0.038, 0.0045, M['jacket'], M['skin_tan'], 0.0045)
    return dict(root=root, body=body, head=head, eyes=ey, armL=armL, armR=armR,
                grin=bpy.data.objects['t_grin'], mouth=bpy.data.objects['t_mouth_o'])


# ------------------------------------------------------------------ Marla (knochig, Wuschelmähne, Zigarette)
def build_marla():
    root = empty('m_root'); body = empty('m_body', parent=root)
    for s in (-1, 1):
        part(f'm_leg{s}', (s * 0.004, 0, 0.019), (0.0028, 0.0028, 0.02), M['pants_dk'], body)
        part(f'm_shoe{s}', (s * 0.0042, -0.003, 0.0025), (0.0035, 0.007, 0.0027), M['black_cloth'], body)
    part('m_dress', (0, 0, 0.048), (0.0125, 0.0095, 0.02), M['dress'], body)
    part('m_collar', (0, 0, 0.066), (0.011, 0.0085, 0.0035), M['shadow'], body)
    part('m_neck', (0, 0, 0.071), (0.0025, 0.0025, 0.005), M['skin_pale'], body)
    head = empty('m_head', (0, 0, 0.075), body)
    part('m_skull', (0, 0, 0.011), (0.0085, 0.0085, 0.0115), M['skin_pale'], head)
    for k in range(11):
        a = k / 11 * math.tau
        part(f'm_hair{k}', (math.cos(a) * 0.0105, 0.004 + math.sin(a) * 0.006 + 0.004, 0.016 + 0.006 * math.sin(a * 2) + (0.004 if k % 2 else 0)),
             (0.0075, 0.0075, 0.0075), M['hair_black'], head, lump=0.05, segs=20)
    part('m_hairtop', (0, 0.002, 0.022), (0.011, 0.01, 0.007), M['hair_black'], head, lump=0.05)
    for s in (-1, 1):
        part(f'm_shadow{s}', (s * 0.0036, -0.0074, 0.0135), (0.0036, 0.0015, 0.0036), M['shadow'], head, lump=0)
    ey = eyes('m_', head, [(-0.0036, -0.0082, 0.0135), (0.0036, -0.0082, 0.0135)], (0.0026, 0.0016, 0.003), 0.0011, M['skin_pale'])
    part('m_lips', (0.0005, -0.0082, 0.0035), (0.0024, 0.0012, 0.0011), M['lips'], head, lump=0)
    cig = cylinder('m_cig', 0.0007, 0.011, loc=(0.004, -0.013, 0.0035), verts=8, mat=M['eyewhite'], rot=(math.pi / 2, 0, 0.4))
    cig.parent = head
    sphere('m_ember', 0.0009, (0.0062, -0.0183, 0.0035), mat=emissive('ember', (1, 0.35, 0.05), 25), segs=8, rings=4).parent = head
    armL, _ = arm('m_', body, -1, (-0.011, 0, 0.064), 0.03, 0.0021, M['skin_pale'], M['skin_pale'], 0.0026)
    armR, _ = arm('m_', body, 1, (0.011, 0, 0.064), 0.03, 0.0021, M['skin_pale'], M['skin_pale'], 0.0026)
    return dict(root=root, body=body, head=head, eyes=ey, armL=armL, armR=armR)


# ------------------------------------------------------------------ Die Anhänger (kahl, schwarz, identisch)
def build_monkey(k):
    root = empty(f'k{k}_root'); body = empty(f'k{k}_body', parent=root)
    for s in (-1, 1):
        part(f'k{k}_leg{s}', (s * 0.0058, 0, 0.022), (0.0058, 0.0058, 0.023), M['black_cloth'], body)
        part(f'k{k}_shoe{s}', (s * 0.006, -0.004, 0.003), (0.0058, 0.0095, 0.0032), M['black_cloth'], body)
    part(f'k{k}_torso', (0, 0, 0.058), (0.0135, 0.009, 0.02), M['black_cloth'], body)
    head = empty(f'k{k}_head', (0, 0, 0.082), body)
    part(f'k{k}_skull', (0, 0, 0.01), (0.0105, 0.0105, 0.0115), M['skin'], head, lump=0.01)
    for s in (-1, 1):
        part(f'k{k}_eye{s}', (s * 0.0038, -0.0098, 0.011), (0.0013, 0.0008, 0.0016), EYE, head, lump=0, segs=12)
    part(f'k{k}_mouth', (0, -0.0102, 0.004), (0.003, 0.0008, 0.0006), M['lips'], head, lump=0)
    armL, _ = arm(f'k{k}_', body, -1, (-0.015, 0, 0.073), 0.035, 0.003, M['black_cloth'], M['skin'], 0.0034)
    armR, _ = arm(f'k{k}_', body, 1, (0.015, 0, 0.073), 0.035, 0.003, M['black_cloth'], M['skin'], 0.0034)
    return dict(root=root, body=body, head=head, armL=armL, armR=armR)


N = build_narrator()
T = build_tyler()
MA = build_marla()
KS = [build_monkey(0), build_monkey(1)]

# Krümel, in die der Andere zerfällt
crumbs = []
TX = 0.075
cm = [M['jacket']] * 5 + [M['jacket_dk'], M['hair_blond'], M['hair_blond'], M['skin_tan'], M['pants_dk'], M['loud']]
for i in range(110):
    z = rnd.uniform(0.005, 0.13)
    wdt = 0.024 if 0.05 < z < 0.085 else 0.012
    p0 = Vector((TX + rnd.uniform(-wdt, wdt), rnd.uniform(-0.008, 0.008), z))
    r = rnd.uniform(0.0018, 0.0038)
    m = M['hair_blond'] if z > 0.11 else M['skin_tan'] if z > 0.09 else M['pants_dk'] if z < 0.045 else rnd.choice(cm)
    c = sphere(f'crumb{i}', r, p0, mat=m, segs=12, rings=6, lumpy=r * 0.4)
    c.scale = HIDE
    crumbs.append(dict(ob=c, p0=p0, r=r, v=Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.1, 0.06), rnd.uniform(0.0, 0.18))),
                       delay=int((0.13 - z) * 40) + rnd.randint(0, 3)))

# Rauch aus der Wange
cheek_puffs = [sphere(f'cheekpuff{i}', 1.0, (0, 0, 0), mat=M['smoke'], segs=16, rings=8, lumpy=0.15) for i in range(6)]
for p in cheek_puffs:
    p.scale = HIDE
flash = sphere('flash', 1.0, (0, 0, 0), mat=FLASH, segs=24, rings=12, lumpy=0.3)
flash.scale = HIDE

# ================================================================== Licht + Kamera
key_l = area_light('key', (-0.35, -0.45, 0.45), (0.0, 0.0, 0.06), 9, 0.4, (1.0, 0.9, 0.82))
fill = area_light('fill', (0.45, -0.35, 0.18), (0.0, 0.0, 0.07), 1.6, 0.6, (0.6, 0.7, 1.0))
rim = area_light('rim', (0.0, 0.28, 0.35), (0.0, 0.0, 0.07), 5, 0.5, (0.55, 0.6, 1.0))
city_glow = area_light('cityglow', (0, 0.95, 0.05), (0, 1.2, 0.5), 0.0, 1.5, (1.0, 0.35, 0.06))
flash_l = point_light('flash_l', (0, 0, 0), 0.0, radius=0.01, color=(1.0, 0.9, 0.7))
cam = camera((0.0, -0.78, 0.13), (0.0, 0.05, 0.075), lens=40, fstop=5.6, focus=0.78)

SHOTS = {
    'wide':  dict(loc=(0.0, -0.5, 0.11), tgt=(0.0, 0.05, 0.07), lens=48, fstop=4.5, focus=0.5),
    'close': dict(loc=(-0.035, -0.26, 0.10), tgt=(-0.07, 0.0, 0.098), lens=65, fstop=3.2, focus=0.265),
    'back':  dict(loc=(-0.03, -0.36, 0.105), tgt=(-0.03, 0.6, 0.15), lens=32, fstop=4.0, focus=0.36),
}


def shot_for(f):
    if 60 <= f < 104:
        return 'close'
    if f >= 190:
        return 'back'
    return 'wide'


def set_shot(f, name):
    s = SHOTS[name]
    cam.location = s['loc']
    look_at(cam, s['tgt'])
    cam.keyframe_insert('location', frame=f)
    cam.keyframe_insert('rotation_euler', frame=f)
    cam.data.lens = s['lens']
    cam.data.dof.aperture_fstop = s['fstop']
    cam.data.dof.focus_distance = s['focus']
    for p in ('lens', 'dof.aperture_fstop', 'dof.focus_distance'):
        cam.data.keyframe_insert(p, frame=f)


# ================================================================== Animation
bN, bT, bM = Boil(1, amp=0.0002, rot=0.004), Boil(2, amp=0.0002, rot=0.004), Boil(3, amp=0.0002, rot=0.004)
bK = [Boil(4), Boil(5)]
NX, MX_END = -0.07, -0.02
YAW_R, YAW_L, YAW_BACK = math.pi / 2, -math.pi / 2, math.pi


def stepcycle(f, walking):
    s = (f // 3) % 2
    return ((0.14 if s else -0.14) if walking else 0.0), (0.002 if walking and f % 3 == 1 else 0.0)


def set_eyes(ey, f, look=(0, 0), closed=False):
    for e in ey:
        e['pupil'].location = e['base'] + Vector((look[0] * e['ws'][0] * 0.45, 0, look[1] * e['ws'][2] * 0.45))
        e['pupil'].keyframe_insert('location', frame=f)
        key(e['lid'], f, scale=e['lid_scale'] if closed else HIDE)


def vis(ob, f, on, mul=(1, 1, 1), loc=None):
    """Ersatzteil ein/aus (per Skalierung, wie bei echten Stop-Motion-Gesichtern)."""
    s0 = ob['s0'] if 's0' in ob else (1, 1, 1)
    key(ob, f, loc=loc, scale=tuple(a * b for a, b in zip(s0, mul)) if on else HIDE)


def blink(f, frames):
    return any(f in (b, b + 1) for b in frames)


crumb_rest = {}
for f in range(1, F + 1):
    shot = shot_for(f)
    set_shot(f, shot)

    # ---------------- Erzähler
    j, je = bN.v(), bN.e()
    yawN = YAW_R
    if shot == 'close':
        yawN = YAW_R - 0.75                                      # 3/4 zur Kamera in der Großaufnahme
    if f >= 176:
        yawN = lerp(YAW_R, YAW_BACK, ease(seg(f, 176, 186)))    # dreht sich zum Fenster
    stagger = 0.0
    sq = 0.0
    if 104 <= f < 118:                                           # taumelt nach dem Schuss
        stagger = -0.18 * math.sin(math.pi * seg(f, 104, 118))
        sq = 0.1 * math.sin(math.pi * seg(f, 104, 110))
    key(N['root'], f, loc=(NX + j.x, j.y, 0), rot=(je.x, stagger + je.y, yawN + je.z))
    key(N['body'], f, scale=(1 + sq * 0.5, 1 + sq * 0.5, 1 - sq))

    # Kopf: schaut zum Anderen, dann auf die Waffe, dann erschrocken
    hp = 0.0
    hp += 0.35 * ease(seg(f, 44, 50)) * (1 - ease(seg(f, 60, 64)))
    hp += 0.25 * ease(seg(f, 68, 74)) * (1 - ease(seg(f, 78, 82)))
    hy = 0.0
    if shot == 'close':
        hy = 0.35 * (1 - ease(seg(f, 64, 70)))
    if 150 <= f < 176:
        hy = -0.5 * ease(seg(f, 150, 156))                      # schaut zu Marla (nach rechts hinten)
    tilt = 0.25 * ease(seg(f, 104, 110)) * (1 - ease(seg(f, 150, 160)))
    if f >= 196:
        hy = -0.35 * ease(seg(f, 196, 202)) * (1 - ease(seg(f, 212, 218)))  # Blick zu Marla, dann raus
        hp = -0.1 * ease(seg(f, 214, 222))
    key(N['head'], f, rot=(hp, tilt, hy))
    look = (0.9, 0) if f < 44 else (0.3, -0.9) if f < 64 else (-0.4, 0.1) if f < 88 else (0.6, 0.0)
    if f >= 196:
        look = (0.8, 0) if f < 214 else (0, 0.2)
    set_eyes(N['eyes'], f, look, closed=blink(f, (22, 118, 162, 240, 270)))
    trem = 0.06 * math.sin(f * 2.1) if 74 <= f < 88 else 0.0

    # Arme: Waffe hängt runter -> hebt sie an die Wange -> Hand an die Wange
    raise_ = ease(seg(f, 66, 78)) * (1 - ease(seg(f, 100, 104)))
    cheek = ease(seg(f, 104, 110)) * (1 - ease(seg(f, 178, 186)))
    up_ = max(raise_, cheek)                                   # Hand neben die Schläfe (Arm aus Knete: staucht sich)
    ar_x = lerp(-0.25, -2.70, up_) + trem
    ar_y = lerp(-0.08, -0.06, up_)
    al_x, al_y = -0.08, 0.1
    if f >= 186:                                                # Hand zu Marla
        hold = ease(seg(f, 188, 196))
        ar_x, ar_y = lerp(ar_x, -0.1, hold), lerp(ar_y, -0.3 * 0, hold)
        al_x, al_y = lerp(-0.08, -0.15, hold), lerp(0.1, 0.62, hold)
    key(N['armR'], f, rot=(ar_x, ar_y, 0), scale=(1, 1, lerp(1.0, 0.78, up_)))
    key(N['gun'], f, rot=(0, 0, -math.pi / 2 * raise_))
    key(N['armL'], f, rot=(al_x, al_y, 0))
    key(N['gun'], f, scale=(1, 1, 1) if f < 118 else HIDE)
    vis(N['wound'], f, f >= 90)
    for k, s in enumerate(N['sweat']):
        if 40 <= f < 104:
            drop = ((f + k * 7) % 14) / 14
            vis(s, f, True, loc=(s.location.x, -0.0095, (0.02 if k == 0 else 0.021) - drop * 0.012))
        else:
            vis(s, f, False)
    vis(N['mouth'], f, True, (1, 1, 1) if not (72 <= f < 120) else (0.7, 1, 2.2))

    # Blitz + Rauch an der Wange (keine blutigen Details)
    sc.frame_set(f)
    bpy.context.view_layer.update()
    cheek_pos = N['head'].matrix_world @ Vector((0.012, -0.004, 0.006))
    if f in (89, 90):
        key(flash, f, loc=cheek_pos, scale=(0.012, 0.012, 0.012) if f == 89 else (0.02, 0.02, 0.02))
        flash_l.location = cheek_pos + Vector((0.01, -0.02, 0))
        flash_l.keyframe_insert('location', frame=f)
        flash_l.data.energy = 6 if f == 89 else 2.5
    else:
        key(flash, f, scale=HIDE)
        flash_l.data.energy = 0
    flash_l.data.keyframe_insert('energy', frame=f)
    for i, p in enumerate(cheek_puffs):
        t0 = 90 + i * 3
        if t0 <= f < t0 + 22:
            t = seg(f, t0, t0 + 22)
            s_ = 0.003 + 0.007 * t
            key(p, f, loc=cheek_pos + Vector((0.004 * i - 0.01, -0.004, 0.02 * t + 0.002)), scale=(s_, s_, s_ * 0.85))
        else:
            key(p, f, scale=HIDE)

    # ---------------- Der Andere: redet, gestikuliert, zerfällt
    j, je = bT.v(), bT.e()
    gone = f >= 108
    key(T['root'], f, loc=(TX + j.x, j.y, 0), rot=(je.x, je.y, YAW_L + je.z), scale=HIDE if gone else (1, 1, 1))
    talk = f < 52 and (f // 3) % 2 == 0
    vis(T['grin'], f, not talk)
    vis(T['mouth'], f, talk)
    gest = 1.0 if f < 56 else 0.0
    key(T['armR'], f, rot=(-1.2 - 0.5 * math.sin(f * 0.5) * gest if f < 56 else -0.2, 0.3 * gest, 0))
    key(T['armL'], f, rot=(-0.6 * gest, -0.4 * gest - 0.05, 0))
    key(T['head'], f, rot=(0, 0.12 * math.sin(f * 0.3) * gest, 0.1 * gest))
    set_eyes(T['eyes'], f, (0.5, 0), closed=blink(f, (30,)))
    key(T['body'], f, scale=(1, 1, 1))
    for c in crumbs:
        t0 = 108 + c['delay']
        if f < t0:
            key(c['ob'], f, scale=HIDE)
            continue
        if c['ob'].name in crumb_rest:
            key(c['ob'], f, loc=crumb_rest[c['ob'].name], scale=(1, 1, 1))
            continue
        tt = (f - t0) / FPS
        p = c['p0'] + c['v'] * tt + Vector((0, 0, -0.6 * tt * tt))
        if p.z <= c['r'] * 0.8:
            p.z = c['r'] * 0.8
            crumb_rest[c['ob'].name] = p.copy()
        key(c['ob'], f, loc=p, scale=(1, 1, 1))

    # ---------------- Marla + Anhänger
    j, je = bM.v(), bM.e()
    walk_in = seg(f, 130, 160)
    mx = lerp(0.42, 0.04, walk_in)
    if f >= 176:
        mx = lerp(0.04, MX_END, ease(seg(f, 176, 186)))
    walking = 130 <= f < 160 or 176 <= f < 186
    roll, bob = stepcycle(f, walking)
    yawM = YAW_L
    if f >= 176:
        yawM = lerp(YAW_L, -YAW_BACK, ease(seg(f, 176, 186)))
    key(MA['root'], f, loc=(mx + j.x, 0.012 + j.y, bob), rot=(je.x, je.y, yawM + je.z))
    key(MA['body'], f, rot=(0, roll, 0))
    mhold = ease(seg(f, 188, 196))
    key(MA['armR'], f, rot=(-0.1, lerp(0.08, -0.6, mhold), 0))
    key(MA['armL'], f, rot=(0.25 if walking and (f // 3) % 2 else -0.1, -0.08, 0))
    key(MA['head'], f, rot=(0, 0, 0.3 * ease(seg(f, 196, 202)) * (1 - ease(seg(f, 212, 218)))))
    set_eyes(MA['eyes'], f, (0.6, 0) if f < 196 else (-0.8, 0) if f < 214 else (0, 0.2), closed=blink(f, (168, 232, 262)))

    for k, K in enumerate(KS):
        j, je = bK[k].v(), bK[k].e()
        ins = seg(f, 128 + k * 4, 152 + k * 4)
        outs = seg(f, 162 + k * 2, 180 + k * 2)
        x = lerp(0.46 + k * 0.05, 0.11 + k * 0.055, ins)
        x = lerp(x, 0.5 + k * 0.05, outs)
        walking = (0 < ins < 1) or (0 < outs < 1)
        roll, bob = stepcycle(f + k, walking)
        yaw = YAW_L if outs < 0.05 else -YAW_L * 0 + YAW_L        # rückwärts raus, Blick bleibt beim Erzähler
        key(K['root'], f, loc=(x + j.x, 0.03 + k * 0.03 + j.y, bob), rot=(je.x, je.y, yaw + je.z))
        key(K['body'], f, rot=(0, roll, 0))
        up = ease(seg(f, 156, 160)) * (1 - ease(seg(f, 176, 180)))    # Hände hoch: "wir gehen schon"
        key(K['armL'], f, rot=(-2.6 * up, 0.2 * up, 0))
        key(K['armR'], f, rot=(-2.6 * up, -0.2 * up, 0))
        key(K['head'], f, rot=(0, 0, 0))

    # ---------------- Die Türme fallen
    glow = 0.0
    for b in targets:
        t0 = b['t0']
        tb = f - t0
        if tb < 0:
            key(b['root'], f, loc=(b['x'], b['y'], -0.25), rot=(0, 0, 0))
            for w in b['wins']:
                key(w, f, scale=(1, 1, 1))
            key(b['fire'], f, scale=HIDE); key(b['core'], f, scale=HIDE)
            b['light'].data.energy = 0
        else:
            glow += 1
            sink = min(0.7, 0.00055 * tb * tb)
            key(b['root'], f, loc=(b['x'], b['y'], -0.25 - sink), rot=(0, b['dir'] * min(0.12, tb * 0.004), 0))
            for w in b['wins']:
                key(w, f, scale=(1, 1, 1) if tb < 2 else HIDE)
            fs = 0.08 * math.sin(math.pi * seg(tb, 0, 14)) if tb < 14 else 0
            key(b['fire'], f, loc=(b['x'], b['y'] - 0.04, 0.035 + fs * 0.4), scale=(fs * 1.3, fs * 0.8, fs) if fs > 0 else HIDE)
            key(b['core'], f, loc=(b['x'], b['y'] - 0.06, 0.03 + fs * 0.3), scale=(fs * 0.6,) * 3 if fs > 0 else HIDE)
            b['light'].data.energy = (3.0 * math.sin(math.pi * seg(tb, 0, 14)) if tb < 14 else 0) * (1 + rnd.uniform(-0.2, 0.2))
        b['light'].data.keyframe_insert('energy', frame=f)
        for i, (pf, dx, dy, rise, r0) in enumerate(b['puffs']):
            tp = f - b['t0'] - 2 - i
            if tp < 0:
                key(pf, f, scale=HIDE)
            else:
                grow = min(1.0, tp / 30)
                s_ = r0 + 0.03 * grow
                key(pf, f, loc=(b['x'] + dx * (0.5 + grow), b['y'] - 0.06 + dy, 0.03 + rise * grow + 0.03 * min(1, tp / 80)),
                    scale=(s_, s_ * 0.8, s_ * 0.85))
    city_glow.data.energy = 110 * min(1.0, glow / 4) * (1 + rnd.uniform(-0.06, 0.06))
    city_glow.data.keyframe_insert('energy', frame=f)

    # Licht-Flackern wie am echten Set
    key_l.data.energy = 9 * (1 + rnd.uniform(-0.012, 0.012)) * (1 + 0.3 * min(1, glow / 6))
    key_l.data.keyframe_insert('energy', frame=f)

constant_interp()
if os.environ.get("CLAYDBG"):
    exec(open(os.environ["CLAYDBG"]).read())
else:
    run(sc, OPTS)
