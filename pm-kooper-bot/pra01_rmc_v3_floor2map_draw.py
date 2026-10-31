import json, glob, collections
from PIL import Image, ImageDraw, ImageFont
L = [r for f in glob.glob('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/f2map_*.json') for r in json.load(open(f))]
def cat(r):
    j, c = r[1]['jump'], r[1]['clip']
    if any(c): return 'clip'
    if j[0] and j[1] is None: return 'stand'
    if any(v for v in j if v): return 'jump_noclip'
    return 'nojump'
COL = {'clip': (40, 160, 70), 'jump_noclip': (240, 180, 40), 'stand': (40, 110, 220), 'nojump': (210, 60, 60)}
LBL = {'clip': 'jumps on frames 2-3; CLIPS only on frame 2', 'jump_noclip': 'jumps (frames 2-3) but never clips',
       'stand': 'standing: jump only on landing frame,\n   cave loads after (no clip)', 'nojump': 'cannot jump (0-5 frames)'}
xs = [r[0][0] for r in L]; ys = [r[0][1] for r in L]
X0, X1 = int(min(xs)) - 1, int(max(xs)) + 2; Y0, Y1 = int(min(ys)) - 3, int(max(ys)) + 4
S = 900 / (X1 - X0); VS = 700 / (Y1 - Y0)
W, H = 900, 700; LEG = 430
im = Image.new('RGB', (W + LEG, H + 110), (246, 247, 249)); dr = ImageDraw.Draw(im)
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
f12, f14, f20 = ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
P = lambda x, y: ((x - X0) * S, 60 + (Y1 - y) * VS)
for x in range(X0, X1 + 1): dr.line([P(x, Y0), P(x, Y1)], fill=(226, 228, 232)); dr.text((P(x, Y0)[0], P(x, Y0)[1] + 4), str(x), fill=(80, 80, 80), font=f12, anchor='mt')
for y in range((Y0 // 5) * 5, Y1 + 1, 5): dr.line([P(X0, y), P(X1, y)], fill=(226, 228, 232)); dr.text((W + 4, P(X0, y)[1]), str(y), fill=(80, 80, 80), font=f12, anchor='lm')
for r in L:
    (x, y, z), c = r[0], cat(r); a = P(x, y); rad = 8 if abs(z + 63) < 0.6 else 6
    dr.ellipse([a[0] - rad, a[1] - rad, a[0] + rad, a[1] + rad], fill=COL[c], outline=(255, 255, 255) if rad == 8 else (40, 40, 40))
dr.text((10, 14), 'pra_01 floor 2: landings after the SECOND tornado jump, jump and clip windows', fill=(20, 20, 30), font=f20)
dr.text((10, H + 80), 'Side view: x left-right, height up. z -63 to -%d (big dots z -63). A tested 0-5 frames after landing; clip = third jump (A 8, down-left, then down).' % int(-min(r[0][2] for r in L)), fill=(80, 80, 80), font=f12)
lx, ly = W + 50, 70; cnt = collections.Counter(cat(r) for r in L)
dr.text((lx, ly), '%d distinct landings from real inputs' % len(L), fill=(20, 20, 30), font=f14); ly += 34
for k in ('clip', 'jump_noclip', 'stand', 'nojump'):
    dr.ellipse([lx, ly, lx + 16, ly + 16], fill=COL[k]); dr.text((lx + 26, ly), '%s (%d)' % (LBL[k], cnt[k]), fill=(30, 30, 30), font=f12); ly += 28 + (14 if '\n' in LBL[k] else 0)
ly += 10
dr.text((lx, ly), 'Same as floor 1: landing sliding blocks\nthe jump for 2 frames; A works on frames\n2 and 3, but only frame 2 clips.\nNo landing has a 2-frame clip window.\nWaiting 4+ frames usually slides you off\nand loads the star piece cave.\nReal inputs, JP, CountPerOp 1.', fill=(30, 30, 30), font=f12)
im.save('/home/user/HackMidwest/pm-kooper-bot/pra01_rmc_v3_floor2map.png'); print(cnt)
