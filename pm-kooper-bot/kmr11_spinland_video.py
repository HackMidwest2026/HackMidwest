"""Video of the closest spin-jump-land attempts into the kmr_11 bush fence (bush_w (373,-210), bush_mid (415,-210),
bush_e (457,-210)). For each target: search start (radius/angle north of the target), spin direction offset, jump
frame k, for the landing that ends closest to the target; then record it: spin (Z), A on frame k, hold toward the
target through the landing and 20 frames after. Captioned frames + slow-motion repeat of the landing.
usage: kmr11_spinland_video.py OUT.mp4"""
import json, math, os, subprocess, sys
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont

outp = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kmrvid')
START = 'states/kmr11_e0_kingdone.st'
FENCE = [(290, -225), (373, -210), (457, -210), (509, -200), (587, -218)]
def fence_z(x):
    for (x0, z0), (x1, z1) in zip(FENCE, FENCE[1:]):
        if x0 <= x <= x1: return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
def stick_for(deg, mag):
    r = math.radians(deg); return int(round(mag * math.cos(r))), int(round(-mag * math.sin(r)))
def setup(sx, sz, settle=12):
    e.load(START); e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, sx); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, sz)
    e.step(0, 0, 0, settle)
def attempt(sx, sz, theta, k, after=20, shot=None, log=None, settle=12):
    """game-frame loop: Z on 0, A on k, stick toward theta throughout; returns landing frame and position"""
    setup(sx, sz, settle)
    st = stick_for(theta, 80)
    airborne, land = False, None
    for f in range(60):
        b = Z if f == 0 else (A if f == k else 0)
        e.step(b, st[0], st[1], 2)
        p = player(e)
        if log is not None:
            log.append({'f': f, 'b': b, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'act': p['action'], 'spd': p['speed'], 'st': st})
            if shot: subprocess.run(['import', '-window', 'root', os.path.join(shot, 'f%04d.png' % len(log))], check=True)
        if p['action'] in (3, 4, 5, 8): airborne = True
        elif airborne and land is None: land = f
        if land is not None and f >= land + after: break
    return land, player(e)
TARGETS = {'bush_w (373,-210)': (373.0, -210.0), 'bush_mid (415,-210)': (415.0, -210.0), 'bush_e (457,-210)': (457.0, -210.0)}
best = json.load(open('/dev/shm/pmbot/kmrvid_best.json')) if os.environ.get('REUSE') else {}
for name, (cx, cz) in TARGETS.items():
    if name in best: continue
    cand = None
    for r in (25, 35, 45, 60):
        for a in range(200, 341, 20):                      # start point north of the fence (angles toward -z)
            sx, sz = cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a))
            toward = math.degrees(math.atan2(cz - sz, cx - sx))
            for off in (-15, 0, 15):
                for k in (1, 2, 3, 4):
                    land, p = attempt(sx, sz, toward + off, k, after=0)
                    if land is None: continue
                    d = abs(p['z'] - fence_z(p['x'])) if fence_z(p['x']) is not None else 99
                    if cand is None or d < cand[0]: cand = (d, sx, sz, toward + off, k)
    best[name] = cand
    print(name, 'closest landing %.2f from the fence' % cand[0], cand, flush=True)
json.dump(best, open('/dev/shm/pmbot/kmrvid_best.json', 'w'))

F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
tmp = '/dev/shm/pmbot/kmrvid_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%04d.png' % n)); n += 1
AN = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 10: 'land', 26: 'spin'}
for name, (d, sx, sz, theta, k) in best.items():
    shot = '/dev/shm/pmbot/kmrvid_raw'; os.makedirs(shot, exist_ok=True)
    for fn in os.listdir(shot): os.remove(os.path.join(shot, fn))
    log = []
    land, p = attempt(sx, sz, theta, k, after=10, shot=shot, log=log, settle=200)
    frames = []
    for i, l in enumerate(log):
        im = Image.new('RGB', (593, 450), (20, 20, 20))
        im.paste(Image.open(os.path.join(shot, 'f%04d.png' % (i + 1))).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
        dr = ImageDraw.Draw(im)
        dr.text((6, 4), 'kmr_11 bush fence, spin jump land into %s' % name, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        inp = ('Z (spin) + ' if l['b'] == Z else 'A (jump) + ' if l['b'] == A else '') + 'stick (%d, %d)' % l['st']
        dr.text((10, 300), inp, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
        fz = fence_z(l['x'])
        dr.text((8, 370), 'frame %d  %s  Mario (%.2f, %.2f, %.2f)  speed %.2f' % (l['f'], AN.get(l['act'], l['act']), l['x'], l['y'], l['z'], l['spd']), fill=(255, 255, 255), font=font)
        dr.text((8, 392), 'distance to fence %.2f (Mario radius 13)%s' % (fz - l['z'] if fz is not None else float('nan'), '   <- LANDING FRAME' if l['f'] == land else ''),
                fill=(255, 150, 150) if l['f'] == land else (200, 200, 200), font=font)
        dr.text((8, 414), 'best of %s setups: start (%.0f, %.0f), spin toward %.0f deg, A on frame %d' % ('96', sx, sz, theta % 360, k), fill=(160, 160, 160), font=font)
        frames.append(im)
    for im in frames: put(im)
    for im in frames[max(0, land - 4): land + 6]:          # landing again at 1/4 speed
        for r in range(4): put(im)
    for r in range(15): put(frames[-1])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames')
