"""Star-power shimmer (status_star_shimmer.c) as an RNG readout: trigger it, log particle RAM per frame, screenshot,
and check the colours against a gRandSeed prediction.
JP addresses (US + 0x1C0, verified by shimmer_find.py): gStatusBar 0x8010F118, ShimmerEmitters 0x8010D1C0.
DIAGNOSTIC RAM writes (setup only): gRandSeed overwritten after the state load; statusBar->shimmerState = 1 and
shimmerTime = 60, i.e. exactly what add_star_power() (Focus) sets, to start the shimmer without menu navigation.
run from /tmp/claude-0/pm/bot1:
  DISPLAY=:93 M64P_GFX=/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus \
  PYTHONPATH=. python3 shimmer_probe.py STATE OUTDIR SEEDHEX [SEEDHEX...]"""
import sys, os, json, subprocess
sys.path.insert(0, os.getcwd())
import emu as _emu
if os.environ.get('M64P_RSP'): _emu.RSP = os.environ['M64P_RSP']   # e.g. rsp-z64 (LLE) for the z64 LLE RDP plugin
from emu import *
from rngsim import adv
SB, EM, SEEDA = 0x8010F118, 0x8010D1C0, 0x800743F0

def rii(s, mx):                       # rand_int_internal: returns (value, new seed)
    part = 0xFFFFFFFF // (mx + 1) or 1
    while True:
        s = adv(s); r = s // part
        if r < mx + 1: return r, s
def rint(s, mx):
    mx = abs(mx)
    if mx == 0: return 0, s
    if mx == 1: v, s = rii(s, 1000); return int(v > 500), s
    if mx == 100: v, s = rii(s, 1009); return v // 10, s
    return rii(s, mx)
def shimmer_colours(s):
    out = []
    for j in range(56):
        r, s = rint(s, 127); g, s = rint(s, 127 - r); b, s = rint(s, 127 - g - r)
        out.append((r + 128, g + 128, b + 128))
    return out, s

if __name__ == '__main__':
    st, OUT = sys.argv[1], sys.argv[2]; seeds = [int(x, 16) for x in sys.argv[3:]]
    os.makedirs(OUT, exist_ok=True)
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/sp%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    res = {}
    for seed in seeds:
        e.load('states/' + st); e.step(0, 0, 0, 2)
        e.w32(SEEDA, seed)                                   # DIAGNOSTIC
        for i in range(3): e.step(0, 0, 0, 2)                # settle; shots of the plain bar
        e.w8(SB + 0x57, 1); e.w8(SB + 0x58, 60)              # DIAGNOSTIC: as add_star_power()
        frames = []
        for f in range(46):
            s0 = e.u32(SEEDA)
            e.step(0, 0, 0, 2)
            parts = []
            for j in range(56):
                p = EM + 0x1C * (j + 1)
                parts.append(dict(anim=e.s8(p + 7), rgb=(e.u8(p + 3), e.u8(p + 4), e.u8(p + 5)),
                                  x=round(e.f32(p + 8), 2), y=round(e.f32(p + 12), 2), sc=round(e.f32(p + 0x18), 3)))
            frames.append(dict(seed_before=s0, alive=e.u8(EM), tl=e.s8(EM + 1), parts=parts,
                               emx=e.f32(EM + 8), emy=e.f32(EM + 12)))
            subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage',
                            '%s/s%08x_%02d.png' % (OUT, seed, f)], check=True)
        # find the frame the colours were drawn and the RNG offset within it
        f0 = next(i for i, fr in enumerate(frames) if fr['parts'][0]['anim'] == 0)
        ram = [tuple(p['rgb']) for p in frames[f0]['parts']]
        s, hit = frames[f0]['seed_before'], None
        for k in range(400):
            cols, _ = shimmer_colours(s)
            if cols == ram: hit = k; break
            s = adv(s)
        draws = None
        if hit is not None:
            s = frames[f0]['seed_before']
            for k in range(hit): s = adv(s)
            s1 = s; _, s2 = shimmer_colours(s1); n = 0
            while s1 != s2: s1 = adv(s1); n += 1
            draws = n
        res['%08x' % seed] = dict(draw_frame=f0, rng_offset_in_frame=hit, draws=draws, colours=ram,
                                  emitter=(frames[f0]['emx'], frames[f0]['emy']),
                                  track=[[(p['anim'], p['x'], p['y'], p['sc']) for p in fr['parts'][:4]] for fr in frames])
        print('%08x draw frame %d, offset %s, draws %s, first colours %s' % (seed, f0, hit, draws, ram[:4]))
    json.dump(res, open(OUT + '/shimmer.json', 'w'))
