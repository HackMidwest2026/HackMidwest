"""Record a kpa_62 cardinal-only setup run for a video. Mario is placed with Laki settled (kpa62_place), then the
program runs: segments 'dir:frames' or 'wait:frames' (neutral), 'Z:dir:k' (spin, dir held k frames) or
'A:dir:a:d' (jump: A held a frames, dir held d frames, 45 frames total), 'mount[:n]' (C-down + n frames, default 40), 'try:T[:label]' (a missed
attempt: mount, ride 40, B, hold down, C-down on frame T (T=99: none), let go after the moment passes),
'miss:T' (a missed C-down on frame T, then hands off), 'B' (dismount), 'recover' (B if riding; if Mario is on the y-50 ledge, jump back up holding up), or
'hDIR:k' (half-tilt hold, for riding Laki at walking speed), then (unless already riding) mount (C-down), ride RIDE frames, B, hold down,
C-down on frame T after the B, hold down 30 more, stand 40. SHOT=1 screenshots every frame (Xvfb :99 + video plugin).
Writes OUT/log.json with per-frame tag, input, Mario/Laki state.
env START=x,z[,y] (default -480,-100,60), HOLD (direction held after B, default down)
usage: record_kpa62_setup.py STATE OUT 'up:120 wait:10 right:30 wait:20 left:12 wait:20 down:12 wait:40' [T=34] [RIDE=40]"""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_place import place
from kpa62_tower import inside_tower
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80), 'wait': (0, 0)}
CARD.update({'h' + d: stick_for(a, 45) for d, a in (('right', 0), ('down', 90), ('left', 180), ('up', 270))})
riding = False
st0, OUT, PROG = sys.argv[1], sys.argv[2], sys.argv[3]
T = int(sys.argv[4]) if len(sys.argv) > 4 else 34; RIDE = int(sys.argv[5]) if len(sys.argv) > 5 else 40
os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rks%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
log = []
def st(b, s, tag, inp):
    e.step(b, *s, 2)
    p, l = player(e), laki()
    log.append({'i': len(log), 'tag': tag, 'inp': inp, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'act': p['action'],
                'lx': l['x'], 'ly': l['y'], 'lz': l['z'], 'ls': l['speed'], 'st': e.u16(0x8010D188), 'in': inside_tower(p['x'], p['z'])})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
