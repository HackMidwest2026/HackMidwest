"""Captioned video from record_kpa62_setup.py frames: game view, current input, Mario/Laki numbers, and a top-down map
(tower outline, the clip line at x -440.7 / z -60..-40, Mario and Laki). Long holds/waits are sped up 3x except the
last 60 frames before the clip, which play at 1x, and the clip itself is repeated at 1/3 speed.
usage: make_kpa62_video.py DIR OUT.mp4 'title'"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
from kpa62_tower import TOWER
d, outp, title = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ''
L = json.load(open(os.path.join(d, 'log.json')))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, small, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '-Bold', 22)
W, H = 1020, 430
first = next(l['i'] for l in L if Image.open(os.path.join(d, 'f%04d.png' % l['i'])).getbbox())
cd = [l['i'] for l in L if l['inp'].startswith('C-DOWN + DOWN')][0]
def P(x, z): return (607 + (x + 535) * 1.9, 40 + (z + 140) * 1.85)
def frame(l, trail, tag2=''):
    im = Image.new('RGB', (W, H), (20, 20, 20))
    g = Image.open(os.path.join(d, 'f%04d.png' % max(l['i'], first))).crop((103, 96, 696, 460)).convert('RGB')
    im.paste(g, (0, 0)); dr = ImageDraw.Draw(im)
    if title: dr.text((6, 4), title, fill=(255, 220, 120), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
    if l['inp']: dr.text((10, 300), l['inp'], fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((10, 334), 'Mario (%.2f, %.1f, %.2f)   Laki speed %.2f' % (l['x'], l['y'], l['z'], l['ls']), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if tag2: dr.text((10, 22), tag2, fill=(255, 150, 150), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.rectangle((600, 22, 1014, 380), fill=(250, 250, 248), outline=(120, 120, 120))
    dr.text((604, 24), 'top-down: x right, z down', fill=(90, 90, 90), font=small)
    dr.polygon([P(x, z) for x, z in TOWER], fill=(200, 200, 215), outline=(80, 80, 120))
    dr.text(P(-400, -70), 'tower', fill=(60, 60, 100), font=small)
    dr.line([P(-440.7, -60), P(-440.7, -40)], fill=(40, 170, 60), width=3)
    dr.text(P(-470, -38), 'clip line x -440.7', fill=(30, 130, 40), font=small)
    pts = [P(a, b) for a, b in trail]
    if len(pts) > 1: dr.line(pts, fill=(80, 130, 230), width=1)
    m = P(l['x'], l['z']); k = P(l['lx'], l['lz'])
    dr.ellipse((k[0] - 5, k[1] - 5, k[0] + 5, k[1] + 5), fill=(240, 170, 0), outline=(0, 0, 0))
    dr.ellipse((m[0] - 5, m[1] - 5, m[0] + 5, m[1] + 5), fill=(40, 110, 220))
    dr.text((604, 362), 'blue Mario (+path)  orange Laki  green clip line', fill=(90, 90, 90), font=small)
    dr.rectangle((0, 392, W, H), fill=(0, 0, 0)); dr.text((8, 402), l['tag'], fill=(255, 255, 255), font=font)
    return im
tmp = os.path.join(d, 'c'); os.makedirs(tmp, exist_ok=True)
for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
n = 0; trail = []
def put(im):
    global n; im.save(os.path.join(tmp, 'c%04d.png' % n)); n += 1
for l in L:
    trail.append((l['x'], l['z']))
    slow_ok = l['inp'] == '' and l['tag'] in ('stand', 'ride Laki') or l['tag'].startswith('hold UP') or l['tag'].startswith('hold RIGHT')
    if slow_ok and l['i'] < cd - 60 and l['i'] % 3: continue
    put(frame(l, trail, '(3x)' if slow_ok and l['i'] < cd - 60 else ''))
trail = [(l['x'], l['z']) for l in L if l['i'] < cd - 3]
for l in L[cd - 3: cd + 30]:
    trail.append((l['x'], l['z'])); im = frame(l, trail, 'replay 1/3 speed')
    for r in range(3): put(im)
for i in range(30): put(frame(L[-1], trail))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames')
