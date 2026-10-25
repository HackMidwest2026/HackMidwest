"""kpa_62 "blockless": reproduce the runner's setup from the video (2026-10-24_08-20-08.mp4) and test variants.
Start: Mario on the y-35 ledge at (-514.1111, -5.2539) with Laki settled beside him (kpa62_place, setup only).
Program tokens (one token = one held input; N = frames, 1 frame = one game frame):
  S:ANG:N      hold stick at screen angle ANG (0 right, 90 down, 180 left, 270 up; 45 = down-right) N frames
  J:ANG:A:N    jump: A held A frames, stick ANG held N frames total (ANG '-' = neutral)
  H:N          hammer (B 2 frames), then N idle frames
  W:N          idle N frames
  WALL:ANG     hold ANG until Mario stops moving (max 120)
After the program: C-down (mount), ride R frames, C-down (dismount), hold down, C-down on frame K after the
dismount, then hold down 30 frames and report whether Mario ends up inside the tower.
usage: kpa62_runner.py STATE 'PROGRAM' [R] [K]"""
import os, sys, math
from emu import *
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CD = 0x400
def stick(ang, mag=80):
    return stick_for(ang % 360, mag) if ang != '-' else (0, 0)
def run(e, prog, log=False):
    for t in prog.split():
        f = t.split(':')
        if f[0] == 'S':
            for i in range(int(f[2])): e.step(0, *stick(float(f[1])), 2)
        elif f[0] == 'J':
            ang = f[1] if f[1] == '-' else float(f[1]); a, n = int(f[2]), int(f[3])
            for i in range(n): e.step(A if i < a else 0, *stick(ang), 2)
        elif f[0] == 'H':
            for i in range(2): e.step(B, 0, 0, 2)
            for i in range(int(f[1])): e.step(0, 0, 0, 2)
        elif f[0] == 'W':
            for i in range(int(f[1])): e.step(0, 0, 0, 2)
        elif f[0] == 'WALL':
            last = None
            for i in range(120):
                e.step(0, *stick(float(f[1])), 2); p = player(e)
                if last and abs(p['x'] - last[0]) + abs(p['z'] - last[1]) < 0.01: break
                last = (p['x'], p['z'])
        if log:
            p = player(e); print('  %-14s -> (%.4f, %.2f, %.4f) act %d yaw %.0f' % (t, p['x'], p['y'], p['z'], p['action'], p['yaw']))
def clip(e, R=18, K=34):
    s = player(e)
    e.step(CD, 0, 0, 2)
    for i in range(R - 1): e.step(0, 0, 0, 2)
    e.step(CD, *stick(90), 2)
    for fr in range(1, K): e.step(0, *stick(90), 2)
    e.step(CD, *stick(90), 2); ok = False
    for f in range(30):
        e.step(0, *stick(90), 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): ok = True
    return s, ok, player(e)
def start(e, st):
    e.load(st); e.step(0, 0, 0, 2); place(e, -514.1111, -5.2539, y=35.0)
if __name__ == '__main__':
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/kr%d' % os.getpid())
    st, prog = sys.argv[1], sys.argv[2]
    R = int(sys.argv[3]) if len(sys.argv) > 3 else 18
    K = int(sys.argv[4]) if len(sys.argv) > 4 else 34
    start(e, st); run(e, prog, log=True)
    s, ok, q = clip(e, R, K)
    print('stand (%.4f, %.4f)  ->  %s   end (%.1f, %.1f, %.1f)' % (s['x'], s['z'], 'CLIP' if ok else 'no', q['x'], q['y'], q['z']))
