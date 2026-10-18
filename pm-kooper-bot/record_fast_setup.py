"""FAST variant (record_fast_setup.py): rock part with 1-frame gaps (fast_setup.rock_part), the fast arc
(states/arc_TAG.json from rev_aim_explore_fast.py) and the fastest top-wall push (states/wall_TAG.json from
fast_wall.py: aim, go G, stop S, wait), no standing around.
Based on: one continuous run of the whole reverse mirror clip setup from states/pra01_top_rock.st, with the same inputs (and
the same extra neutral frame at every saved-state boundary) as the stage scripts:
 1 walk at PA degrees for PRE frames, wait 60, jump left (stick R frames), wait 60 (make_setup_left.py)
 2 wiggle on the rock until the history ring is full, wait 10, hop right (stick H frames), wait 21
 3 the push arc (states/arc_TAG.json, aimed at Laki) into the lower corner (save_corners.py)
 4 ledge plan + aimed stop-and-go push along the top wall until Laki x >= 983, wait 30 (make_topright_from_corner.py)
 5 the hold-up ending (rta_holdup2.route with A + down N), stopping hammer B+up on frame h, hold up, C-down on frame c
SHOT=1 screenshots every frame (video plugin + DISPLAY); writes OUT/log.json for make_video.py.
usage: record_full_setup.py OUT TAG [N h c]   (h, c count frames from the top-right state, as in rta_holdup2.py)"""
import json, math, os, subprocess, sys
from rta_holdup2 import *
from fast_setup import rock_part, rock_part2
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT, TAG = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
N, h, c = (int(a) for a in sys.argv[3:6]) if len(sys.argv) > 5 else (31, 97, 132)
PA, PRE, R, H = 160, 10, 12, 8
arc = json.load(open('states/arc_%s.json' % TAG)); led = json.load(open('states/wall_%s.json' % TAG))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rfs')
log = []
def st(b, s, tag=''):
    e.step(b, *s, 2)
    p, l = player(e), laki(e); ptr = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'act': p['action']})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
def show(t):
    p, l = player(e), laki(e); ptr = e.u32(PTR)
    print('%-10s frame %4d  M (%.1f, %.1f, %.1f)  L (%.1f, %.1f, %.1f)  state %d ptr %d target (%.1f, %.1f)' % (t, len(log), p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)), flush=True)
def jump(stick, hold, tag, maxf=30):
    for i in range(maxf):
        st(0x80 if i < 8 else 0, stick if i < hold else (0, 0), tag)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
e.load('states/pra01_top_rock.st'); st(0, (0, 0), 'start: Mario by the small rock, Laki idle on his right')
(rock_part2 if os.environ.get('V2') else rock_part)(e, st)
show('fill')
st(0, (0, 0), 'push Laki along the arc')
for g, th, sl in arc:
    p, l = player(e), laki(e)
    s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
    for i in range(g): st(0, s, 'stop-and-go push aimed at Laki: the arc')
    for i in range(sl): st(0, (0, 0), 'stop-and-go push aimed at Laki: the arc')
show('arc')
st(0, (0, 0), 'lower corner reached')
U, jumps, _ = led['plan']
for i in range(U): st(0, stick_for(270, 80), 'up to the top wall')
for W, Hh, D in jumps:
    s = stick_for(D, 80)
    for i in range(W): st(0, s, 'ledge: jump at %d deg' % D)
    jump(s, Hh, 'ledge: jump at %d deg' % D, 24)
    for i in range(3): st(0, (0, 0), 'ledge')
show('ledge')
for k in range(200):
    p, l = player(e), laki(e)
    s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + led['aim']) % 360, 80)
    for i in range(led['G']): st(0, s, 'push Laki along the top wall (stick %d frames, release %d)' % (led['G'], led['S']))
    for i in range(led['S']): st(0, (0, 0), 'push Laki along the top wall (stick %d frames, release %d)' % (led['G'], led['S']))
    p, l = player(e), laki(e)
    if l['x'] >= 983 or p['x'] > l['x'] + 5: break
for i in range(led['wait']): st(0, (0, 0), 'palace corner')
st(0, (0, 0), 'palace corner: Laki pinned at the wall, stale target intact')
show('top-right')
t0 = len(log)
st(0, (0, 0), 'ending: hold up, right into the corner')
fr = [0]
def st2(b, s, tag=''): st(b, s, tag); fr[0] += 1
if os.environ.get('ENDING') == 'W':
    # release-and-wait ending (rta_wide.py family W): args N = A + down, h = left frames T after the step-3 landing,
    # c = frames standing before up (U); C-down on frame CDABS (default 136) of the ending
    T, U = h, c
    for i in range(10): st2(0, U_, 'ending: hold up')
    for i in range(10): st2(0, SD['R'], 'hold right: very top-right corner')
    st2(B, SD['D'], 'hammer (B) with down held')
    for i in range(13): st2(0, SD['D'], 'hold down')
    for i in range(N): st2(0x80 if i < 12 else 0, SD['D'], 'A + hold down (%d frames): jump onto the top step, walk down' % N)
    st2(0, (0, 0), 'release')
    while player(e)['action'] != 9: st2(0, SD['L'], 'hold left')
    for i in range(8): st2(0, (0, 0), 'release during the forced drop: lands on step 3')
    for i in range(T): st2(0, SD['L'], 'left %d frames: Mario at x 889.2' % T)
    for i in range(1 + U): st2(0, (0, 0), 'release, stand %d frame(s)' % (1 + U))
    while fr[0] < int(os.environ.get('CDABS', 136)): st2(0, U_, 'hold up: into the wall, slide down onto step 2; wait for Laki to turn around')
    st2(CD, U_, 'C-down (still holding up) on the spike frame: Laki speed %.2f')
else:
    route(e, N, st2)
    while fr[0] < h: st2(0, SD['L'], 'hold left: off the top step onto step 3, keep running')
    st2(B, U_, 'hammer (B) with up held: Mario stops at x 889.2 on step 3')
    for i in range(9): st2(0, U_, 'hammer swing, holding up')
    while fr[0] < c: st2(0, U_, 'hold up: into the wall, slide down onto step 2; wait for Laki to turn around')
    st2(CD, U_, 'C-down (still holding up) on the spike frame: Laki speed %.2f')
log[-1]['tag'] = log[-1]['tag'] % log[-1]['ls']
ok = log[-1]['ls'] >= 115.75
for i in range(70): st(0, U_ if i < 3 else (0, 0), 'mount -> FRONT side of the mirror' if ok else 'mount: not enough speed')
show('end')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), 'frames; C-down speed %.2f' % [l['ls'] for l in log if l['tag'].startswith('C-down')][0])
