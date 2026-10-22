"""Compose explainer frames: game screenshot + top-down map (history ring, frozen target, Mario, Laki, tether) + text.
usage: isk11_explain_compose.py DIR TITLE OUT.mp4"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
d, title, outp = sys.argv[1], sys.argv[2], sys.argv[3]
log = json.load(open(os.path.join(d, 'log.json')))
col = json.load(open('isk11_collision.json'))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, small, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '-Bold', 16)
X0, X1, Z0, Z1, SC = -350, 450, 360, 680, 0.9
W = int((X1 - X0) * SC); H = int((Z1 - Z0) * SC)
tp = lambda x, z: ((x - X0) * SC, (z - Z0) * SC)
base = Image.new('RGB', (W, H), (25, 25, 30)); bd = ImageDraw.Draw(base)
for c in col['colliders']:
    if c['flags'] & 0x7FFFFE00: continue
    for t in c['tris']:
        if t['n'][1] > 0.7:
            y = t['v'][0][1]; g = int(max(40, min(200, 200 + (y + 470) * 0.9)))
            bd.polygon([tp(v[0], v[2]) for v in t['v']], fill=(g, g, int(g * 0.9)))
SN = {0: 'state 0: chase target', 1: 'state 1: hop', 2: 'state 2: hop (in air)', 5: 'state 5: idle by Mario', 15: 'state 15: catch-up (history CLEARED)'}
tmp = os.path.join(d, 'c'); os.makedirs(tmp, exist_ok=True)
n = 0; peak = 0
for r in log:
    if not r['shot']: continue
    fp = os.path.join(d, 'f%05d.png' % r['k'])
    if not os.path.exists(fp): continue
    im = Image.new('RGB', (W, 364 + H + 92), (12, 12, 12))
    g = Image.open(fp).convert('RGB').crop((103, 96, 696, 460)); im.paste(g, ((W - 593) // 2, 0))
    m = base.copy(); md = ImageDraw.Draw(m)
    for i, (hx, hz) in enumerate(r['hist']):
        x, z = tp(hx, hz); md.ellipse((x - 2, z - 2, x + 2, z + 2), fill=(150, 150, 150))
    mx, mz = tp(r['m'][0], r['m'][2]); lx, lz = tp(r['l'][0], r['l'][2]); tx, tz = tp(*r['t'])
    rr = 40 * SC; md.ellipse((mx - rr, mz - rr, mx + rr, mz + rr), outline=(255, 120, 120))
    md.line((lx, lz, tx, tz), fill=(255, 220, 0), width=1)
    md.line((tx - 6, tz - 6, tx + 6, tz + 6), fill=(255, 220, 0), width=3); md.line((tx - 6, tz + 6, tx + 6, tz - 6), fill=(255, 220, 0), width=3)
    md.ellipse((lx - 5, lz - 5, lx + 5, lz + 5), fill=(90, 150, 255)); md.ellipse((mx - 5, mz - 5, mx + 5, mz + 5), fill=(255, 60, 60))
    md.text((4, 2), 'top-down map (camera at bottom)    red dot = Mario, red circle = 40-unit tether    blue = Laki', fill=(230, 230, 230), font=small)
    md.text((4, 16), 'yellow X = the history slot Laki is flying to (his target)    grey dots = the 40-slot history ring', fill=(230, 230, 230), font=small)
    im.paste(m, (0, 364))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title[:95], fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    y0 = 364 + H + 4
    dt = math.hypot(r['l'][0] - r['t'][0], r['l'][2] - r['t'][1])
    peak = max(peak, r['ls'])
    dr.text((8, y0), r['tag'], fill=(255, 255, 120), font=big)
    dr.text((8, y0 + 24), 'Laki: %s   speed %.1f   distance to target %.0f' % (SN.get(r['st'], 'state %d' % r['st']), r['ls'], dt), fill=(255, 255, 255), font=font)
    dr.text((8, y0 + 46), 'history: write slot %d, Laki\'s slot %d%s   map %s' % (r['idx'], r['ptr'], '  (FULL: recording stopped)' if (r['ptr'] - 1) % 40 == r['idx'] else '', {10: 'isk_11', 16: 'isk_19'}.get(r['map'], r['map'])), fill=(200, 200, 200), font=font)
    im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', os.environ.get('FPS', '30'), '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '23', outp], check=True)
print('wrote', outp, n, 'frames')
