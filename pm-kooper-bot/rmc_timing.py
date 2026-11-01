"""Time the three reverse mirror clip methods against each other (real inputs only, CountPerOp 1, JP ROM).
Start: states/pra02_topdoor_closed.st = the first frame on which pra_02's top (back-wall) door is fully closed after
       entering from pra_04 (Speedy Spin + Ultra Boots equipped, Lakilester out).
End:   the frame of the A press that opens pra_02's bottom (front-wall) door (the map change is queued 18 frames later).
Every route uses Speedy Spin dashes (Z) for movement, cancelled with a jump (A) near the target.
The three methods are Laki inside (v1/v2, two input variants of the same pra_02 clip), Laki outside (lo) and Ultra
Boots outside (v3).
  v1  Laki inside, frame-perfect hops: corner setup, push Laki to the right wall, run 10, A5 hops, C-down on f37.
  v2  Laki inside, RTA hops: same setup, push stops at Laki x>930, full jump f3, 4 floor frames, A5 hop.
  lo  Laki outside (pra_01 reflected side): rock-jump stale-target setup, arc push, ledge, top-wall push, hold-up
      ending, ride to pra_01's south door -> pra_02 lower west door -> bottom door.
  v3  Ultra Boots outside, pra_01 climb: west upper door -> pra_01 north, neutral climb, land on the near-cave floor (sam_10
      loads), walk straight back into pra_01 (south side, entry 0), pra_01 south door -> pra_02 lower west door,
      bottom door.
Each route is searched with savestates (door A frames, push loop), then the recorded inputs are replayed from the
start state in one continuous run with no savestate loads, and that replay is what is reported.
usage: rmc_timing.py [v1 v2 v3 lo]"""
import sys, json
import rmc_tim as tim
from rmc_tim import *
from rmc_clipseq import *

def common_setup(t):
    go_fast(t, 130, -80, 60, 60, 3)                      # spin to the back-left area
    for i in range(25): t.step(0, -56, 56)                # UP-LEFT into the corner: Laki ends facing 315
    l = BC.laki(); t.go(l['x'] - 4, l['z'], 80, 0.3)      # line up 4 units behind Laki

def finish_front(t, marks, ride_k, tx, rc, far, stopd):
    for i in range(16): t.step()                          # mount ride (stick ignored until here)
    ride(t, tx, 230, ride_k); dismount(t)                 # ride Laki toward the door, then B to get off
    marks['dismounted (walking)'] = t.n
    return to_door(t, tx, 230, (0, -80), rc, far, stopd)  # spin to the door, hold DOWN, A

def v1(t):
    marks = {}
    common_setup(t); marks['lined up behind Laki'] = t.n
    push(t, stop=975); marks['push done (Laki at right wall)'] = t.n; t.step()
    jt = None; tgt = (850, -75)
    for f in range(38):
        p = player(t.e); grounded = p['action'] in (0, 1, 2)
        dx, dz = tgt[0] - p['x'], tgt[1] - p['z']; d = math.hypot(dx, dz)
        stick = (0, 0) if (p['y'] > 14 and grounded) or d < 3 else (int(80 * dx / d), int(-80 * dz / d))
        b = 0
        if f >= 10 and not (grounded and p['y'] > 14):
            if jt is None and grounded: jt = 0
            if jt is not None:
                b = A if jt < 5 else 0; jt += 1
                if jt > 4 and grounded: jt = None
        if f == 37: b = D_CBUTTON
        t.step(b, *stick)
    marks['C-down'] = t.n
    return marks, finish_front(t, marks, 8, 500, 90, 60, 60)

def v2(t):
    tim.CHAIN = 21                                       # 1-frame jump out of every spin on spin frame 21
    marks = {}
    common_setup(t); marks['lined up behind Laki'] = t.n
    push(t, stop=930); marks['push done (Laki x>930)'] = t.n
    marks['C-down'] = v2_finish(t, 3, 55, 4)
    return marks, finish_front(t, marks, 7, 500, 90, 60, 30)

