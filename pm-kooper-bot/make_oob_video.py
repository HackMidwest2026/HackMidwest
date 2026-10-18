"""Captioned video of a record_laki_oob.py run: game footage + top-down map of the room (walls from the collision
dump) with Mario, Laki (+trail), his history target and the history ring. usage: make_oob_video.py DIR COLLISION.json OUT.mp4 [title]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
d, coll, outp = sys.argv[1:4]; title = sys.argv[4] if len(sys.argv) > 4 else ''
L = json.load(open(os.path.join(d, 'log.json')))
C = json.load(open(coll)); C = C['colliders'] if isinstance(C, dict) else C
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, small, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '-Bold', 18)
W, H = 1020, 430
BX0, BY0, BX1, BY1 = 600, 22, 1014, 386
xs = [v[0] for c in C for t in c['tris'] for v in t['v']]; zs = [v[2] for c in C for t in c['tris'] for v in t['v']]
cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
sc = min((BX1 - BX0) / (max(xs) - min(xs) + 500), (BY1 - BY0) / (max(zs) - min(zs) + 500))
P = lambda x, z: (BX0 + (BX1 - BX0) / 2 + (x - cx) * sc, BY0 + (BY1 - BY0) / 2 + (z - cz) * sc)
bg = Image.new('RGB', (BX1 - BX0, BY1 - BY0), (250, 250, 248)); bd = ImageDraw.Draw(bg)
for c in C:
    for t in c['tris']:
        pts = [P(v[0], v[2]) for v in t['v']]; pts = [(a - BX0, b - BY0) for a, b in pts]
        if t['n'][1] > 0.5: bd.polygon(pts, fill=(205, 222, 205))
for c in C:
    for t in c['tris']:
        if abs(t['n'][1]) < 0.5:
            pts = [P(v[0], v[2]) for v in t['v']]; pts = [(a - BX0, b - BY0) for a, b in pts]
            bd.line(pts + [pts[0]], fill=(200, 60, 60), width=1)
STN = {0: 'follow (0)', 1: 'hop start (1)', 2: 'hop (2)', 5: 'idle (5)', 15: 'move beside Mario (15)'}
first = next(l['i'] for l in L if Image.open(os.path.join(d, 'f%04d.png' % l['i'])).getbbox())
tmp = os.path.join(d, 'c'); os.makedirs(tmp, exist_ok=True)
peak = max(range(len(L)), key=lambda i: L[i]['ls'])
trail = []; n = 0
for l in L:
    trail.append(P(l['lx'], l['lz']))
    im = Image.new('RGB', (W, H), (20, 20, 20))
    g = Image.open(os.path.join(d, 'f%04d.png' % max(l['i'], first))).crop((103, 96, 696, 460)).convert('RGB')
    im.paste(g, (0, 0)); im.paste(bg, (BX0, BY0)); dr = ImageDraw.Draw(im)
    dr.rectangle((BX0, BY0, BX1 - 1, BY1 - 1), outline=(120, 120, 120))
    for hx, hz in l['hist']:
        p = P(hx, hz); dr.ellipse((p[0] - 1.5, p[1] - 1.5, p[0] + 1.5, p[1] + 1.5), fill=(150, 150, 150))
    if len(trail) > 1: dr.line(trail[-400:], fill=(230, 150, 40), width=1)
    t = P(l['tx'], l['tz']); dr.line((t[0] - 5, t[1] - 5, t[0] + 5, t[1] + 5), fill=(220, 40, 40), width=2); dr.line((t[0] - 5, t[1] + 5, t[0] + 5, t[1] - 5), fill=(220, 40, 40), width=2)
    m = P(l['x'], l['z']); dr.ellipse((m[0] - 5, m[1] - 5, m[0] + 5, m[1] + 5), fill=(40, 110, 220))
    k = P(l['lx'], l['lz']); dr.ellipse((k[0] - 5, k[1] - 5, k[0] + 5, k[1] + 5), fill=(240, 170, 0), outline=(0, 0, 0))
    o = lambda xy, s, c=(255, 255, 255), f=font: dr.text(xy, s, fill=c, font=f, stroke_width=2, stroke_fill=(0, 0, 0))
    o((6, 300), 'Laki speed %.2f   state %s' % (l['ls'], STN.get(l['st'], str(l['st']))))
    o((6, 320), 'history: pointer %d  write index %d   frame %d' % (l['ptr'], l['idx'], l['i']))
    o((6, 340), 'Mario y %.0f   Laki y %.0f   Laki target y %.0f' % (l['y'], l['ly'], l['ty']), f=small)
    if l['idx'] == (l['ptr'] - 1) % 40: o((6, 278), 'RING FULL: recording blocked', (255, 120, 120))
    if l['ly'] < l['y'] and l['st'] == 0: o((6, 256), 'Laki below Mario: speed capped at 6', (255, 220, 80))
    if not os.environ.get('NOSPIKE') and l['i'] >= peak and l['i'] <= peak + 40: o((150, 120), 'SPEED SPIKE: %.1f' % L[peak]['ls'], (120, 255, 120), big)
    if title: o((6, 4), title, (255, 220, 120), small)
    dr.text((BX0, 4), 'top-down: walls red, floor green; blue Mario, orange Laki, red X target', fill=(220, 220, 220), font=small)
    dr.rectangle((0, 392, W, H), fill=(0, 0, 0)); dr.text((8, 402), l['tag'], fill=(255, 255, 255), font=font)
    for r in range(6 if abs(l['i'] - peak) <= 3 and not os.environ.get('NOSPIKE') else 1):
        im.save(os.path.join(tmp, 'c%04d.png' % n)); n += 1
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print(n, 'frames ->', outp)
