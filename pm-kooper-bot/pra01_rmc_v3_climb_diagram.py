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
f12, f14, f16, f18 = ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 15), ImageFont.truetype(F % '-Bold', 18)
SX0, SX1, SY0, SY1, PW, PH = 455, 540, -75, 180, 540, 700
TX0, TX1, TZ0, TZ1, TW, TH = 455, 540, -95, 100, 540, 520
GW, GH = 1180, 150
CW, CH = 1240, 70 + PH + 40 + GH + 60
def panel(w, h): im = Image.new('RGB', (w + 44, h + 22), (246, 247, 249)); d = ImageDraw.Draw(im); d.rectangle([0, 0, w, h], fill=(255, 255, 255), outline=(200, 200, 205)); return im, d
def frame(n, path):
    p = T[n]; col = (240, 120, 0) if p['a'] == 34 else (220, 40, 40)
    im = Image.new('RGB', (CW, CH), (246, 247, 249)); dr = ImageDraw.Draw(im)
    dr.text((20, 10), 'pra_01 RMC v3: Mario climbing the cliff by the star piece cave (real inputs, collision slices)', fill=(20, 20, 30), font=f18)
    # side view
    sv, d = panel(PW, PH); sx = PW / (SX1 - SX0); sy = PH / (SY1 - SY0)
    S = lambda x, y: ((x - SX0) * sx, (SY1 - y) * sy)
    for y in range(-50, 181, 25): d.line([S(SX0, y), S(SX1, y)], fill=(235, 236, 240))
    for x in range(460, 541, 10): d.line([S(x, SY0), S(x, SY1)], fill=(235, 236, 240))
    for k, (a, b) in section(2, p['z']): d.line([S(a[0], a[1]), S(b[0], b[1])], fill=CK[k], width=4)
    for q in T[:n]:
        c = S(q['x'], q['y']); d.ellipse([c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2], fill=(160, 160, 170))
    if p['y'] > SY0:
        d.rectangle([S(p['x'] - 10, p['y'] + 37), S(p['x'] + 10, p['y'])], outline=col, width=3)
        c = S(p['x'], p['y']); d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=col)
    else:
        c = S(p['x'], SY0); d.polygon([(c[0] - 12, c[1] - 26), (c[0] + 12, c[1] - 26), (c[0], c[1] - 4)], fill=col)
        d.text((c[0] + 16, c[1] - 30), 'Mario below view: height %.0f' % p['y'], fill=col, font=f14)
    d.rectangle([PW + 1, 0, PW + 44, PH + 22], fill=(246, 247, 249)); d.rectangle([0, PH + 1, PW + 44, PH + 22], fill=(246, 247, 249)); d.rectangle([0, 0, PW, PH], outline=(200, 200, 205))
    for y in range(-50, 181, 25): d.text((S(SX1, y)[0] + 4, S(SX1, y)[1]), str(y), fill=(110, 110, 110), font=f12, anchor='lm')
    for x in range(460, 541, 10): d.text((S(x, SY0)[0], S(x, SY0)[1] + 3), str(x), fill=(110, 110, 110), font=f12, anchor='mt')
    im.paste(sv, (20, 70)); dr.text((20, 46), 'SIDE: slice at Mario\'s z = %.1f  (x across, height up)' % p['z'], fill=(20, 20, 30), font=f16)
    # top view
    tv, d = panel(TW, TH); tsx = TW / (TX1 - TX0); tsz = TH / (TZ1 - TZ0)
    Tp = lambda x, z: ((x - TX0) * tsx, (z - TZ0) * tsz)
    d.rectangle([Tp(TX0, -95), Tp(500, -50)], fill=(250, 225, 240)); d.text(Tp(457, -93), 'star piece cave loading zone', fill=(200, 60, 140), font=f12)
    d.rectangle([Tp(TX0, 50), Tp(500, TZ1)], fill=(250, 225, 240)); d.text(Tp(457, 52), 'near cave loading zone (sam_10)', fill=(200, 60, 140), font=f12)
    d.rectangle([Tp(TX0, 0), Tp(TX1, TZ1)], outline=None); d.text(Tp(538, 3), 'SOUTH (near) side', fill=(40, 120, 60), font=f12, anchor='ra'); d.text(Tp(538, -3), 'NORTH side', fill=(170, 60, 60), font=f12, anchor='rb')
    for z in range(-90, 101, 10): d.line([Tp(TX0, z), Tp(TX1, z)], fill=(235, 236, 240))
    for x in range(460, 541, 10): d.line([Tp(x, TZ0), Tp(x, TZ1)], fill=(235, 236, 240))
    d.line([Tp(TX0, 0), Tp(TX1, 0)], fill=(60, 140, 230), width=2)
    for k, (a, b) in section(1, p['y'] + 15): d.line([Tp(a[0], a[2]), Tp(b[0], b[2])], fill=CK[k], width=4)
    for q in T[:n]:
        c = Tp(q['x'], q['z']); d.ellipse([c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2], fill=(160, 160, 170))
    c = Tp(p['x'], p['z']); d.ellipse([c[0] - 10 * tsx, c[1] - 10 * tsz, c[0] + 10 * tsx, c[1] + 10 * tsz], outline=col, width=3)
    d.rectangle([TW + 1, 0, TW + 44, TH + 22], fill=(246, 247, 249)); d.rectangle([0, TH + 1, TW + 44, TH + 22], fill=(246, 247, 249)); d.rectangle([0, 0, TW, TH], outline=(200, 200, 205))
    for z in range(-90, 101, 10): d.text((Tp(TX1, z)[0] + 4, Tp(TX1, z)[1]), str(z), fill=(110, 110, 110), font=f12, anchor='lm')
    for x in range(460, 541, 10): d.text((Tp(x, TZ1)[0], Tp(x, TZ1)[1] + 3), str(x), fill=(110, 110, 110), font=f12, anchor='mt')
    TXO = 20 + PW + 70; im.paste(tv, (TXO, 70)); dr.text((TXO, 46), 'TOP: slice at Mario\'s waist (height %.0f)  (x across, z down)' % (p['y'] + 15), fill=(20, 20, 30), font=f16)
    # info + legend
    iy = 70 + TH + 30
    dr.text((TXO, iy), 'frame %d   %s' % (n, ACT.get(p['a'], str(p['a']))), fill=col, font=f18)
    dr.text((TXO, iy + 26), 'x %.1f   height %.1f   z %.1f' % (p['x'], p['y'], p['z']), fill=(20, 20, 30), font=f16)
    dr.text((TXO, iy + 50), 'input: %s  stick (%d, %d)   [%s]' % ('A' if p['b'] else '-', p['sx'], p['sy'], p['tag']), fill=(60, 60, 70), font=f14)
    lx, ly = TXO, iy + 80
    for k, lab in (('floor', 'floor'), ('lean', 'leaning face (steep, slidable)'), ('wall', 'wall'), ('under', 'underside'), ('lz', 'loading-zone floor')):
        dr.line([lx, ly + 8, lx + 26, ly + 8], fill=CK[k], width=5); dr.text((lx + 34, ly), lab, fill=(40, 40, 50), font=f12); ly += 18
    # height-over-time strip
    gy = 70 + PH + 40; g = Image.new('RGB', (GW + 50, GH + 22), (246, 247, 249)); d = ImageDraw.Draw(g)
    d.rectangle([0, 0, GW, GH], fill=(255, 255, 255), outline=(200, 200, 205))
    Y0, Y1 = -960, 200; G = lambda f, y: (f / (len(T) - 1) * GW, (Y1 - y) / (Y1 - Y0) * GH)
    for y in (-900, -600, -300, 0, 150):
        d.line([G(0, y), G(len(T) - 1, y)], fill=(235, 236, 240)); d.text((GW + 4, G(0, y)[1]), str(y), fill=(110, 110, 110), font=f12, anchor='lm')
    d.line([G(0, 150), G(len(T) - 1, 150)], fill=(150, 150, 160))
    d.line([G(0, -60), G(len(T) - 1, -60)], fill=(60, 170, 80))
    pts = [G(i, q['y']) for i, q in enumerate(T)]; d.line(pts, fill=(160, 160, 170), width=2)
    zc = next((i for i, q in enumerate(T) if q['z'] > 0), None)
    if zc is not None: d.line([G(zc, Y0), G(zc, Y1)], fill=(60, 140, 230), width=2); d.text((G(zc, Y1)[0] + 4, 2), 'crosses mirror (z>0)', fill=(60, 140, 230), font=f12)
    d.line([G(n, Y0), G(n, Y1)], fill=col, width=2); c = G(n, p['y']); d.ellipse([c[0] - 5, c[1] - 5, c[0] + 5, c[1] + 5], fill=col)
    im.paste(g, (20, gy)); dr.text((20, gy - 22), 'HEIGHT over time (whole route; grey line = cave wall top 150, green = floor -60)', fill=(20, 20, 30), font=f16)
    dr.text((20, CH - 24), 'Mario drawn as an approximate box/circle (radius ~10, height ~37). Grey dots = earlier frames. Collision from the game\'s loaded collision data.', fill=(100, 100, 110), font=f12)
    im.save(path)
out = '/dev/shm/pmbot/cd2_frames'; os.makedirs(out, exist_ok=True)
for fn in os.listdir(out): os.remove(os.path.join(out, fn))
for n in range(len(T)): frame(n, os.path.join(out, 'c%04d.png' % n))
frame(len(T) - 1, '/home/user/HackMidwest/pm-kooper-bot/pra01_rmc_v3_climb_diagram.png')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '5', '-i', os.path.join(out, 'c%04d.png'), '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', '/home/user/HackMidwest/pm-kooper-bot/videos/pra01_rmc_v3_climb_diagram.mp4'], check=True)
print('ok', len(T), CW, CH)
