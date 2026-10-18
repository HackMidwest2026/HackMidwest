"""Captioned video of record_laki_stuck.py runs: game footage + top-down view (history ring, Laki's target, trail)
+ zoomed view around Mario. usage: make_stuck_video.py DIR OUT.mp4 [title]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
d, outp = sys.argv[1], sys.argv[2]; title = sys.argv[3] if len(sys.argv) > 3 else ''
L = json.load(open(os.path.join(d, 'log.json')))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, small, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '-Bold', 20)
STN = {0: 'follow (0)', 1: 'hop (1)', 2: 'hop (2)', 5: 'idle (5)'}
W, H = 1020, 430
first = next(l['i'] for l in L if Image.open(os.path.join(d, 'f%04d.png' % l['i'])).getbbox())
_ss = [l for l in L if l['tag'].startswith('stand still')] or L
mx_end, mz_end = _ss[-1]['x'], _ss[-1]['z']
stand1 = _ss[-1]['i']
def view(dr, box, cx, cz, sc, l, trail, hist=True):
    x0, y0, x1, y1 = box
    P = lambda x, z: (x0 + (x1 - x0) / 2 + (x - cx) * sc, y0 + (y1 - y0) / 2 + (z - cz) * sc)
    dr.rectangle(box, fill=(250, 250, 248), outline=(120, 120, 120))
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if hist:
        for k, (hx, hz) in enumerate(l['hist']):
            p = P(hx, hz)
            if inside(p): dr.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=(170, 170, 170))
    pts = [P(a, b) for a, b in trail]
    pts = [p for p in pts if inside(p)]
    if len(pts) > 1: dr.line(pts, fill=(230, 150, 40), width=1)
    t = P(l['tx'], l['tz'])
    if inside(t): dr.line((t[0] - 5, t[1] - 5, t[0] + 5, t[1] + 5), fill=(220, 40, 40), width=2); dr.line((t[0] - 5, t[1] + 5, t[0] + 5, t[1] - 5), fill=(220, 40, 40), width=2)
    m = P(l['x'], l['z']); r = 5
    if inside(m): dr.ellipse((m[0] - r, m[1] - r, m[0] + r, m[1] + r), fill=(40, 110, 220))
    k = P(l['lx'], l['lz'])
    if inside(k): dr.ellipse((k[0] - r, k[1] - r, k[0] + r, k[1] + r), fill=(240, 170, 0), outline=(0, 0, 0))
def frame(l, trail, speedtag):
    im = Image.new('RGB', (W, H), (20, 20, 20))
    g = Image.open(os.path.join(d, 'f%04d.png' % max(l['i'], first))).crop((103, 96, 696, 460)).convert('RGB')
    im.paste(g, (0, 0)); dr = ImageDraw.Draw(im)
    dr.text((6, 300), 'Laki speed %.2f   state %s' % (l['ls'], STN.get(l['st'], str(l['st']))), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((6, 320), 'history: pointer %d  write index %d   frame %d %s' % (l['ptr'], l['idx'], l['i'], speedtag), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    full = l['idx'] == (l['ptr'] - 1) % 40
    if full: dr.text((6, 280), 'RING FULL: recording blocked', fill=(255, 120, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if l['st'] == 0 and l['ptr'] == l['idx'] and l['ls'] > 0.5:
        dr.text((6, 255), 'STUCK: target = newest entry, never reached', fill=(255, 220, 80), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if title: dr.text((6, 4), title, fill=(255, 220, 120), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((600, 4), 'top-down (x right, camera at bottom)', fill=(220, 220, 220), font=small)
    view(dr, (600, 22, 1014, 182), -55, -98, 2.0, l, trail)
    dr.text((600, 190), 'zoom on Mario (5x)', fill=(220, 220, 220), font=small)
    view(dr, (600, 208, 1014, 364), mx_end, mz_end - 4, 12.0, l, trail[-400:], hist=False)
    dr.text((600, 368), 'blue Mario  orange Laki (+trail)  red X Laki target  grey history', fill=(220, 220, 220), font=small)
    dr.rectangle((0, 392, W, H), fill=(0, 0, 0)); dr.text((8, 402), l['tag'], fill=(255, 255, 255), font=font)
    return im
n = 0; trail = []
tmp = os.path.join(d, 'c'); os.makedirs(tmp, exist_ok=True)
stand0 = next((l['i'] for l in L if l['tag'].startswith('stand still')), len(L))
for l in L:
    trail.append((l['lx'], l['lz']))
    fast = stand0 + 150 < l['i'] <= stand1
    if fast and (l['i'] - stand0) % 4: continue
    frame(l, trail, '(4x)' if fast else '').save(os.path.join(tmp, 'c%04d.png' % n)); n += 1
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print(n, 'frames ->', outp)
