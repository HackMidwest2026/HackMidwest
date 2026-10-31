import json, glob
from PIL import Image, ImageDraw, ImageFont
L = [r for f in glob.glob('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/jmap_*.json') for r in json.load(open(f))]
def cat(r):
    act, ok = r[1]['act'], r[1]['ok']
    if act == 0 and len(ok) == 1: return 'stand_now' if ok[0] else 'stand_load'
    w = [i for i, v in enumerate(ok) if v]
    if not w: return 'slide_no'
    return 'slide_23' if (2 in w and 3 in w) else 'slide_2'
COL = {'slide_23': (40, 160, 70), 'slide_2': (150, 200, 60), 'stand_now': (40, 110, 220), 'slide_no': (210, 60, 60), 'stand_load': (150, 90, 190)}
LBL = {'slide_23': 'sliding: A works 2 or 3 frames after landing', 'slide_2': 'sliding: A works only 2 frames after landing',
       'stand_now': 'standing: A only on the landing frame\n   (cave loads 1 frame later)', 'slide_no': 'sliding: A never jumps (0-5 frames)',
       'stand_load': 'standing: no jump, cave loads 1 frame later'}
X0, X1, Y0, Y1, S = 488, 501, 0, 34, 52
W, H = int((X1 - X0) * S), int((Y1 - Y0) * S / 2.2)
LEG = 470
im = Image.new('RGB', (W + LEG, H + 110), (246, 247, 249)); dr = ImageDraw.Draw(im)
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
f12, f14, f20 = ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
P = lambda x, y: ((x - X0) * S, 60 + (Y1 - y) * S / 2.2)
for x in range(X0, X1 + 1): dr.line([P(x, Y0), P(x, Y1)], fill=(226, 228, 232)); dr.text((P(x, Y0)[0], P(x, Y0)[1] + 4), str(x), fill=(80, 80, 80), font=f12, anchor='mt')
for y in range(0, 35, 5): dr.line([P(X0, y), P(X1, y)], fill=(226, 228, 232)); dr.text((W + 4, P(X0, y)[1]), str(y), fill=(80, 80, 80), font=f12, anchor='lm')
dr.rectangle([P(X0, Y1), P(500, Y0)], outline=(150, 120, 200), width=2)
dr.text(P(488.2, 33.5), 'x < 500: over the star piece cave loading zone', fill=(130, 100, 180), font=f12)
for r in sorted(L, key=lambda r: cat(r) == 'slide_23'):
    (x, y, z), c = r[0], cat(r)
    a = P(x, y); rad = 7 if abs(z + 63) < 0.6 else 5
    dr.ellipse([a[0] - rad, a[1] - rad, a[0] + rad, a[1] + rad], fill=COL[c], outline=(255, 255, 255) if rad == 7 else (40, 40, 40))
dr.text((10, 14), 'pra_01: landings after the FIRST tornado jump, and whether you can jump from them', fill=(20, 20, 30), font=f20)
dr.text((10, H + 80), 'Side view: x left-right (toward the cliff = left), height up. All landings are on the cave arch\'s south side, z -63 to -66 (big dots z -63, small z -64 to -66).', fill=(80, 80, 80), font=f12)
lx, ly = W + 50, 70
dr.text((lx, ly), '%d distinct landings from real inputs' % len(L), fill=(20, 20, 30), font=f14); ly += 34
import collections; cnt = collections.Counter(cat(r) for r in L)
for k in ('slide_23', 'slide_2', 'stand_now', 'slide_no', 'stand_load'):
    dr.ellipse([lx, ly, lx + 16, ly + 16], fill=COL[k]); dr.text((lx + 26, ly), '%s (%d)' % (LBL[k], cnt[k]), fill=(30, 30, 30), font=f12); ly += 28 + (14 if k == 'stand_now' else 0)
ly += 10
dr.text((lx, ly), 'Rule of thumb:\n- heights 6-16: sliding, jump 2-3 frames after\n  landing -> this is where the route jumps from\n- heights 17-29 sliding: cannot jump at all\n- standing near the top (x ~491, height 22-26):\n  jump on the landing frame only\n- standing low by x 499 or high by x 495-490:\n  no jump, star piece cave loads next frame\nReal inputs, JP, CountPerOp 1. A tested 0-5\nframes after landing (held up to 6 frames).', fill=(30, 30, 30), font=f12)
im.save('/home/user/HackMidwest/pm-kooper-bot/pra01_rmc_v3_jumpmap.png'); print(im.size, cnt)
