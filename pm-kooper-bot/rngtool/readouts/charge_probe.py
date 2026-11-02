"""Charge probe (run from the emulator working dir, bot1/).  DIAGNOSTIC: seed written after state load. Logs per game frame: start seed, every rand_int (ra, max,
replayed value), energy_in_out parts (pos.x, unk_10, unk_14, unk_24, scale, unk_3C), camera matrices; screenshots.
usage: charge_probe.py STATE SEEDHEX "n:btn:x:y,..." NFRAMES OUTDIR [SHOT 0/1]"""
import sys, os, json, struct, subprocess
from emu import *
from pm import *
from rngsim import *
st, seed, inp, N, OUT = sys.argv[1], int(sys.argv[2], 16), sys.argv[3], int(sys.argv[4]), sys.argv[5]
SHOT = int(sys.argv[6]) if len(sys.argv) > 6 else 1
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cp%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
seq = []
for tok in inp.split(','):
    if not tok: continue
    p = tok.split(':'); n = int(p[0]); b = eval(p[1]) if len(p) > 1 and p[1] else 0
    x = int(p[2]) if len(p) > 2 else 0; y = int(p[3]) if len(p) > 3 else 0
    for i in range(n): seq.append((b if i == 0 else 0, x, y if i == 0 else 0))
while len(seq) < N: seq.append((0, 0, 0))
GC, GCID = 0x800B1D60, 0x800773E0
def fl(a): return struct.unpack('<f', struct.pack('<I', e.u32(a)))[0]
def scan():
    out = []
    base = 0x80000000
    # signature of part 0: unk_00 = 6, unk_18/1C/20 = 255, unk_28 = 255, unk_2C = 245
    r = e.ram
    for i in range(0x100000 // 4, 0x800000 // 4):
        if r[i] == 6 and r[i + 6] == 255 and r[i + 7] == 255 and r[i + 8] == 255 and r[i + 10] == 255 and r[i + 11] == 245:
            out.append(base + 4 * i)
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
    # remaining plain steps (per-frame advance done without rand_int)
    k = 0
    while s != s1 and k < 100: s = adv(s); k += 1
    fx = {}
    if f % 1 == 0:
        if not known or any(c[0].startswith('0xe00d6') for c in calls): known = scan()
        for a in known:
            if e.s32(a) == 6: fx[hex(a)] = parts(a)
            if os.environ.get('NORAYS'):
                for k in range(1, 11): e.wf32(a + 0x48 * k + 0x34, 0.0)   # DIAGNOSTIC: ray quads zero length (background only)
    cams = {i: [fl(GC + 0x558 * i + 0xD4 + 4 * j) for j in range(16)] + [e.s16(GC + 0x558 * i + 0xA), e.s16(GC + 0x558 * i + 0xC), e.s16(GC + 0x558 * i + 0xE), e.s16(GC + 0x558 * i + 0x10), fl(GC + 0x558 * i + 0x6C)] for i in range(4)}
    frames.append({'f': f, 'in': seq[f], 's0': s0, 's1': s1, 'calls': calls, 'extra': k, 'fx': fx, 'cams': cams, 'camid': e.s16(GCID)})
    if SHOT: subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/%04d.png' % (OUT, f)], check=True)
json.dump(frames, open(OUT + '/log.json', 'w'))
print('done', N, 'frames; fx frames', sum(1 for fr in frames if fr['fx']), 'bad replays', sum(1 for fr in frames if fr['extra'] >= 100))
