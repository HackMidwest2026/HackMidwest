"""Write the Charge reader's data for the Duplighost fight (battle 0x2402, stage kpa_01) into readouts/data/:
  charge_cams_mario_dup.json   per-frame gCameras[1] (perspective matrix + viewport) for frames 0..47 and the rays'
                               centre, the format of charge_cams_mario_route.json / _jr.json
  charge_mario_ref_dup.json    Mario's patch at frame -1, the format of charge_mario_ref_jr.json (EMULATOR render)
  charge_dup_reader.json       centre on screen, nuisance draws during the rays, per-frame order, burst brightness
                               (this arena vs the Hallway, both emulator), suggested CHG_BRIGHT, HUD-hide delay, the
                               turn draws a carried lock needs (dc_model)
from ../jr_charge/jc_probe.py logs with Glide64 screenshots of a T1 Charge here (two seeds) and of the Hallway T1.
usage: python3 dc_reader_data.py DUPLOG DUPSHOTS DUPLOG2 DUPSHOTS2 HWLOG HWSHOTS"""
import sys, os, json, base64, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, '..', 'readouts', 'data')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jr_charge'))
import dc_model as DM
from jc_mario_ref import shift
dlog, dshots, dlog2, dshots2, hwlog, hwshots = sys.argv[1:7]
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
LD, LD2, LH = (json.load(open(f)) for f in (dlog, dlog2, hwlog))
cd, cen, CD = cams(LD); cd2, cen2, CD2 = cams(LD2); ch, cenh, CH = cams(LH)
route = json.load(open(os.path.join(DATA, 'charge_cams_mario_route.json')))
jr = json.load(open(os.path.join(DATA, 'charge_cams_mario_jr.json')))
maxdiff = lambda A, B: max(abs(a - b) for ra, rb in zip(A, B) for a, b in zip(ra, rb))
same = {'second_seed': CD2 == CD and cen2 == cen, 'hallway_emulator': CH == CD and cenh == cen,
        'charge_cams_mario_route.json': route['cams'] == CD and route['centre'] == cen,
        'charge_cams_mario_jr.json': jr['cams'] == CD and jr['centre'] == cen}
diffs = {'route_max_abs': maxdiff(route['cams'], CD), 'jr_max_abs': maxdiff(jr['cams'], CD), 'hallway_emulator_max_abs': maxdiff(CH, CD)}
print('camera table identical:', same, diffs, 'centre', cen)
json.dump({'centre': cen, 'cams': CD}, open(os.path.join(DATA, 'charge_cams_mario_dup.json'), 'w'))
# Mario patch: the image after step c shows frame c-1 = frame -1
X0, Y0, W, H = 160, 236, 160, 120
FD, FD2, FH = luma('%s/%04d.png' % (dshots, cd)), luma('%s/%04d.png' % (dshots2, cd2)), luma('%s/%04d.png' % (hwshots, ch))
P = FD[Y0:Y0 + H, X0:X0 + W]
M = np.array(CD[0][:16]).reshape(4, 4); vw, vh, vx, vy = CD[0][16:20]
v = np.array(cen + [1.0]) @ M; sx = vx + (v[0] / v[3] + 1) / 2 * vw; sy = vy + (1 - v[1] / v[3]) / 2 * vh
hwref = json.load(open(os.path.join(HERE, '..', 'charge_live', 'mario_ref.json')))
HR = np.frombuffer(base64.b64decode(hwref['b64']), np.uint8).reshape(hwref['h'], hwref['w'])
xs = {'dup_patch_on_dup_seed2': shift(P, FD2), 'dup_patch_on_hallway_emulator': shift(P, FH),
      'hallway_capture_patch_on_dup': shift(HR, FD), 'hallway_capture_patch_on_hallway_emulator': shift(HR, FH)}
print('Mario patch (dx, dy, ncc):', xs, 'seed2 identical:', bool((FD2[Y0:Y0 + H, X0:X0 + W] == P).all()))
json.dump({'x0': X0, 'y0': Y0, 'w': W, 'h': H, 'b64': base64.b64encode(P.tobytes()).decode(),
           'centre_world': cen, 'centre_raster': [round(2 * sx, 1), round(2 * sy, 1)],
           'note': 'Mario before the Charge (frame -1, 640x480 game raster luma) in the Duplighost arena (battle 0x2402, stage kpa_01, '
                   'Bombette out, T1, 10 HP): EMULATOR render (Glide64), not a capture. For the centre offset (chgMarioShift); same box '
                   'as charge_live/mario_ref.json. Cross-scores (dx, dy, ncc): %s' % xs},
          open(os.path.join(DATA, 'charge_mario_ref_dup.json'), 'w'))
