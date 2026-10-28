"""Video: NO-SPIN, cardinal-only (right / down / A) ending for the WORKING right-side north->south clip with Speedy Spin + a long touching push past the north-wall bump
(pra18_ns_jumprun.py hit: CORNER freeze, pushes (180,250)+(240,120)+(180,250), spin start (522,-123), stick 52 deg,
spin 3 frames, jump (A 6 frames), land and run to (571.5,-15), C-down on frame 23 = the frame Laki's speed spikes).
DIAGNOSTIC SETUP: start (715,-125) placed in RAM, Speedy Spin equipped by a badge write; all inputs after are real and
Laki's speed is never written. usage: pra18_ns_speedy_video.py OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
PTR, STATE, HIST = 0x8010D17C, 0x8010D188, 0x8010CEF8
PUSHSEQ, S, ANG, K, H, T, CDF = [(180, 250, 4), (240, 120, 6), (180, 250, 4)], (522, -123), 52.0, 3, 6, (571.5, -15), 23
e = Emu('pm-jp.z64', '/dev/shm/pmbot/spv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
fstate = lambda: e.u32(STATE) >> 16
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 715.0); e.wf32(PLAYER + PS_POS + 8, -125.0)                     # DIAGNOSTIC start
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
for i in range(20): e.step(0, 0, 0, 2)
raw = '/dev/shm/pmbot/spv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
frames = []; REC = [True]
def step(b, sx, sy, title, show=True):
    lx0, lz0, _ = L(); e.step(b, sx, sy, 2)
    lx, lz, sp = L(); p = player(e); k = e.u32(PTR)
    touch = fstate() == 5 and math.hypot(lx - lx0, lz - lz0) > 0.5 and math.hypot(lx - p['x'], lz - p['z']) < 20
    if REC[0] and show:
        path = os.path.join(raw, 'f%05d.png' % len(frames)); subprocess.run(['import', '-window', 'root', path], check=True)
        frames.append((path, b, sx, sy, title, p, lx, lz, sp, fstate(), (e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12)), touch))
    return p, sp
t1 = '1. mount Laki, ride into the NE corner, get off'
step(D_CBUTTON, 0, 0, t1, False)
for i in range(40): step(0, 0, 0, t1, False)
for i in range(20): step(0, 80, -40, t1, False)
step(D_CBUTTON, 80, 0, t1, False)
for i in range(60): step(0, 0, 0, t1, False)
t2 = '2. lead Laki out west and back along the north wall into the NE corner'
for i in range(20): step(0, *st(180, 80), t2, False)
for i in range(30): step(0, 0, 0, t2, False)
for i in range(10): step(0, *st(270, 80), t2, False)
for i in range(30): step(0, *st(0, 80), t2, False)
for i in range(8): step(0, *st(90, 80), t2, False)
for i in range(30): step(0, 0, 0, t2, False)
t3 = '3. up/down taps beside Laki: history fills (39 points) and FREEZES'
for i in range(30):
    for j in range(4): step(0, *st(90 if i % 2 else 270, 30), t3, False)
    step(0, 0, 0, t3, False)
t4 = '1. touching push west along the north wall, around the bump (shown at 2x)'
for A_, C_, G_ in PUSHSEQ:
    ux, uz = math.cos(math.radians(A_)), math.sin(math.radians(A_))
    for f in range(C_):
        p = player(e); lx, lz, _ = L(); tx, tz = lx - G_ * ux, lz - G_ * uz
        d = math.hypot(tx - p['x'], tz - p['z'])
        s_ = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
        step(0, *s_, t4, show=(f % 2 == 0 and f < C_ - 0))
for i in range(10): step(0, 0, 0, '', False)
for i in range(30):
    p0 = player(e)['x']; step(0, *st(180, 80), '2. hold LEFT along the wall: Mario stops at x 513.00', show=(i < 6))
    if abs(player(e)['x'] - p0) > 0.01 or i % 6 == 0: frames.append(frames[-1]) if False else None
for i in range(3): step(0, 0, 0, '', False)
cd = None; f = 0
for i in range(12): step(0, *st(0, 80), '3. hold RIGHT exactly 12 frames (Mario to x 567.56)'); f += 1
for i in range(6): step(0, *st(90, 80), '4. hold DOWN exactly 6 frames'); f += 1
phase = 1; jt = 0
for i in range(70):
    q = player(e); grounded = q['action'] in (0, 1, 2)
    if phase == 1:
        b = A if jt < 6 else 0; jt += 1; t = '5. jump (A) holding DOWN'
        if jt > 3 and grounded: phase = 3; jt = 0
    if phase == 3:
        b = A if jt < 5 else 0; jt += 1; t = '6. jump again on landing, A held exactly 5 frames, holding DOWN'
        if jt > 3 and grounded: phase = 4
    if phase == 4: b = 0; t = '7. keep holding DOWN'
    if f == 47:
        cd = len(frames); step(b | D_CBUTTON, *st(90, 80), '8. C-down 1 frame after landing (the frame Laki dashes)'); break
    step(b, *st(90, 80), t); f += 1
for i in range(60): step(0, 0, 0, 'mount pushes Mario + Lakilester through the mirror')
tmp = '/dev/shm/pmbot/spv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 26: 'spin', 33: 'ride'}
STN = {0: 'following', 5: 'hovering (Mario within 40)', 15: 'settling', 1: 'hop', 2: 'hop'}
n = 0; pushes = 0
for j, (path, b, sx, sy, title, p, lx, lz, sp, fs, tgt, touch) in enumerate(frames):
    pushes += touch
    im = Image.new('RGB', (593, 490), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if touch: dr.text((10, 270), 'TOUCHING - push frame %d' % pushes, fill=(120, 255, 255), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    lab = ' '.join(x for m, x in ((D_CBUTTON, 'C-DOWN'), (Z, 'Z'), (A, 'A')) if b & m)
    if lab: dr.text((10, 300), lab, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    hl = j == cd
    need = 616 - p['x']
    dr.text((8, 368), 'stick (%d, %d)   Laki %s, target (%.0f, %.0f)' % (sx, sy, STN.get(fs, fs), tgt[0], tgt[1]), fill=(255, 255, 255), font=font)
    dr.text((8, 390), 'Laki speed %.2f   Laki-Mario %.1f' % (sp, math.hypot(lx - p['x'], lz - p['z'])) + ('  (clip window %.1f-%.2f)' % (need - max(0, 0.9 - 0.3 * (p['x'] - 569)), need) if hl else ''),
            fill=(255, 140, 120) if hl else (200, 200, 200), font=big if hl else font)
    dr.text((8, 418), 'Mario (%.2f, %.1f, %.2f) %s' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action'])), fill=(200, 200, 200), font=font)
    dr.text((8, 440), 'no spin, no diagonals: right / down / A only', fill=(160, 160, 160), font=font)
    dr.text((8, 462), 'pra_18 right side only; start + badge set in RAM, Laki speed NOT edited', fill=(160, 160, 160), font=font)
    im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
    if hl:
        for r in range(60): im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
cf = frames[cd]
print('wrote', outp, n, 'frames; pushes', pushes, '; C-down at mario x %.2f laki speed %.2f; end action %d z %.1f' % (cf[5]['x'], cf[8], frames[-1][5]['action'], frames[-1][5]['z']))
