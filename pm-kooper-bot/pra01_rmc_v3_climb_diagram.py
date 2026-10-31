import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont
T = json.load(open('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/traj.json'))
D = json.load(open('/tmp/claude-0/pm/bot1/pra01_collision.json'))
tris = [(c['id'], t) for c in D['colliders'] for t in c['tris']]
TRIG = {t['collider'] for t in D['triggers']}
def kind(cid, n):
    if cid in TRIG: return 'lz'
    if n[1] > 0.7: return 'floor'
    if n[1] > 0.1: return 'lean'
    if n[1] >= -0.1: return 'wall'
    return 'under'
CK = {'floor': (60, 170, 80), 'lean': (240, 140, 30), 'wall': (90, 95, 110), 'under': (150, 90, 190), 'lz': (230, 80, 160)}
def section(axis, c):
    segs = []
    for cid, t in tris:
        v = t['v']; d = [p[axis] - c for p in v]; pts = []
        for i in range(3):
            a, b = v[i], v[(i + 1) % 3]; da, db = d[i], d[(i + 1) % 3]
            if (da < 0) != (db < 0):
                s = da / (da - db); pts.append([a[k] + (b[k] - a[k]) * s for k in range(3)])
        if len(pts) == 2: segs.append((kind(cid, t['n']), pts))
    return segs