_s = [float(v) for v in os.environ.get('START', '-480,-100,60').split(',')]
e.load(st0); e.step(0, 0, 0, 2); place(e, _s[0], _s[1], y=_s[2] if len(_s) > 2 else 60.0)
for seg in PROG.split():
    f = seg.split(':')
    if f[0] == 'try':
        TT = int(f[1]); what = ('C-down on frame %d (should be 34)' % TT) if TT < 99 else 'no C-down'
        if len(f) > 2: what = f[2].replace('_', ' ')
        st(0x400, (0, 0), 'C-down: mount Laki', 'C-DOWN')
        for i in range(40): st(0, (0, 0), 'ride Laki', '')
        st(0x40, (0, 0), 'B: dismount (frame 0)', 'B  (frame 0)')
        for fr in range(1, 46):
            held = CARD['down'] if fr <= max(34, min(TT, 36)) else (0, 0)
            st(0x400 if fr == TT else 0, held, 'MISTAKE: ' + what, ('C-DOWN  frame %d' % fr) if fr == TT else ('DOWN  frame %d' % fr if held != (0, 0) else ''))
        for i in range(45): st(0, CARD['down'] if TT <= 36 else (0, 0), 'MISTAKE: ' + what + ' - no clip', '')
        continue
    if f[0] == 'miss':
        TT = int(f[1])
        st(0x400, (0, 0), 'C-down: mount Laki', 'C-DOWN')
        for i in range(40): st(0, (0, 0), 'ride Laki', '')
        st(0x40, (0, 0), 'B: dismount (frame 0)', 'B  (frame 0)')
        for fr in range(1, TT): st(0, CARD['down'], 'MISTAKE: C-down on frame %d (should be 34)' % TT, 'DOWN  frame %d' % fr)
        st(0x400, CARD['down'], 'MISTAKE: C-down on frame %d (should be 34)' % TT, 'C-DOWN + DOWN  frame %d' % TT)
        for i in range(120): st(0, (0, 0), 'MISTAKE: hands off, Mario is still riding Laki', '')
        riding = True
        continue
    if f[0] == 'B':
        st(0x40, (0, 0), 'BACKUP: B to get off Laki in the corner', 'B')
        for i in range(40): st(0, (0, 0), 'stand', '')
        riding = False
        continue
    if f[0] == 'recover':
        if player(e)['action'] == 33:
            st(0x40, (0, 0), 'RECOVER: B to get off Laki', 'B')
            for i in range(40): st(0, (0, 0), 'RECOVER: B to get off Laki', '')
        if player(e)['y'] < 58:
            for i in range(50): st(0x80 if i < 25 else 0, CARD['up'], 'RECOVER: jump back up holding UP', 'A + UP' if i < 25 else 'UP')
            for i in range(15): st(0, (0, 0), 'stand', '')
        continue
    if f[0] == 'mount':
        st(0x400, (0, 0), 'C-down: mount Laki', 'C-DOWN')
        for i in range(int(f[1]) if len(f) > 1 else 40): st(0, (0, 0), 'ride Laki', '')
        riding = True
        continue
    if f[0] == 'Z':
        k = int(f[2])
        for i in range(k): st(0x20 if i == 0 else 0, CARD[f[1]], 'spin (Z) holding %s %d frames' % (f[1].upper(), k), ('Z + ' if i == 0 else '') + '%s %d/%d' % (f[1].upper(), i + 1, k))
        continue
    if f[0] == 'A':
        a, dd = int(f[2]), int(f[3])
        for i in range(45): st(0x80 if i < a else 0, CARD[f[1]] if i < dd else (0, 0), 'jump (A held %d) holding %s %d frames' % (a, f[1].upper(), dd), ' + '.join(x for x in (('A' if i < a else ''), ('%s %d/%d' % (f[1].upper(), i + 1, dd) if i < dd else '')) if x))
        continue
    d, k = f[0], int(f[1])
    for i in range(k):
        st(0, CARD[d], ('hold %s (%d frames)' % (d.upper(), k) if not d.startswith('h') else ('BACKUP: ' if riding else '') + 'ride at walking speed: half-tilt %s (%d frames)' % (d[1:].upper(), k)) if d != 'wait' else ('stand' if not riding else 'ride Laki'), (('%s %d/%d' % (d.upper(), i + 1, k)) if not d.startswith('h') else ('half %s %d/%d' % (d[1:].upper(), i + 1, k))) if d != 'wait' else '')
if not riding:
    st(0x400, (0, 0), 'C-down: mount Laki', 'C-DOWN')
    for i in range(RIDE): st(0, (0, 0), 'ride Laki', '')
st(0x40, (0, 0), 'B: dismount (frame 0)', 'B  (frame 0)')
HOLD = os.environ.get('HOLD', 'down'); dn = CARD[HOLD]
for fr in range(1, T): st(0, dn, 'hold %s, count frames after B' % HOLD.upper(), '%s  frame %d' % (HOLD.upper(), fr))
st(0x400, dn, 'C-down on frame %d after B (+ %s)' % (T, HOLD.upper()), 'C-DOWN + %s  frame %d' % (HOLD.upper(), T))
for i in range(30): st(0, dn, 'remount' if HOLD != 'down' else 'remount: Laki carries Mario into the tower', HOLD.upper())
for i in range(40): st(0, (0, 0), 'inside the tower' if log[-1]['in'] else 'end', '')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
q = log[-1]; print(len(log), 'frames; end (%.1f %.1f %.1f) inside=%s' % (q['x'], q['y'], q['z'], q['in']))
