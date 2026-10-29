"""Video: pra_02 behind the mirror, the 'pass' that wasn't. Steered push east along the back wall (Mario kept 4 units
behind Lakilester) until Laki reaches x 170, then the angled push (-60 deg, gap 10, stick capped at 20) that seemed to
get past the back-left pillar. Shows the frame contact breaks: Laki leaves hover (state 5) for normal following
(state 0) and just trails Mario. No RAM edits. usage: pra02_contact_break_video.py OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
STATE = 0x8010D188
fstate = lambda: e.u32(STATE) >> 16
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cbv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L():
    a = laki()['addr']; return e.f32(a + 0x38), e.f32(a + 0x3C), e.f32(a + 0x40), e.f32(a + 0x18)
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra02_back_left.st'); e.step(0, 0, 0, 2)
raw = '/dev/shm/pmbot/cbv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
frames = []
def pstep(A, gap, magmax, title, k=None, show=True):
    ux, uz = math.cos(math.radians(A)), math.sin(math.radians(A))
    p = player(e); lx, ly, lz, sp = L(); tx, tz = lx - gap * ux, lz - gap * uz
    d = math.hypot(tx - p['x'], tz - p['z'])
    s_ = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(14, min(magmax, int(d * 8)))) if d > 0.8 else (0, 0)
    e.step(0, *s_, 2)
    lx2, ly2, lz2, sp2 = L(); p2 = player(e); stt = fstate()
    touch = stt == 5 and math.hypot(lx2 - lx, lz2 - lz) > 0.5
    if show:
        path = os.path.join(raw, 'f%05d.png' % len(frames)); subprocess.run(['import', '-window', 'root', path], check=True)
        frames.append((path, 0, s_[0], s_[1], title, k, p2, sp2, math.hypot(lx2 - p2['x'], lz2 - p2['z']), False, (lx2, ly2, lz2), stt, touch))
    return stt
for f in range(89): pstep(0, 4, 80, '1. push east along the back wall (Mario 4 behind Laki)', show=(f % 3 == 0))
lost = None
for k in range(80):
    s = pstep(-60, 10, 20, '2. angled push (-60 deg, gap 10, stick <= 20)', k=k)
    if s != 5 and lost is None:
        lost = k; fr = list(frames[-1]); fr[4] = '3. CONTACT LOST: Laki leaves hover and starts following'; fr[9] = True; frames[-1] = tuple(fr)
AN = {}
print('contact lost at angled frame', lost)
tmp = '/dev/shm/pmbot/snv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
for path, b, sx, sy, title, k, p, spd, dist, mark, lk, stt, touch in frames:
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((10, 300), 'TOUCHING' if touch else ('CONTACT LOST' if k is not None and k >= 0 else ''), fill=(120, 255, 120) if touch else (255, 110, 110), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), ('angled push frame %d   ' % k if k is not None else 'wall push   ') + 'stick (%d, %d)' % (sx, sy), fill=(255, 255, 255), font=font)
    dr.text((8, 392), 'Laki (%.1f, %.1f, %.1f) state %d %s  speed %.1f  dist %.1f' % (lk[0], lk[1], lk[2], stt, '(hover)' if stt == 5 else '(FOLLOWING)', spd, dist), fill=(120, 255, 120) if stt == 5 else (255, 140, 140), font=font)
    dr.text((8, 420), 'Mario (%.2f, %.1f, %.2f)' % (p['x'], p['y'], p['z']), fill=(200, 200, 200), font=font)
    dr.text((8, 444), 'pra_02 behind the mirror: bot-steered push, no RAM edits', fill=(160, 160, 160), font=font)
    put(im)
    if len(frames) and path == frames[0][0]:
        for r in range(20): put(im)
    if mark:
        for r in range(30): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
last = frames[-1][6]
print('wrote', outp, n)
