"""Captioned video of a record_kpa62_setup.py run that shows Laki's speed every frame (for the dgb_01 fastest-remount
demo): game view, input, a big Laki-speed readout, and a speed-over-time graph; the C-down moment is replayed slowly.
env: ORIGIN (tag prefix where the speed graph starts), ORIGIN_FRAME (frame number of that first frame, 0), FAST (tag prefix played at 4x)
usage: make_speed_video.py DIR OUT.mp4 'title'"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
d, outp, title = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ''
L = json.load(open(os.path.join(d, 'log.json')))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, small, big, huge = (ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '-Bold', 22), ImageFont.truetype(F % '-Bold', 40))
W, H = 1020, 430
first = next(l['i'] for l in L if Image.open(os.path.join(d, 'f%04d.png' % l['i'])).getbbox())
cd = [l['i'] for l in L if l['inp'].startswith('C-DOWN +')][-1]
ORIGIN = os.environ.get('ORIGIN', 'B: dismount')
b0 = [l['i'] for l in L if l['tag'].startswith(ORIGIN)][0]
vmax = max(30.0, max(l['ls'] for l in L))
def frame(l, tag2=''):
    im = Image.new('RGB', (W, H), (20, 20, 20))
    g = Image.open(os.path.join(d, 'f%04d.png' % max(l['i'], first))).crop((103, 96, 696, 460)).convert('RGB')
    im.paste(g, (0, 0)); dr = ImageDraw.Draw(im)
    if title: dr.text((6, 4), title, fill=(255, 220, 120), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
    if tag2: dr.text((10, 22), tag2, fill=(255, 150, 150), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if l['inp']: dr.text((10, 300), l['inp'], fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((10, 334), 'Mario (%.1f, %.1f, %.1f)' % (l['x'], l['y'], l['z']), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.rectangle((600, 0, W, 392), fill=(245, 245, 245))
    dr.text((612, 14), 'Laki speed', fill=(60, 60, 60), font=big)
    dr.text((612, 44), '%.1f' % l['ls'], fill=(20, 120, 40) if l['i'] >= cd else (30, 30, 30), font=huge)
    dr.text((612, 98), 'needed to clip out in this room: 160+', fill=(170, 40, 40), font=font)
    if 'd' in l: dr.text((612, 118), 'Laki -> frozen target: %.0f' % l['d'], fill=(60, 60, 60), font=font)
    # graph of speed over time from the dismount
    x0, y0, x1, y1 = 612, 140, 1005, 360
    dr.rectangle((x0, y0, x1, y1), outline=(150, 150, 150))
    span = max(1, cd + 20 - b0)
    pts = [(x0 + (k['i'] - b0) / span * (x1 - x0), y1 - k['ls'] / vmax * (y1 - y0)) for k in L if b0 <= k['i'] <= min(l['i'], cd + 20)]
    if len(pts) > 1: dr.line(pts, fill=(40, 110, 220), width=2)
    xc = x0 + (cd - b0) / span * (x1 - x0); dr.line((xc, y0, xc, y1), fill=(220, 150, 40))
    dr.text((x0, y1 + 4), 'frames ->  (orange: C-down, frame %d)' % (cd - b0 + int(os.environ.get('ORIGIN_FRAME', '0'))), fill=(90, 90, 90), font=small)
    dr.text((x0 + 4, y0 + 2), '%.0f' % vmax, fill=(90, 90, 90), font=small)
    dr.rectangle((0, 392, W, H), fill=(0, 0, 0)); dr.text((8, 402), l['tag'], fill=(255, 255, 255), font=font)
    return im
tmp = os.path.join(d, 'c'); os.makedirs(tmp, exist_ok=True)
for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%04d.png' % n)); n += 1
FAST = os.environ.get('FAST', '')                     # tag prefix of a long phase to play at 4x
for l in L:
    if FAST and l['tag'].startswith(FAST):
        if l['i'] % 4: continue
        put(frame(l, '(4x)')); continue
    if l['i'] < b0 - 45 and l['i'] % 2: continue
    put(frame(l, '(2x)' if l['i'] < b0 - 45 else ''))
for l in L[cd - 6: cd + 8]:
    im = frame(l, 'replay 1/4 speed')
    for r in range(4): put(im)
for i in range(30): put(frame(L[-1]))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames')
