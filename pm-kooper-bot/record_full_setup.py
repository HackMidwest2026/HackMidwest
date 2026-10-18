"""One continuous run of the whole reverse mirror clip setup from states/pra01_top_rock.st, with the same inputs (and
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
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT, TAG = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
N, h, c = (int(a) for a in sys.argv[3:6]) if len(sys.argv) > 5 else (31, 97, 132)
PA, PRE, R, H = 160, 10, 12, 8
arc = json.load(open('states/arc_%s.json' % TAG)); led = json.load(open('states/ledge_%s.json' % TAG))
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
for i in range(PRE): st(0, stick_for(PA, 80), 'walk left (angled down 20 deg) %d frames: Laki follows' % PRE)
for i in range(60): st(0, (0, 0), 'wait: Laki goes idle further left (stale target moves to x 555)')
jump(stick_for(180, 80), R, 'jump left onto the rock')
for i in range(60): st(0, (0, 0), 'stand on the rock')
show('rock')
up, dn = stick_for(270, 30), stick_for(90, 30)
for f in range(120):
    if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
    st(0, up if f % 2 == 0 else dn, "wiggle on the rock: fill Laki's history (old points on the rock)")
for i in range(10): st(0, (0, 0), 'history full')
jump(stick_for(0, 80), H, 'hop down to the right, next to Laki')
for i in range(21): st(0, (0, 0), 'ready to push (Laki idle, stale target intact)')
show('fill')
st(0, (0, 0), 'ready to push (Laki idle, stale target intact)')
for g, th, sl in arc:
    p, l = player(e), laki(e)
    s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
    for i in range(g): st(0, s, 'stop-and-go push aimed at Laki: the arc')
    for i in range(sl): st(0, (0, 0), 'stop-and-go push aimed at Laki: the arc')
show('arc')
st(0, (0, 0), 'lower corner reached')
U, jumps, G = led['plan']
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
    for i in range(G): st(0, s, 'stop-and-go push aimed at Laki along the top wall')
    for i in range(2): st(0, (0, 0), 'stop-and-go push aimed at Laki along the top wall')
    p, l = player(e), laki(e)
    if l['x'] >= 983 or p['x'] > l['x'] + 5: break
for i in range(30): st(0, (0, 0), 'palace corner: Laki pinned at the wall, stale target intact')
st(0, (0, 0), 'palace corner: Laki pinned at the wall, stale target intact')
show('top-right')
t0 = len(log)
st(0, (0, 0), 'ending: hold up, right into the corner')
fr = [0]
def st2(b, s, tag=''): st(b, s, tag); fr[0] += 1
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
