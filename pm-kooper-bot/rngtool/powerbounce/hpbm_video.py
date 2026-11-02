"""Overlay video of one High Power Bounce Manipulator rung from an hpbm_run.py output: the emulator frames the page saw,
with the page's state (shines, lock, countdown to the confirm, planned count) and the truth from RAM (A presses, Blooper's
HP, bounces so far). usage: hpbm_video.py RUNDIR RUNG_INDEX OUT.mp4 [frames before the lock]"""
import sys, json, io, subprocess, os
from PIL import Image, ImageDraw, ImageFont
D, I, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]; PRE = int(sys.argv[4]) if len(sys.argv) > 4 else 150
J = json.load(open(D + '/hpbm.json')); fr = J['frames']; ev = [x for x in J['events'] if 'got' in x][I]; T0 = J['T0']; FMS = 1001 / 30
data = open(D + '/run.mjpeg', 'rb').read(); jp = []; i = 0
while True:
    a = data.find(b'\xff\xd8', i)
    if a < 0: break
    b = data.find(b'\xff\xd9', a); jp.append(data[a:b + 2]); i = b + 2
c = ev['confirm_vf']; idx = [k for k, x in enumerate(fr) if x['f'] == c][0]
start = idx
while start > 0 and not (fr[start - 1]['lock'] is None and fr[start]['lock'] is not None): start -= 1
start = max(0, start - PRE); end = idx
while end < len(fr) - 1 and fr[end]['note'] in ('bounce', 'confirm') or end < idx + 30: end += 1
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18); S = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except Exception: F = S = ImageFont.load_default()
tmp = OUT + '.d'; os.makedirs(tmp, exist_ok=True); hits = 0; hp0 = fr[start]['hp']; lastA = -99
for n, k in enumerate(range(start, end + 1)):
    x = fr[k]; im = Image.open(io.BytesIO(jp[k])).convert('RGB'); W, H = im.size
    canvas = Image.new('RGB', (W, H + 110), (12, 16, 30)); canvas.paste(im, (0, 0)); d = ImageDraw.Draw(canvas)
    if k > start and x['hp'] < fr[k - 1]['hp']: hits += 1
    if x['btn']: lastA = k
    t = T0 + x['f'] * FMS; P = x['plan']
    line1 = 'High Power Bounce Manipulator  ·  target %d  ·  emulator (JP), seed unknown to the page' % ev['K']
    if P and t < P['tPress']: line2 = 'seed locked · confirm in %.1f s · planned %d bounces' % ((P['tPress'] - t) / 1000, P['count'])
    elif x['note'] in ('confirm', 'bounce'): line2 = 'confirmed on the final beep · planned %d' % ev['planned']
    elif x['lock'] is not None: line2 = 'seed locked'
    else: line2 = 'reading the coin: %d shines' % x['shines']
    line3 = 'bounces so far: %d   Blooper HP %d' % (hits, x['hp']) + ('   RESULT %d of %d planned' % (ev['got'], ev['planned']) if k > idx and x['note'] != 'bounce' and x['note'] != 'confirm' else '')
    d.text((10, H + 8), line1, fill=(240, 192, 74), font=S); d.text((10, H + 34), line2, fill=(232, 236, 246), font=F); d.text((10, H + 66), line3, fill=(69, 201, 139), font=F)
    if k - lastA < 3: d.rectangle([W - 70, H + 30, W - 10, H + 60], fill=(240, 192, 74)); d.text((W - 52, H + 35), 'A', fill=(20, 20, 20), font=F)
    canvas.save('%s/%05d.png' % (tmp, n))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30000/1001', '-i', tmp + '/%05d.png', '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', OUT], check=True)
subprocess.run(['rm', '-rf', tmp]); print('wrote', OUT, end - start + 1, 'frames')
