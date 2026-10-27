"""Video: closest RIGHT-SIDE north->south attempt with a real TOUCHING Lakilester push (from pra18_ns_ne_push.py:
A 190, 35 push frames, waypoint (650,-80) with a Speedy Spin, then the clip spot (570,-15)). Shows the NE-pocket
history freeze, every push frame where Mario's collider moves Laki (TOUCHING), Laki's follow state / frozen target,
the dash when the history reopens, and C-down on the frame Laki is fastest on the clip spot. No clip.
DIAGNOSTIC SETUP: start (715,-125) placed in RAM; all inputs after are real; Laki's speed never written.
usage: pra18_ns_ne_video.py OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
PTR, STATE, HIST = 0x8010D17C, 0x8010D188, 0x8010CEF8
A, C, GAP, WP, T = 190, 35, 4, (650, -80), (570, -15)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nev')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
fstate = lambda: e.u32(STATE) >> 16
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 715.0); e.wf32(PLAYER + PS_POS + 8, -125.0)                     # DIAGNOSTIC
for i in range(20): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/nev_0.st'; e.save(b0)
REC = [False]; frames = []; raw = '/dev/shm/pmbot/nev_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
def step(b, sx, sy, title, skip=False):
    lx0, lz0, _ = L()
    e.step(b, sx, sy, 2)
    lx, lz, sp = L(); p = player(e); k = e.u32(PTR)
    touch = fstate() == 5 and math.hypot(lx - lx0, lz - lz0) > 0.5 and math.hypot(lx - p['x'], lz - p['z']) < 20
    info = (b, sx, sy, title, p, lx, lz, sp, fstate(), (e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12)), touch)
    if REC[0] and not skip:
        path = os.path.join(raw, 'f%05d.png' % len(frames))
        subprocess.run(['import', '-window', 'root', path], check=True); frames.append((path,) + info)
    return info
def run(cdown_at=None):
    e.load(b0); log = []
    step(D_CBUTTON, 0, 0, '1. mount Laki in the NE pocket (north of statue 3)', True)
    for i in range(40): step(0, 0, 0, '1. mount Laki in the NE pocket (north of statue 3)', True)
    for i in range(20): step(0, 80, -40, '1. ride into the NE corner')
    step(D_CBUTTON, 80, 0, '2. get off')
    for i in range(60): step(0, 0, 0, '2. get off', i < 50)
    for i in range(18): step(0, *st(170, 80), '3. walk out so Laki follows (his history pointer leaves 0)')
    for i in range(40): step(0, 0, 0, '3. walk out so Laki follows (his history pointer leaves 0)', i < 30)
    for i in range(18): step(0, *st(350, 80), '4. walk back into the pocket')
    for i in range(10): step(0, 0, 0, '4. walk back into the pocket')
    for i in range(30):
        for j in range(4): step(0, *st(90 if i % 2 else 270, 30), '5. up/down taps beside Laki: history fills (39 points) and FREEZES')
        step(0, 0, 0, '5. up/down taps beside Laki: history fills (39 points) and FREEZES')
    ux, uz = math.cos(math.radians(A)), math.sin(math.radians(A))
    for f in range(C):
        p = player(e); lx, lz, _ = L(); tx, tz = lx - GAP * ux, lz - GAP * uz
        d = math.hypot(tx - p['x'], tz - p['z'])
        s = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
        step(0, *s, '6. touching push: Mario stays 4 units behind Laki, pushing him west')
    n = 0
    for tx, tz, title, spin in ((WP[0], WP[1], '7. Speedy Spin away (Z) toward (650,-80)', True), (T[0], T[1], '8. go to the clip spot (570,-15)', False)):
        for f in range(80):
            q = player(e); dd = math.hypot(q['x'] - tx, q['z'] - tz)
            if dd <= 1.5: break
            if cdown_at is not None and n == cdown_at: return log
            s = st(math.degrees(math.atan2(tz - q['z'], tx - q['x'])), 80 if dd > 8 else 25)
            info = step(Z if (spin and f == 0) else 0, *s, title); n += 1
            log.append((n, info[4], info[7]))
    for f in range(40):
        if cdown_at is not None and n == cdown_at: return log
        info = step(0, *((0, 0) if f < 20 else st(270 if f % 2 else 90, 30)), '9. stand / nudge on the clip spot'); n += 1
        log.append((n, info[4], info[7]))
    return log
log = run()
zone = [(n, p['x'], sp) for n, p, sp in log if p['action'] in (0, 1, 2) and 568 <= p['x'] <= 576 and -20 <= p['z'] <= -12]
nb, xb, sb = max(zone, key=lambda t: t[2])
print('best frame on spot', nb, 'x %.2f speed %.2f need %.2f' % (xb, sb, 616 - xb), flush=True)
REC[0] = True
run(cdown_at=nb)
step(D_CBUTTON, 0, 0, '10. C-down on the frame Laki is fastest on the clip spot')
mark = len(frames) - 2
for i in range(45): step(0, 0, 0, 'result: mount does not clip (speed %.1f, needs %.0f)' % (sb, round(616 - xb)))
tmp = '/dev/shm/pmbot/nev_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 26: 'spin', 33: 'ride'}
ST = {0: 'following', 5: 'hovering (Mario within 40)', 15: 'settling'}
n = 0; pushes = 0
for j, (path, b, sx, sy, title, p, lx, lz, sp, fs, tgt, touch) in enumerate(frames):
    pushes += touch
    im = Image.new('RGB', (593, 490), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if touch: dr.text((10, 270), 'TOUCHING - push frame %d' % pushes, fill=(120, 255, 255), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    if b & D_CBUTTON: dr.text((10, 300), 'C-DOWN', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    if b & Z: dr.text((10, 300), 'Z (spin)', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 368), 'stick (%d, %d)   Laki %s, target (%.0f, %.0f)' % (sx, sy, ST.get(fs, fs), tgt[0], tgt[1]), fill=(255, 255, 255), font=font)
    hl = j == mark
    dr.text((8, 390), 'Laki speed %.2f   Laki-Mario %.1f' % (sp, math.hypot(lx - p['x'], lz - p['z'])) + ('   (needs %.0f here)' % (616 - p['x']) if hl else ''),
            fill=(255, 140, 120) if hl else (200, 200, 200), font=big if hl else font)
    dr.text((8, 418), 'Mario (%.1f, %.1f) %s   Laki (%.1f, %.1f)' % (p['x'], p['z'], AN.get(p['action'], p['action']), lx, lz), fill=(200, 200, 200), font=font)
    dr.text((8, 440), 'clip needs Laki speed = 616 - Mario x (42-46 at x 574-570)', fill=(160, 160, 160), font=font)
    dr.text((8, 462), 'pra_18 right side only; start placed in RAM, Laki speed NOT edited', fill=(160, 160, 160), font=font)
    im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
    if hl:
        for r in range(45): im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames; touching push frames', pushes, '; end', frames[-1][5]['x'], frames[-1][5]['z'], frames[-1][5]['action'])
