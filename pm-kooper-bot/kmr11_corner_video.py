"""Video of the closest spin-jump landing into the trapped arena's acute corner (kmr_11, right after the Goomba
King): Bush2's wall meets the arena's south-east wall at about (-227.1, 48.5) in the low pocket (y -8).
Replays a spin_land_sweep pre-landing record (JSON with 'inputs': start, spin_deg, jump_frame, air_deg): spin (Z) on
game frame 0 toward spin_deg, A on jump_frame, steer air_deg, then hold toward the corner for 20 frames after landing.
Captioned frames + a 1/4-speed repeat of the landing. usage: kmr11_corner_video.py PRE.json OUT.mp4"""
import json, math, os, subprocess, sys
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont

pre, outp = json.load(open(sys.argv[1])), sys.argv[2]
CORNER = (-227.1, 48.5)
inp = pre['inputs']
def stick_for(deg, mag):
    r = math.radians(deg); return int(round(mag * math.cos(r))), int(round(-mag * math.sin(r)))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kmrcvid')
e.load('states/kmr11_e0_kingdone.st'); e.step(0, 0, 0, 2)
e.w8(game_status(e) + 0x74, 1)
sx0, sz0 = inp['start']
e.wf32(PLAYER + PS_POS, sx0); e.wf32(PLAYER + PS_POS + 4, -8.0); e.wf32(PLAYER + PS_POS + 8, sz0)
e.step(0, 0, 0, 200)                                   # let the camera settle
shot = '/dev/shm/pmbot/kmrcvid_raw'; os.makedirs(shot, exist_ok=True)
for fn in os.listdir(shot): os.remove(os.path.join(shot, fn))
st, sta = stick_for(inp['spin_deg'], 80), stick_for(inp['air_deg'], 80) if inp['air_deg'] is not None else (0, 0)
toward = math.degrees(math.atan2(CORNER[1] - pre['pos'][2], CORNER[0] - pre['pos'][0]))
stc = stick_for(toward, 80)
log, airborne, land = [], False, None
for f in range(80):
    b = Z if f == 0 else (A if f == inp['jump_frame'] else 0)
    s = st if f <= inp['jump_frame'] else sta
    if land is not None or f >= pre['land_f']: s = stc
    e.step(b, s[0], s[1], 2)
    p = player(e)
    subprocess.run(['import', '-window', 'root', os.path.join(shot, 'f%04d.png' % f)], check=True)
    log.append({'f': f, 'b': b, 'st': s, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'act': p['action'], 'spd': p['speed']})
    if p['action'] in (3, 4, 5, 8): airborne = True
    elif airborne and land is None: land = f
    if land is not None and f >= land + 20: break
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 10: 'land', 26: 'spin'}
tmp = '/dev/shm/pmbot/kmrcvid_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
frames = []
for l in log:
    im = Image.new('RGB', (593, 450), (20, 20, 20))
    im.paste(Image.open(os.path.join(shot, 'f%04d.png' % l['f'])).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), 'kmr_11 trapped arena: spin jump land into the Bush2 corner (-227, 48.5)', fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    label = ('Z (spin) + ' if l['b'] == Z else 'A (jump) + ' if l['b'] == A else '') + 'stick (%d, %d)' % tuple(l['st'])
    dr.text((10, 300), label, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    d = math.hypot(l['x'] - CORNER[0], l['z'] - CORNER[1])
    dr.text((8, 370), 'frame %d  %s  Mario (%.2f, %.2f, %.2f)  speed %.2f' % (l['f'], AN.get(l['act'], l['act']), l['x'], l['y'], l['z'], l['spd']), fill=(255, 255, 255), font=font)
    dr.text((8, 392), 'distance to the corner point %.2f%s' % (d, '  <- LANDING' if l['f'] == land else ''),
            fill=(255, 150, 150) if l['f'] == land else (200, 200, 200), font=font)
    dr.text((8, 414), 'closest of 5000 spin-jump setups; start (%.0f, %.0f), spin %.0f deg, A on frame %d' % (sx0, sz0, inp['spin_deg'], inp['jump_frame']), fill=(160, 160, 160), font=font)
    frames.append(im)
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%04d.png' % n)); n += 1
for im in frames: put(im)
for im in frames[max(0, land - 4): land + 8]:
    for r in range(4): put(im)
for r in range(20): put(frames[-1])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames; landing frame', land, 'end', log[-1])