bd, bd2, bh = bright(dshots, cd), bright(dshots2, cd2), bright(hwshots, ch)
CHG_BRIGHT = [7.2, 12.5, 19.4, 28, 35.9, 42.1, 47.6, 49.2, 50.4, 53.9, 56.4, 56.9, 58.8, 61.2, 61.2, 61.7, 60.7, 62.1, 59.9, 57.1, 55.5, 50, 45.4,
              40.7, 29.8, 20.3, 14.7, 8.3, 3.4, 2.2, 4.2, 6.5, 7.3, 6.9, 6.8, 6.6, 6.5, 6.3, 6.2, 6, 6, 6, 5.9]   # page curve, frames 3..45
sug = [round(CHG_BRIGHT[n - 3] + bd[n] - bh[n], 1) for n in range(3, 46)]
oth = {}; per = []
for L in (LD, LD2):
    c = creation(L)
    for f in range(c, c + 49):
        for a, mx, val in L[f]['calls']:
            if not (a.startswith('0xe00d6') or a in ('0x80146d54', '0x800269ac')): oth[a] = oth.get(a, 0) + 1
hud = []
for L in (LD, LD2):
    c = creation(L); conf = next(f for f in range(c - 1, -1, -1) if L[f]['in'][0])
    hud.append(c - conf)
doc = {
    'fight': 'Duplighosts x4 (battle 0x2402, kpa3 formation 2, stage kpa_01), Mario Super Charge on T1 (Mario acts first), Bombette (Super) out, 10 HP',
    'frame0': 'Charge confirm (A on the target screen, hand on Mario) + 13: first energy_in_out(6) creation; second on frame 3 (checked: creation at confirm +%s in the probe runs)' % hud,
    'hud_hide_frames_after_confirm': 3,
    'centre_world': cen, 'centre_raster_640x480': [round(2 * sx, 1), round(2 * sy, 1)],
    'camera': 'identical to charge_cams_mario_route.json (Hallway) on all 48 frames: %s; max abs differences %s' % (same, diffs),
    'nuisance_draws_during_rays': oth or 'none',
    'per_frame_order': ['battle script: energy_in_out creation (rand(360), then 10 x [rand(10) speed, rand(10) phase])',
                        'status-bar coin rand(100) (24 frames, 48 after a roll >= 70)',
                        'energy_in_out updates in creation order (part counter wraps -> rand(359))', 'per-frame rand_int(1)'],
    'burst_brightness_emulator': {'dup_seed1': bd, 'dup_seed2': bd2, 'hallway_t1': bh, 'frames': '0..45, game area mean above frames -6..-1',
                                  'max_abs_dup_minus_hallway': round(max(abs(a - b) for a, b in zip(bd, bh)), 1)},
    'CHG_BRIGHT_dup_suggested': {'frames': '3..45', 'values': sug,
                                 'how': 'page CHG_BRIGHT (real Hallway captures) + (emulator Duplighost - emulator Hallway); unverified on a capture'},
    'mario_patch_cross_scores': xs,
    'turn_draws': {'charge': {'eio': [[13, 58], [16, 61]]},
                   'popup_A': 'no draws; the partner menu opens at A+16 (A on +77..+136; no A: +153)',
                   'menus': 'no draws (Bombette wheel, Strategies list)',
                   'do_nothing': 'copy rolls RandInt(1000) < 600: first at +%d; a copy -> next +%d; a failed copy (flying tackle, 4 damage) -> '
                                 '8 x rand(359) at +%d, next roll +%d; all script draws, before the coin' % (DM.ROLL0, DM.COPY_NEXT, DM.FAIL_FX, DM.FAIL_NEXT),
                   'close_call': 'rand(100) when a tackle hits Mario under 6 HP: from 10 HP only on a 3rd failed copy'},
}
json.dump(doc, open(os.path.join(DATA, 'charge_dup_reader.json'), 'w'), indent=1, default=list)
print('nuisance', oth or 'none', '| creation - confirm', hud, '| max |dup - hallway| brightness', doc['burst_brightness_emulator']['max_abs_dup_minus_hallway'])
print('suggested', sug)
