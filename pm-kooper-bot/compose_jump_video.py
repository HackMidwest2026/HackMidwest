"""Compose the three Jr. Troopa (ch 8) jump variants side by side, aligned on the target-confirm press (frame 0),
30 fps (one PNG per game frame), with labels, a frame counter and the partner-menu marker.
usage: compose_jump_video.py SRCDIR OUTDIR"""
import os, sys, re
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
V = [('normal', 'Normal Jump (A only for the action command)'), ('quick', 'Quick jump: A during the crouch (frame 20)'),
     ('cancel', 'Run cancel: ONE A press on frame 16')]
meta = {}
for v, _ in V:
    m = open(os.path.join(src, v, 'meta.txt')).read().split()
    meta[v] = (int(m[1]), int(m[3]))          # confirm index, partner-menu frame
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
CROP = (104, 100, 696, 500)            # the 592x400 game picture inside the 800x600 window
pre, post = 10, 60
last = max(meta[v][1] for v, _ in V) + post
for t in range(-pre, last + 1):
    canvas = Image.new('RGB', (592 * 3, 400 + 90), 'black')
    for j, (v, label) in enumerate(V):
        c0, pm = meta[v]
        idx = c0 + min(t, pm + post)
        p = os.path.join(src, v, 'f%05d.png' % max(0, idx))
        while not os.path.exists(p) and idx > 0:
            idx -= 1; p = os.path.join(src, v, 'f%05d.png' % idx)
        im = Image.open(p).crop(CROP)
        canvas.paste(im, (592 * j, 0))
        d = ImageDraw.Draw(canvas)
        d.text((592 * j + 10, 405), label, font=font, fill='white')
        shown = min(t, pm) if t >= 0 else t
        col = 'yellow' if t >= pm else 'white'
        txt = 'frame %d since target confirm' % max(shown, 0) if t >= 0 else 'selecting target'
        if t >= pm: txt = 'PARTNER MENU at frame %d' % pm
        d.text((592 * j + 10, 435), txt, font=font, fill=col)
        if t >= pm and v != 'normal':
            d.text((592 * j + 10, 462), '%d frames faster than normal' % (meta['normal'][1] - pm), font=small, fill='lime')
    canvas.save(os.path.join(out, 'c%05d.png' % (t + pre)))
print('frames', last + pre + 1)
