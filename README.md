# Angst und Schrecken – ein Tintenfilm

Eine animierte Webseite, die den Anfang von Hunter S. Thompsons Roman *Fear and Loathing in Las Vegas* als kurzen „Film“ nacherzählt – in eigenen Worten, mit selbst gezeichneten Tintenkleck-Illustrationen, inspiriert vom Stil Ralph Steadmans.

Einfach `index.html` im Browser öffnen. Steuerung: Leertaste (Pause), ← / → (Szenen), Klick aufs Bild.

## Projekt Pixel – Fight Club, die letzte Szene

`fightclub.html`: die Schlussszene von *Fight Club* (1999) als stummer Pixel-Film im Stil der Point-and-Click-Adventures der 90er: schiefe Cartoon-Perspektiven, übertriebene Figuren mit Konturen, satte Farben. Gezeichnet wird weich auf einer 320×180-Leinwand und dann auf eine feste VGA-Palette mit Dithering reduziert. Kein Text, keine Dialoge, keine Songtexte; alle Figuren sind eigene Entwürfe.

## Projekt Knete – Fight Club als Claymation

`knete.html` spielt `clay/out/fightclub_clay.mp4`: dieselbe Schlussszene als 24-sekündiger Stop-Motion-Knetfilm aus Blender (Cycles, 12 fps, ohne Text). Gebaut mit dem [blender-claymation-skill](https://github.com/angrypenguinpng/blender-claymation-skill) (MIT); dessen `claylib.py` liegt unter `clay/lib/`. Alle Figuren sind eigene Entwürfe.

Neu rendern (Blender 4.x, ffmpeg):

```bash
CLAYDBG=clay/lib/render_loop.py blender -b -P clay/scenes/fightclub_clay.py -- --res 640 360 --samples 20 --out clay/renders/fightclub
ffmpeg -framerate 12 -i clay/renders/fightclub/%04d.png -vf "nlmeans=s=4:p=5:r=9,scale=1280:720:flags=lanczos,noise=alls=3:allf=t,vignette=angle=PI/6,fps=24,format=yuv420p" -c:v libx264 -crf 20 clay/out/fightclub_clay.mp4
```
