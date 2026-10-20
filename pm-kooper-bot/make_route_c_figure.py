"""Step-by-step figure of kpa_62 route C from record_kpa62_setup.py frames.
usage: make_route_c_figure.py DIR OUT.png"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
d, outp = sys.argv[1], sys.argv[2]; L = json.load(open(os.path.join(d, 'log.json')))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'; font = ImageFont.truetype(F % '-Bold', 16); small = ImageFont.truetype(F % '', 13)
def first(pred): return next(l for l in L if pred(l))
def last(pred): return [l for l in L if pred(l)][-1]
m = first(lambda l: l['tag'].startswith('C-down: mount'))['i']
rideend = last(lambda l: l['tag'].startswith('ride at walking'))['i']
steps = [
    ('1. On the y-35 ledge: hold RIGHT (pins Mario)', last(lambda l: l['tag'].startswith('hold RIGHT (150'))),
    ('2. Spin: Z + DOWN for 1 frame', first(lambda l: l['tag'].startswith('spin'))),
    ('3. Jump, keep holding RIGHT', first(lambda l: l['tag'].startswith('jump') and l['y'] > 58)),
    ('   ...lands in the tower corner every time', last(lambda l: l['tag'] == 'stand' and l['i'] < 240)),
    ('4. Run DOWN exactly 7 frames (full tilt)', L[m - 1]),
    ('5. C-down: mount, wait 28-36 frames', L[m + 28]),
    ('6. Ride half-tilt LEFT exactly 5 frames', L[rideend + 8]),
    ('7. B: dismount, then hold DOWN', first(lambda l: l['inp'].startswith('DOWN  frame 20'))),
    ('8. C-down on frame 34 after B (+DOWN)', first(lambda l: l['inp'].startswith('C-DOWN + DOWN'))),
    ('9. Laki carries Mario into the tower', first(lambda l: l['in'] and l['i'] > 410)),
]
W, H, cols = 593, 364, 2
im = Image.new('RGB', (cols * W, ((len(steps) + 1) // 2) * (H + 30)), (15, 15, 15)); dr = ImageDraw.Draw(im)
for n, (cap, l) in enumerate(steps):
    g = Image.open(os.path.join(d, 'f%04d.png' % l['i'])).crop((103, 96, 696, 460)).convert('RGB')
    x = (n % cols) * W; y = (n // cols) * (H + 30)
    im.paste(g, (x, y + 30)); dr.text((x + 8, y + 6), cap, fill=(255, 230, 120), font=font)
    dr.text((x + 8, y + H + 8), 'Mario (%.1f, %.1f, %.1f)' % (l['x'], l['y'], l['z']), fill=(255, 255, 255), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
im.save(outp)
