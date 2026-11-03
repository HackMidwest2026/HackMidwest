"""Jr. Troopa (final, battle 0x0207) frame logger: every rand_int call per game frame (caller ra, max, replayed value),
gRandSeed before/after, gBattleState, Mario HP, Jr. Troopa HP, gCameras[1] (perspective matrix + viewport), and the
energy_in_out(6) parts (the Charge rays) once they exist; optional Glide64 screenshots.
Runs from the emulator dir (/tmp/claude-0/pm/bot1), debug core.
usage: M64P_DBG=1 python3 jc_probe.py STATE SEEDHEX "n:btn:x:y,..." NFRAMES OUT.json [SHOTDIR]
  inputs: n frames, button pressed on the first of them (A/B/Z/... names from emu.py), stick x/y held on the first.
DIAGNOSTIC RAM write: gRandSeed (both copies) set to SEEDHEX right after the state load (stands for an unknown run).
NORAYS=1 (DIAGNOSTIC, render only): ray quads set to zero length each frame (background renders)."""
import sys, os, json, struct, subprocess
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import *
st, seed, inp, N, OUT = sys.argv[1], int(sys.argv[2], 16), sys.argv[3], int(sys.argv[4]), sys.argv[5]
SHOT = sys.argv[6] if len(sys.argv) > 6 else None
if SHOT: os.makedirs(SHOT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jcp%d' % os.getpid())
if SHOT:
    for i in range(30): e.step(0, 0, 0, 2)          # let the video plugin come up before the state load
e.load(st); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
seq = []
for tok in inp.split(','):
    if not tok: continue
    p = tok.split(':'); n = int(p[0]); b = eval(p[1]) if len(p) > 1 and p[1] else 0
    x = int(p[2]) if len(p) > 2 and p[2] else 0; y = int(p[3]) if len(p) > 3 and p[3] else 0
    for i in range(n): seq.append((b if i == 0 else 0, x if i == 0 else 0, y if i == 0 else 0))
while len(seq) < N: seq.append((0, 0, 0))
GC = 0x800B1D60
def fl(a): return struct.unpack('<f', struct.pack('<I', e.u32(a)))[0]
def scan():
    out = []; r = e.ram
    for i in range(0x100000 // 4, 0x800000 // 4):
        if r[i] == 6 and r[i + 6] == 255 and r[i + 7] == 255 and r[i + 8] == 255 and r[i + 10] == 255 and r[i + 11] == 245:
            out.append(0x80000000 + 4 * i)
    return out
def parts(a):
    rows = []
    for k in range(11):
        p = a + 0x48 * k
        rows.append([e.s32(p), fl(p + 4), fl(p + 8), fl(p + 12), e.s32(p + 0x10), e.s32(p + 0x14), e.s32(p + 0x24), fl(p + 0x34), fl(p + 0x38), fl(p + 0x3C), fl(p + 0x40)])
    return rows
frames = []; known = []
for f in range(N):
    s0 = e.u32(SEED); b, x, y = seq[f]; e.step(b, x, y, 2); s1 = e.u32(SEED)
    ev = e.dbg_events(); s = s0; calls = []
    for v in ev:
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        s, val = rand_int(s, mx); calls.append([hex(v['ra']), mx, val])
    k = 0
    while s != s1 and k < 100: s = adv(s); k += 1
    fx = {}
    if any(c[0] == '0xe00d6160' for c in calls): known = scan()
    for a in known:
        if e.s32(a) == 6:
            fx[hex(a)] = parts(a)
            if os.environ.get('NORAYS'):
                for j in range(1, 11): e.wf32(a + 0x48 * j + 0x34, 0.0)   # DIAGNOSTIC: ray quads zero length (background only)
    cam = [fl(GC + 0x558 + 0xD4 + 4 * j) for j in range(16)] + [e.s16(GC + 0x558 + 0xA), e.s16(GC + 0x558 + 0xC), e.s16(GC + 0x558 + 0xE), e.s16(GC + 0x558 + 0x10)]
    frames.append({'f': f, 'in': seq[f], 's0': s0, 's1': s1, 'calls': calls, 'extra': k, 'bs': bstate(e),
                   'hp': e.s8(PLAYER_DATA + 2), 'jr': e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8), 'fx': fx, 'cam': cam})
    if SHOT: subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/%04d.png' % (SHOT, f)], check=True)
json.dump(frames, open(OUT, 'w'))
print('done', N, 'frames; bad replays', sum(1 for fr in frames if fr['extra'] >= 100))
