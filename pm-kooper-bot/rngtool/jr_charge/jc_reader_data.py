"""Write the Charge reader's data for the Jr. Troopa fight (readouts/data/):
  charge_cams_mario_jr.json   per-frame gCameras[1] (perspective matrix + viewport) for frames 0..47 and the rays'
                              centre, same format as charge_cams_mario_route.json (charge_prep.py 'cams')
  charge_mario_ref_jr.json    Mario's patch at frame -1 (format of charge_live/mario_ref.json), EMULATOR render
  charge_jr_reader.json       the rest: centre on screen, nuisance draws, per-frame order, burst brightness curve,
                              the HUD-hide delay, and the turn draws a carried lock needs (jc_model.TURNS)
from jc_probe.py logs with screenshots of the T3 Charge (and the T1 / T5 / Hallway ones for the comparisons).
usage: python3 jc_reader_data.py T3LOG.json T3SHOTS T1LOG.json T1SHOTS T5LOG.json HWLOG.json HWSHOTS"""
import sys, os, json, base64, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, '..', 'readouts', 'data')
sys.path.insert(0, HERE)
import jc_model as JM
t3log, t3shots, t1log, t1shots, t5log, hwlog, hwshots = sys.argv[1:8]
def creation(L): return next(f for f, fr in enumerate(L) if any(x[0] == '0xe00d6160' for x in fr['calls']))
def cams(L):
    c = creation(L); cen = L[c]['fx'][min(L[c]['fx'], key=lambda a: int(a, 16))][0][1:4]
    return c, cen, [L[c + n]['cam'][:20] for n in range(48)]
def luma(fn):
    a = np.asarray(Image.open(fn).convert('RGB')).astype(np.int32)
    return ((77 * a[..., 0] + 150 * a[..., 1] + 29 * a[..., 2] + 128) >> 8).astype(np.uint8)
def bright(d, c):     # game-area mean (320-space x 23.5..299.2, y 39.5..220) above frames -6..-1
    m = lambda n: luma('%s/%04d.png' % (d, c + n + 1))[79:441, 47:599].astype(float).mean()
    b = np.mean([m(n) for n in range(-6, 0)]); return [round(m(n) - b, 1) for n in range(46)]
L3, L1, L5, LH = (json.load(open(f)) for f in (t3log, t1log, t5log, hwlog))
c3, cen, C3 = cams(L3); c1, cen1, C1 = cams(L1); c5, cen5, C5 = cams(L5); ch, cenh, CH = cams(LH)
route = json.load(open(os.path.join(DATA, 'charge_cams_mario_route.json')))
same = {'t1': C1 == C3 and cen1 == cen, 't5': C5 == C3 and cen5 == cen, 'hallway_emulator': CH == C3 and cenh == cen,
        'charge_cams_mario_route.json': route['cams'] == C3 and route['centre'] == cen}
print('camera tables identical to T3:', same)
json.dump({'centre': cen, 'cams': C3}, open(os.path.join(DATA, 'charge_cams_mario_jr.json'), 'w'))
# Mario patch: image after step c shows frame c-1 = frame -1
X0, Y0, W, H = 160, 236, 160, 120
P3 = luma('%s/%04d.png' % (t3shots, c3))[Y0:Y0 + H, X0:X0 + W]; P1 = luma('%s/%04d.png' % (t1shots, c1))[Y0:Y0 + H, X0:X0 + W]
M = np.array(C3[0][:16]).reshape(4, 4); vw, vh, vx, vy = C3[0][16:20]
v = np.array(cen + [1.0]) @ M; sx = vx + (v[0] / v[3] + 1) / 2 * vw; sy = vy + (1 - v[1] / v[3]) / 2 * vh
json.dump({'x0': X0, 'y0': Y0, 'w': W, 'h': H, 'b64': base64.b64encode(P3.tobytes()).decode(),
           'centre_world': cen, 'centre_raster': [round(2 * sx, 1), round(2 * sy, 1)],
           'note': 'Mario before the Charge (frame -1, 640x480 game raster luma) in the Jr. Troopa arena (battle 0x0207, Bombette): '
                   'EMULATOR render (Glide64), not a capture. T1 (10 HP) and T3 (2 HP) are byte-identical here, T5 differs by <= 24 '
                   'levels (NCC 1.00). For the centre offset (chgMarioShift); same box as charge_live/mario_ref.json.'},
          open(os.path.join(DATA, 'charge_mario_ref_jr.json'), 'w'))