def v3(t):
    tim.CHAIN = 21
    e = t.e
    marks = {}
    af, mc = to_door(t, 0, -75, (-80, 0), 90, 60, 25)    # pra_02 west upper door -> pra_01 north (entry 2)
    marks['west upper door A'] = af
    go_fast(t, 550, -60, 60, 60, 0.5)                     # spot in front of the star piece cave
    marks['at climb start spot'] = t.n
    marks['south landing (sam_10 queued)'] = v3_climb(t, 8)
    for i in range(200):                                  # sam_10: hold RIGHT straight back into pra_01
        t.step(0, 80, 0)
        if where(e)[:2] == (21, 0) and abs(player(e)['z'] - 105) < 1 and player(e)['y'] < -50: break
    marks['back in pra_01 south side'] = t.n
    af, mc = to_door(t, 1000, 60, (80, 0), 20, 60, 30)   # pra_01 south door -> pra_02 lower west door
    marks['pra_01 south door A'] = af
    return marks, to_door(t, 520, 230, (0, -80), 90, 60, 60)

def lo(t):
    """Laki outside (pra_01 reflected side): west upper door, rock-jump stale-target setup, guided arc push into the
    lower corner, two ledge jumps, top-wall push to the palace wall, hold-up ending, ride + B, pra_01 south door."""
    import rmc_lo_route as lo_route, rmc_lo_end as lo_end
    tim.CHAIN = None                                     # the setup depends on the plain spins' exact positions
    marks = {}
    af, mc = to_door(t, 0, -75, (-80, 0), 90, 60, 25)    # pra_02 west upper door -> pra_01 north (entry 2)
    marks['west upper door A'] = af
    lo_route.to_rock(t, 600, 565, 0)                      # spin along the mirror, walk left, rock jump, fill, hop
    marks['rock setup done'] = t.n
    lo_route.arc(t, json.load(open('data/rmc_lo_arc.json')))
    marks['Laki in lower corner'] = t.n
    lo_route.ledge_wall(t, json.load(open('data/rmc_lo_wall.json')))
    marks['Laki pinned at palace wall'] = t.n
    t.step(); lo_end.replay(t, 32, 646, 685)              # hold-up ending: A+down 32, stopping hammer, C-down
    marks['C-down'] = t.n
    tim.CHAIN = 21                                       # after the clip: chained spin-jumps
    for i in range(16): t.step()
    ride(t, 1000, 60, 8); dismount(t)
    af, mc = to_door(t, 1000, 60, (80, 0), 90, 60, 30)   # pra_01 south door -> pra_02 lower west door
    marks['pra_01 south door A'] = af
    return marks, to_door(t, 520, 230, (0, -80), 90, 60, 60)

def replay(e, log, n_end):
    """continuous replay from START with no loads; returns frames where the queued map changes."""
    e.load(START); prev = where(e)[:2]; ch = []
    for n in range(1, n_end + 1):
        b, x, y = log[n]; e.step(b, x, y, 2)
        w = where(e)[:2]
        if w != prev: ch.append((n, w)); prev = w
    return ch

if __name__ == '__main__':
    names = sys.argv[1:] or ['v2', 'lo', 'v3']
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/rmct'); out = {}
    for nm in names:
        t = T(e); t.start()
        marks, (af, mc) = globals()[nm](t)
        log = {n: t.log[n] for n in range(1, mc + 1)}
        ch = replay(e, log, mc)
        ok = ch and ch[-1] == (mc, (21, 1)) or (ch and ch[-1][0] == mc)
        print('%s: bottom door A on frame %d = %.2f s  (map change queued %d)  marks %s' % (nm, af, af / 30, mc, marks))
        print('    continuous replay map changes: %s -> %s' % (ch, 'MATCH' if ch and ch[-1][0] == mc else 'MISMATCH'))
        out[nm] = {'door_A_frame': af, 'map_change': mc, 'marks': marks, 'replay_changes': ch, 'inputs': [log[n] for n in range(1, mc + 1)]}
    json.dump(out, open('/dev/shm/pmbot/rmc_timing_%s.json' % '_'.join(names), 'w'))