ACT = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 10: 'land', 15: 'TORNADO', 16: 'tornado land', 34: 'SLIDE (steep slope)'}
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
f12, f14, f16, f18 = ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 16), ImageFont.truetype(F % '-Bold', 18)
SX0, SX1, SY0, SY1 = 455, 540, -75, 180
TX0, TX1, TZ0, TZ1 = 455, 540, -95, 5
PW, PH = 560, 820; TW, TH = 560, 660
def frame(n, path):
    p = T[n]
    im = Image.new('RGB', (PW + TW + 110, PH + 170), (246, 247, 249)); dr0 = ImageDraw.Draw(im)
    side = Image.new('RGB', (PW + 40, PH + 22), (246, 247, 249)); dr = ImageDraw.Draw(side)
    ox, oy = 0, 0; sx = PW / (SX1 - SX0); sy = PH / (SY1 - SY0)
    S = lambda x, y: (ox + (x - SX0) * sx, oy + (SY1 - y) * sy)
    dr.rectangle([S(SX0, SY1), S(SX1, SY0)], fill=(255, 255, 255), outline=(200, 200, 205))
    for y in range(-50, 181, 25): dr.line([S(SX0, y), S(SX1, y)], fill=(235, 236, 240)); dr.text((S(SX1, y)[0] + 3, S(SX1, y)[1]), str(y), fill=(110, 110, 110), font=f12, anchor='lm')
    for x in range(460, 541, 10): dr.line([S(x, SY0), S(x, SY1)], fill=(235, 236, 240)); dr.text((S(x, SY0)[0], S(x, SY0)[1] + 3), str(x), fill=(110, 110, 110), font=f12, anchor='mt')
    for k, (a, b) in section(2, p['z']): dr.line([S(a[0], a[1]), S(b[0], b[1])], fill=CK[k], width=4)
    for q in T[:n]: dr.ellipse([S(q['x'], q['y'])[0] - 2, S(q['x'], q['y'])[1] - 2, S(q['x'], q['y'])[0] + 2, S(q['x'], q['y'])[1] + 2], fill=(160, 160, 170))
    col = (220, 40, 40) if p['a'] != 34 else (240, 120, 0)
    dr.rectangle([S(p['x'] - 10, p['y'] + 37), S(p['x'] + 10, p['y'])], outline=col, width=3)
    dr.ellipse([S(p['x'], p['y'])[0] - 4, S(p['x'], p['y'])[1] - 4, S(p['x'], p['y'])[0] + 4, S(p['x'], p['y'])[1] + 4], fill=col)
    dr.rectangle([PW, 0, PW + 40, PH + 22], fill=(246, 247, 249)); dr.rectangle([0, PH, PW + 40, PH + 22], fill=(246, 247, 249))
    for y in range(-50, 181, 25): dr.text((S(SX1, y)[0] + 3, S(SX1, y)[1]), str(y), fill=(110, 110, 110), font=f12, anchor='lm')
    for x in range(460, 541, 10): dr.text((S(x, SY0)[0], S(x, SY0)[1] + 3), str(x), fill=(110, 110, 110), font=f12, anchor='mt')
    im.paste(side, (20, 70)); dr = dr0
    dr.text((20, 44), 'SIDE VIEW: slice at Mario\'s z = %.1f   (x across, height up)' % p['z'], fill=(20, 20, 30), font=f16)
    top = Image.new('RGB', (TW + 40, TH + 22), (246, 247, 249)); dr = ImageDraw.Draw(top)
    tx0 = 0; ty0 = 0; tsx = TW / (TX1 - TX0); tsz = TH / (TZ1 - TZ0)
    Tp = lambda x, z: (tx0 + (x - TX0) * tsx, ty0 + (z - TZ0) * tsz)
    dr.rectangle([Tp(TX0, TZ0), Tp(TX1, TZ1)], fill=(255, 255, 255), outline=(200, 200, 205))
    dr.rectangle([Tp(TX0, -95), Tp(500, -50)], fill=(250, 225, 240))
    dr.text(Tp(458, -93), 'star piece cave loading zone\n(airborne here -> pra_15)', fill=(200, 60, 140), font=f12)
    for z in range(-90, 6, 10): dr.line([Tp(TX0, z), Tp(TX1, z)], fill=(235, 236, 240)); dr.text((Tp(TX1, z)[0] + 3, Tp(TX1, z)[1]), str(z), fill=(110, 110, 110), font=f12, anchor='lm')
    for x in range(460, 541, 10): dr.line([Tp(x, TZ0), Tp(x, TZ1)], fill=(235, 236, 240)); dr.text((Tp(x, TZ1)[0], Tp(x, TZ1)[1] + 3), str(x), fill=(110, 110, 110), font=f12, anchor='mt')
    dr.line([Tp(TX0, 0), Tp(TX1, 0)], fill=(60, 140, 230), width=2); dr.text(Tp(520, -2), 'mirror z 0', fill=(60, 140, 230), font=f12, anchor='rb')
    for k, (a, b) in section(1, p['y'] + 15): dr.line([Tp(a[0], a[2]), Tp(b[0], b[2])], fill=CK[k], width=4)
    for q in T[:n]: dr.ellipse([Tp(q['x'], q['z'])[0] - 2, Tp(q['x'], q['z'])[1] - 2, Tp(q['x'], q['z'])[0] + 2, Tp(q['x'], q['z'])[1] + 2], fill=(160, 160, 170))
    c = Tp(p['x'], p['z']); r = 10 * tsx
    dr.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=col, width=3)
    dr.rectangle([TW, 0, TW + 40, TH + 22], fill=(246, 247, 249)); dr.rectangle([0, TH, TW + 40, TH + 22], fill=(246, 247, 249))
    for z in range(-90, 6, 10): dr.text((Tp(TX1, z)[0] + 3, Tp(TX1, z)[1]), str(z), fill=(110, 110, 110), font=f12, anchor='lm')
    for x in range(460, 541, 10): dr.text((Tp(x, TZ1)[0], Tp(x, TZ1)[1] + 3), str(x), fill=(110, 110, 110), font=f12, anchor='mt')
    TXO = 20 + PW + 60; im.paste(top, (TXO, 70)); dr = dr0
    dr.text((TXO, 44), 'TOP VIEW: slice at Mario\'s waist (height %.1f)   (x across, z down)' % (p['y'] + 15), fill=(20, 20, 30), font=f16)
    tx0 = TXO; ty0 = 70
    iy = ty0 + TH + 30
    dr.text((tx0, iy), 'frame %d   %s' % (n, ACT.get(p['a'], str(p['a']))), fill=col, font=f18)
    dr.text((tx0, iy + 28), 'x %.1f   height %.1f   z %.1f' % (p['x'], p['y'], p['z']), fill=(20, 20, 30), font=f16)
    dr.text((tx0, iy + 54), 'input: %s  stick (%d, %d)   [%s]' % ('A' if p['b'] else '-', p['sx'], p['sy'], p['tag']), fill=(60, 60, 70), font=f14)
    lx = tx0; ly = iy + 90
    for k, lab in (('floor', 'floor'), ('lean', 'leaning face (steep, slidable)'), ('wall', 'wall'), ('under', 'underside / overhang'), ('lz', 'loading-zone floor')):
        dr.line([lx, ly + 8, lx + 26, ly + 8], fill=CK[k], width=5); dr.text((lx + 34, ly), lab, fill=(40, 40, 50), font=f12); ly += 20
    dr.text((20, 12), 'pra_01 RMC v3: Mario climbing the cliff by the star piece cave (real inputs, collision slices)', fill=(20, 20, 30), font=f18)
    dr.text((20, PH + 148), 'Mario drawn as an approximate box (radius ~10, height ~37). Grey dots = earlier frames. Collision from the game\'s loaded collision data.', fill=(100, 100, 110), font=f12)
    im.save(path)
out = '/dev/shm/pmbot/cd_frames'; os.makedirs(out, exist_ok=True)
for fn in os.listdir(out): os.remove(os.path.join(out, fn))
for n in range(len(T)): frame(n, os.path.join(out, 'c%04d.png' % n))
frame(len(T) - 1, '/home/user/HackMidwest/pm-kooper-bot/pra01_rmc_v3_climb_diagram.png')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '4', '-i', os.path.join(out, 'c%04d.png'), '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', '/home/user/HackMidwest/pm-kooper-bot/videos/pra01_rmc_v3_climb_diagram.mp4'], check=True)
print('ok', len(T))
