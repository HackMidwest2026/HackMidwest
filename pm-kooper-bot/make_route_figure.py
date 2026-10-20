"""Step-by-step figure from record_kpa62_setup.py frames. Each step is 'caption|tag-prefix|first/last[+offset]'.
usage: make_route_figure.py DIR OUT.png 'caption|tag prefix|last' ..."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
d, outp = sys.argv[1], sys.argv[2]; L = json.load(open(os.path.join(d, 'log.json')))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'; font = ImageFont.truetype(F % '-Bold', 16); small = ImageFont.truetype(F % '', 13)
steps = []
for spec in sys.argv[3:]:
    cap, pre, which = spec.split('|')
    off = int(which.split('+')[1]) if '+' in which else 0
    m = [l for l in L if l['tag'].startswith(pre) or (pre.startswith('inp:') and l['inp'].startswith(pre[4:]))]
    l = m[0] if which.startswith('first') else m[-1]
    steps.append((cap, L[min(len(L) - 1, l['i'] + off)]))
W, H, cols = 593, 364, 2
im = Image.new('RGB', (cols * W, ((len(steps) + 1) // 2) * (H + 30)), (15, 15, 15)); dr = ImageDraw.Draw(im)
for n, (cap, l) in enumerate(steps):
    g = Image.open(os.path.join(d, 'f%04d.png' % l['i'])).crop((103, 96, 696, 460)).convert('RGB')
    x = (n % cols) * W; y = (n // cols) * (H + 30)
    im.paste(g, (x, y + 30)); dr.text((x + 8, y + 6), cap, fill=(255, 230, 120), font=font)
    dr.text((x + 8, y + H + 8), 'Mario (%.1f, %.1f, %.1f)' % (l['x'], l['y'], l['z']), fill=(255, 255, 255), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
im.save(outp); print(outp)
