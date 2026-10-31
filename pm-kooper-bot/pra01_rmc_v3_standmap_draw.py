import json, glob
from PIL import Image, ImageDraw, ImageFont
out = [o for f in sorted(glob.glob('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/vmap_*.json')) for o in json.load(open(f))]
X0, X1, Z0, Z1, S = 494, 536, -78, -42, 22
W, H = int((X1 - X0) * S), int((Z1 - Z0) * S)
LEG = 330
im = Image.new('RGB', (W + LEG, H + 70), (245, 246, 248)); dr = ImageDraw.Draw(im)
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
f12, f14, f16, f20 = [ImageFont.truetype(F % '', s) for s in (12, 14, 16)] + [ImageFont.truetype(F % '-Bold', 20)]
P = lambda x, z: ((x - X0) * S, (z - Z0) * S + 50)
COL = {20: (46, 160, 67), 30: (24, 150, 160), 40: (40, 100, 210), 60: (230, 140, 30), 80: (210, 50, 50)}
# cave loading zone
dr.rectangle([P(X0, Z0), P(500, -50)], fill=(225, 215, 245)); dr.text(P(495, -76), 'star piece cave\nloading zone\n(x < 500)', fill=(110, 80, 170), font=f12)
# cliff (approx: lower face from (500,-50) to (510,0)), drawn as hatched region
cliff = [P(500, -50), P(500 + 0.2 * 8, -42), P(X0, -42), P(X0, -50)]
dr.polygon([P(500, -50), P(501.6, -42), P(X0, -42), P(X0, -50)], fill=(190, 200, 215)); dr.text(P(495, -47), 'cliff', fill=(70, 80, 100), font=f12)
# grid cells
for x, z, w in out:
    tx = 500 + round((x - 500) / 1.5) * 1.5 if w is not None else x
    tz = -74 + round((z + 74) / 1.5) * 1.5 if w is not None else z
    a, b = P(tx - 0.72, tz - 0.72), P(tx + 0.72, tz + 0.72)
    if w is None: continue
    if not w: dr.rectangle([a, b], fill=(200, 200, 205))
    else:
        m = min(t for t, _ in w); dr.rectangle([a, b], fill=COL[m])
        dr.text(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), str(len(w)), fill=(255, 255, 255), font=f12, anchor='mm')
# axes
for x in range(496, 537, 4): dr.text(P(x, Z0), str(x), fill=(80, 80, 80), font=f12, anchor='mt'); dr.line([P(x, Z0), P(x, Z1)], fill=(225, 225, 230))
for z in range(-76, -41, 4): dr.text((W + 4, P(0, z)[1]), str(z), fill=(80, 80, 80), font=f12, anchor='lm'); dr.line([P(X0, z), P(X1, z)], fill=(225, 225, 230))
dr.text((10, 12), 'pra_01 north half: standing spots for RMC v3 (neutral jump, then LEFT, then tornado)', fill=(20, 20, 30), font=f20)
dr.text((10, H + 52), 'x axis left-right, z up = north (toward the back wall), like the in-game camera. Mirror line (z 0) is below this view.', fill=(80, 80, 80), font=f12)
# legend
lx = W + 50; ly = 70
dr.text((lx, ly), 'Lightest LEFT tilt that clips', fill=(20, 20, 30), font=f16); ly += 30
for m, c in COL.items():
    dr.rectangle([lx, ly, lx + 22, ly + 22], fill=c); dr.text((lx + 32, ly + 3), 'tilt %d' % m, fill=(30, 30, 30), font=f14); ly += 32
dr.rectangle([lx, ly, lx + 22, ly + 22], fill=(200, 200, 205)); dr.text((lx + 32, ly + 3), 'can stand, never clips', fill=(30, 30, 30), font=f14); ly += 32
dr.text((lx, ly), 'blank = not tested (the tilt-20\nwalk steps ~2.1 units, so it never\nstopped in those columns)', fill=(30, 30, 30), font=f14); ly += 70
dr.text((lx, ly), 'Number in a cell = how many of\n30 (tilt x tornado frame) input\ncombos clip from that spot.', fill=(30, 30, 30), font=f14); ly += 80
dr.text((lx, ly), 'Inputs tested at each spot:\n- jump, A held 5, stick neutral\n  on frame 0\n- LEFT tilt 20/30/40/60/80\n  from frame 1\n- tornado on frame 6..11\n- then neutral 2nd jump and the\n  down-left 3rd jump\nReal inputs, JP, CountPerOp 1.', fill=(30, 30, 30), font=f14)
im.save('/home/user/HackMidwest/pm-kooper-bot/pra01_rmc_v3_standmap.png')
print(im.size, sum(1 for o in out if o[2]), 'working')
