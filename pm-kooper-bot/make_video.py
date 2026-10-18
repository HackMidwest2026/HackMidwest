"""Caption the frames of a record_rta.py run (OUT/f%04d.png + OUT/log.json) and encode OUT.mp4 (30 fps) and
OUT_slow.mp4 (10 fps). The frames around the C-down are held. usage: make_video.py <dir> <out_base> [what-if note]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
d, base = sys.argv[1], sys.argv[2]
note = sys.argv[3] if len(sys.argv) > 3 else ''
L = json.load(open(os.path.join(d, 'log.json')))
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
cd = [l['i'] for l in L if l['tag'].startswith('C-down')][0]
ok = L[cd]['ls'] >= 115.75
first = next(l['i'] for l in L if Image.open(os.path.join(d, 'f%04d.png' % l['i'])).getbbox())
out = 0
for l in L:
    im = Image.open(os.path.join(d, 'f%04d.png' % max(l['i'], first))).crop((104, 100, 696, 500)).convert('RGB')
    dr = ImageDraw.Draw(im)
    dr.rectangle((0, 370, 592, 400), fill=(0, 0, 0))
    dr.text((8, 377), l['tag'], fill=(255, 255, 255), font=font)
    dr.text((8, 6), 'Mario %.1f %.1f %.1f   Laki %.0f %.0f %.0f   speed %.2f' % (l['x'], l['y'], l['z'], l['lx'], l['ly'], l['lz'], l['ls']), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((8, 24), 'history pointer %d   target (%.0f, %.0f)   frame %d' % (l['ptr'], l['tx'], l['tz'], l['i']), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if note: dr.text((8, 42), note, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if l['i'] > cd + 25:
        if ok and l['z'] > 1:
            dr.text((150, 330), 'FRONT SIDE OF THE MIRROR', fill=(120, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
        elif not ok:
            dr.text((120, 330), 'NO CLIP: %.2f < 115.75' % L[cd]['ls'], fill=(255, 90, 90), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    for k in range(8 if cd - 3 <= l['i'] <= cd + 2 else 1):
        im.save(os.path.join(d, 'c%04d.png' % out)); out += 1
for fps, suf in ((30, ''), (10, '_slow')):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', os.path.join(d, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                    '-c:v', 'libx264', '-crf', '20', base + suf + '.mp4'], check=True)
print(out, 'frames ->', base + '.mp4', base + '_slow.mp4')
