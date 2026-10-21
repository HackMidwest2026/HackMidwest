"""Video of the isk_11 Ruins Stones Skip clip with a forced mount speed (exploration: Mario walks to the -575 step at (X, Z);
Laki's moveSpeed is held at S until the mount reads it, a RAM write). Record with the Glide64mk2 plugin: Rice draws
the ruins' shaded sprites black. C-down, the mount lands Mario past
the front edge, Mario steers toward the isk_19 exit floor (collider 13) while falling, the floor-above trigger loads
isk_19. usage: isk11_clip_video.py OUT.mp4 [X Z S]"""
import math, os, subprocess, sys
from emu import *
from pm import *
from corner_sweep import stick_for
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]; X, Z, S = (float(a) for a in sys.argv[2:5]) if len(sys.argv) > 4 else (316.0, 532.0, 96.0)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/icv')
raw = '/dev/shm/pmbot/icv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 2: 'run', 8: 'fall', 33: 'ride'}
frames = []
def grab(label, note):
    path = os.path.join(raw, 'f%05d.png' % len(frames))
    subprocess.run(['import', '-window', 'root', path], check=True)
    lk = [q for q in npcs(e) if q['id'] == -4]
    frames.append((path, label, note, player(e), where(e)[1], e.s16(GAME_MODE), e.f32(lk[0]['addr'] + 0x18) if lk else 0.0))
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
lk = [q for q in npcs(e) if q['id'] == -4][0]['addr']
from nav import go_to
for i in range(15): e.step(0, 0, 0, 2); grab('', 'isk_11, puzzle unsolved')
for (wx, wz) in ((250, 500), (255, 536), (285, 536), (X, Z)):
    for k in range(200):
        p = player(e)
        if math.hypot(wx - p['x'], wz - p['z']) < 4: break
        st = stick_for(math.degrees(math.atan2(wz - p['z'], wx - p['x'])) % 360, 80 if math.hypot(wx - p['x'], wz - p['z']) > 12 else 30)
        e.step(0, st[0], st[1], 2); grab('WALK', 'walk down to the 2nd step from the bottom (y -575)')
for i in range(30): e.step(0, 0, 0, 2); grab('', 'Mario on the 2nd step from the bottom (y -575), x %.0f' % player(e)['x'])
e.wf32(lk + 0x18, S); e.step(D_CBUTTON, 0, 0, 2); grab('C-DOWN', 'Laki speed %.0f (RAM) when the mount reads it' % S)
for i in range(20):
    if e.u8(PLAYER + PS_ACTION) == 33: break
    e.wf32(lk + 0x18, S); e.step(0, 0, 0, 2); grab('C-DOWN', 'mount: 4 test moves of %.0f units decide the landing point' % S)
for f in range(160):
    p = player(e)
    st = stick_for(math.degrees(math.atan2(540 - p['z'], 225 - p['x'])) % 360, 80) if f > 4 else (0, 0)
    e.step(0, st[0], st[1], 2)
    grab('HOLD TO EXIT FLOOR' if f > 4 else '', 'landing point past the front edge; steer toward the isk_19 exit floor (x 188-252) while falling')
    if where(e)[1] == 16 and e.s16(GAME_MODE) == 4: break
for i in range(90):
    e.step(0, 0, 0, 2)
    if i % 2 == 0: grab('', 'isk_19 (Boss Antechamber)' if where(e)[1] == 16 else 'loading isk_19')
tmp = '/dev/shm/pmbot/icv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
for i, (path, label, note, p, mp, gm, spd) in enumerate(frames):
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), 'isk_11 Ruins Stones Skip: mount-speed clip (Laki speed forced to %.0f)' % S, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if label: dr.text((10, 300), label, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), 'Mario (%.0f, %.0f, %.0f) %s   Laki speed %.1f' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action']), spd), fill=(255, 255, 255), font=font)
    dr.text((8, 392), 'map %s   mode %s' % ({10: 'isk_11', 16: 'isk_19'}.get(mp, mp), {4: 'field', 5: 'change map'}.get(gm, gm)), fill=(120, 255, 120) if mp == 16 else (200, 200, 200), font=font)
    dr.text((8, 430), note, fill=(180, 180, 180), font=font)
    im.save(os.path.join(tmp, 'c%05d.png' % i))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, len(frames), 'frames; final map', frames[-1][4])