print('Mario patch T1 == T3:', bool((P1 == P3).all()), 'centre raster', round(2 * sx, 1), round(2 * sy, 1))
bj, bh = bright(t3shots, c3), bright(hwshots, ch)
CHG_BRIGHT = [7.2, 12.5, 19.4, 28, 35.9, 42.1, 47.6, 49.2, 50.4, 53.9, 56.4, 56.9, 58.8, 61.2, 61.2, 61.7, 60.7, 62.1, 59.9, 57.1, 55.5, 50, 45.4,
              40.7, 29.8, 20.3, 14.7, 8.3, 3.4, 2.2, 4.2, 6.5, 7.3, 6.9, 6.8, 6.6, 6.5, 6.3, 6.2, 6, 6, 6, 5.9]
sug = [round(CHG_BRIGHT[n - 3] + bj[n] - bh[n], 1) for n in range(3, 46)]
# nuisance draws during the rays (frames 0..47), every Charge of the probe logs
oth = {}
for L in (L3, L1, L5):
    c = creation(L)
    for f in range(c, c + 49):
        for a, mx, val in L[f]['calls']:
            if not (a.startswith('0xe00d6') or a in ('0x80146d54', '0x800269ac')): oth[a] = oth.get(a, 0) + 1
doc = {
    'fight': 'Jr. Troopa (final, battle 0x0207), Mario Super Charge, Bombette out; T1 (10 HP), T3 / T5 (2 HP, Danger)',
    'frame0': 'Charge confirm (A on the target screen, hand on Mario) + 13: first energy_in_out(6) creation; second on frame 3',
    'hud_hide_frames_after_confirm': 3,
    'centre_world': cen, 'centre_raster_640x480': [round(2 * sx, 1), round(2 * sy, 1)],
    'camera': 'identical to readouts/data/charge_cams_mario_route.json (Hallway Bowser) on all 48 frames: %s' % same,
    'nuisance_draws_during_rays': oth or 'none',
    'per_frame_order': ['battle script: energy_in_out creation (rand(360), then 10 x [rand(10) speed, rand(10) phase])',
                        'status-bar coin rand(100) (24 frames, 48 after a roll >= 70)',
                        'energy_in_out updates in creation order (part counter wraps -> rand(359))', 'per-frame rand_int(1)'],
    'burst_brightness_emulator': {'jr_t3': bj, 'hallway_t1': bh, 'frames': '0..45, game area mean above frames -6..-1'},
    'CHG_BRIGHT_jr_suggested': {'frames': '3..45', 'values': sug,
                                'how': 'page CHG_BRIGHT (real Hallway captures) + (emulator Jr - emulator Hallway); unverified on a capture'},
    'turn_draws': {k: {kk: ({str(o): v for o, v in vv.items()} if isinstance(vv, dict) else vv) for kk, vv in t.items()} for k, t in JM.TURNS.items()},
    'turn_draws_note': 'offsets from each confirm (A frame); pre = before the coin on that frame, post = after; (100, name) = a roll. '
                       'Popup A after the Charge: no draws; it only moves the partner menu to A+16 (A on +77..+136; none = +153).',
}
json.dump(doc, open(os.path.join(DATA, 'charge_jr_reader.json'), 'w'), indent=1, default=list)
print('nuisance', oth or 'none'); print('max |jr - hallway| brightness', max(abs(a - b) for a, b in zip(bj, bh)))
