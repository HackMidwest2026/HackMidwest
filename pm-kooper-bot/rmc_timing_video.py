"""Render the replayed inputs from rmc_timing.py as a video with a frame counter, timer and input display.
usage: rmc_timing_video.py v1|v2|v3 out.mp4   (needs DISPLAY=:99 and M64P_GFX=glide64mk2)"""
import os, sys, json, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
nm, outp = sys.argv[1], sys.argv[2]
D = json.load(open('data/rmc_timing_%s.json' % nm))[nm]
TITLE = {'v1': 'RMC v1  pra_02 switch-block clip (frame-perfect hops)', 'v2': 'RMC v2  pra_02 switch-block clip (RTA version)',
         'v3': 'RMC v3  pra_01 Ultra Boots climb', 'lo': 'RMC Laki outside  pra_01 stale-target push'}[nm]
MAPS = {(21, 0): 'pra_01', (21, 1): 'pra_02', (20, 9): 'sam_10', (21, 2): 'next room'}
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rv%s' % nm)
for i in range(150): e.step(0, 0, 0, 2)
raw = '/dev/shm/pmbot/rv_%s' % nm; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, mid, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 16), ImageFont.truetype(F % '-Bold', 26)
e.load('states/pra02_topdoor_closed.st')
AF = os.environ.get('AUDCAP_FILE'); aoff = os.path.getsize(AF) if AF else 0   # audio written from here on is this replay's
nframes = 0
inp = D['inputs']; af = D['door_A_frame']; TM = [0.0] + D['times']; vf = 0; marks = {v: k for k, v in D['marks'].items()}
tail = 12
W, H, GW, GH = 860, 400, 592, 400
note = ''
for n in range(0, len(inp) + 1):
    if n > 0:
        b, x, y = inp[n - 1]; e.step(b, x, y, 2)
    else: b, x, y = 0, 0, 0
    if n > af + tail: break
    shot = os.path.join(raw, 's.png')
    if n == 0: continue                      # frame 0 = the loaded state; nothing rendered yet, frame 1 is drawn twice below
    subprocess.run(['import', '-window', 'root', shot], check=True)
    im = Image.new('RGB', (W, H), (18, 18, 22)); im.paste(Image.open(shot).crop((104, 100, 104 + GW, 100 + GH)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im); X = GW + 14
    if n in marks: note = '%s @ %d' % (marks[n], n)
    t_s = TM[min(n, af)]                       # real (emulated-clock) seconds since the door closed
    dr.text((X, 10), nm.upper(), fill=(255, 220, 120), font=big)
    dr.text((X, 46), '%6.2f s' % t_s, fill=(255, 255, 255), font=big)
    dr.text((X, 80), '= %5.1f fr' % (t_s * 30), fill=(200, 200, 200), font=mid)
    if n >= af: dr.text((X, 114), 'END: door A (%.2f s)' % TM[af], fill=(120, 255, 120), font=mid)
    w = where(e)[:2]; p = player(e)
    dr.text((X, 142), 'map var: %s' % MAPS.get(w, str(w)), fill=(200, 200, 200), font=font)  # set when a door/LZ fires
    dr.text((X, 160), 'x %.0f  y %.0f  z %.0f' % (p['x'], p['y'], p['z']), fill=(200, 200, 200), font=font)
    dr.text((X, 178), ('front side' if p['z'] > 0 else 'back side') + ' of mirror', fill=(120, 255, 120) if p['z'] > 0 else (255, 160, 160), font=font)
    dr.text((X, 196), note, fill=(255, 220, 120), font=font)
    cx, cy, r = X + 60, 280, 48
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(150, 150, 150), width=2)
    px, py = cx + x / 80 * r, cy - y / 80 * r
    dr.line((cx, cy, px, py), fill=(230, 230, 230), width=3); dr.ellipse((px - 7, py - 7, px + 7, py + 7), fill=(240, 80, 80))
    for i, (bit, lab, col) in enumerate(((A, 'A', (70, 120, 255)), (B, 'B', (60, 200, 90)), (Z, 'Z', (200, 200, 200)), (D_CBUTTON, 'Cv', (240, 200, 40)))):
        bx, by = X + 130 + (i % 2) * 54, 240 + (i // 2) * 44
        on = bool(b & bit)
        dr.rounded_rectangle((bx, by, bx + 46, by + 36), radius=8, fill=col if on else (40, 40, 40), outline=col, width=2)
        dr.text((bx + 23, by + 18), lab, fill=(0, 0, 0) if on else col, font=mid, anchor='mm')
    dr.text((8, GH - 22), TITLE, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    # real-time pacing: during room transitions one game frame is held for several VIs, so repeat it
    target = round(TM[n] * 30)
    while vf <= target: im.save(os.path.join(raw, 'c%05d.png' % vf)); vf += 1
    nframes = vf
vid = outp if not AF else os.path.join(raw, 'v.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(raw, 'c%05d.png'), '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-crf', '22', vid], check=True)
if AF:
    # audio captured by audcap.so for this replay; the game queues sound slightly ahead of the picture, so trim that
    # lead (audio length - video length) from the start, then mux
    import wave
    rate = int(open(AF + '.rate').read()); data = open(AF, 'rb').read()[aoff:]
    lead = len(data) / 4 / rate - nframes / 30
    if lead > 0: data = data[int(lead * rate) * 4:]
    wv = os.path.join(raw, 'a.wav'); w = wave.open(wv, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data); w.close()
    print('audio: rate %d, lead trimmed %.3f s' % (rate, lead))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', wv, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', outp], check=True)
print('wrote', outp)
