"""FB2 route T6 -> T7 RNG model (JP): from a seed locked after the T6 Super Charge rays to Bowser's T6 attack choice,
the Close Call roll and the T7 Power Bounce rolls. Frame numbers are relative to the T6 Charge confirm (frame 0).

Measured in the emulator (t6_collect.py, t6_check.py):
- the Charge rays draw on frames 13..60 only (charge_model.py covers them); from frame 61 on the only per-frame draws are
  the lightning bolts, the status-bar coin and the step until Bowser's turn;
- the "Jump power +3" popup after the Charge is dismissed by A on frame K (K = 77 at the earliest; with no press it
  closes on its own like K = 137). Bowser's AI runs on frame E = K + 40:
  RandInt(100) (Star Rod re-cast; T6 is 2 turns after the beam, so the chance is 0 but the draw is made),
  RandInt(80) (< 20 and Body Slam allowed -> Body Slam), else RandInt(60) (< 20 and Claw allowed -> Claw), else Fire Breath;
- the target test on Mario on frame E + DELTA[attack]: Close Call rand_int(100) < 30 = Lucky (Mario is at Danger, no Cloud
  Nine, Lakilester KO'd);
- T7 menu opens on E + DELTA + MENU[attack] (Lucky branch); the Power Bounce target-screen A on frame d (absolute);
  rolls as powerbounce/fb2model.py (stars at d+45+27k, roll k at d+71+27(k-1)).
Same-frame order: bolts, then the script draws (AI / target test / bounce), then the coin, then the step.
usage (self-test against collected logs): t6model.py LOG.json [...]"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'powerbounce'))
from fb2model import adv, rand_int, TH, nstars

DELTA = {'slam': 52, 'claw': 62, 'fire': 55}      # target-test frame after the AI frame
MENU = {'slam': 101, 'claw': 83, 'fire': 134}      # Lucky branch: T7 menu opens this many frames after the test
KMIN, KMAX = 77, 137                                 # popup-dismiss window (A on confirm + K)
P130 = (78, 83, 113, 118); P220 = (18, 78, 88, 178)


def bolt_frames(p130, p220, f0, f1):
    """frames f in [f0, f1) with a bolt draw (count per frame) for lightning phases p130, p220 (frame f has a 130-loop
    bolt when (f + p130) % 130 in P130, etc.)"""
    out = {}
    for f in range(f0, f1):
        n = ((f + p130) % 130 in P130) + ((f + p220) % 220 in P220)
        if n: out[f] = n
    return out


def sim(seed, f0, K, d, bolts, coin_next, slam_ok=True, claw_ok=True, dmg0=15, kmax=14, bowser_hp=None):
    """seed = gRandSeed at the start of frame f0 (>= 61). bolts: {frame: count}. coin_next: frame of the next coin draw.
    Returns dict(attack, cc, lucky, menu, rolls, bounces). d None -> stop after the Close Call."""
    if K < KMIN or K > KMAX: K = KMAX                     # no press in the window: the popup closes by itself
    s = seed; nc = coin_next; E = K + 40; atk = None; T = None; res = dict(attack=None, cc=None, lucky=None, menu=None,
                                                                            rolls=[], bounces=0)
    k = 0; hit = 0; dmg_total = 0
    end = (d + 71 + 27 * kmax) if d is not None else E + 70
    for f in range(f0, end):
        for i in range(bolts.get(f, 0)): s, _ = rand_int(s, 359)
        if f == E:
            s, _ = rand_int(s, 100); s, v80 = rand_int(s, 80)
            if v80 < 20 and slam_ok: atk = 'slam'
            else:
                s, v60 = rand_int(s, 60); atk = 'claw' if (v60 < 20 and claw_ok) else 'fire'
            res['attack'] = atk; T = E + DELTA[atk]
        if T is not None and f == T:
            s, v = rand_int(s, 100); res['cc'] = v; res['lucky'] = v < 30; res['menu'] = T + MENU[atk]
            if not res['lucky'] or d is None: return res
        if d is not None and res['lucky']:
            if f == d + 71 + 27 * k and k == hit - 1:
                s, v = rand_int(s, 100); res['rolls'].append((f - d, v))
                if v > TH[k]: res['bounces'] = k + 2; return res
                k += 1
            if f == d + 45 + 27 * hit:
                dm = max(1, dmg0 - hit)
                for i in range(nstars(dm)): s, _ = rand_int(s, 359)
                hit += 1; dmg_total += dm
                if bowser_hp is not None and dmg_total >= bowser_hp: res['bounces'] = hit; return res
        if f == nc:
            s, v = rand_int(s, 100); nc += 48 if v >= 70 else 24
        s = adv(s)
    res['bounces'] = k + 2 if d is not None else 0
    return res
