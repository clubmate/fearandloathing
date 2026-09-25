"""Rendert Einzelbilder in einer Schleife statt render(animation=True).
Umgeht einen Absturz von Blender 4.0 (Ubuntu-Build) im Animationsmodus und
überspringt bereits vorhandene Bilder, damit ein abgebrochener Lauf fortgesetzt werden kann.
Aufruf: CLAYDBG=clay/lib/render_loop.py blender -b -P <scene.py> -- --res W H --samples N --out DIR
"""
import bpy, os
sc = bpy.context.scene
sc.render.use_persistent_data = False
os.makedirs(OPTS['out'], exist_ok=True)
a, b = OPTS['range'] or (sc.frame_start, sc.frame_end)
for f in range(a, b + 1):
    path = os.path.join(OPTS['out'], '%04d.png' % f)
    if os.path.exists(path):
        continue
    sc.frame_set(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('FRAME', f, flush=True)
print('DONE', flush=True)
