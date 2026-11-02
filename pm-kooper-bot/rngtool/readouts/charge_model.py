"""Forward model of the Charge rays on gRandSeed (JP). Two energy_in_out(type 6, duration 45) effects, created on
frames c and c+3 (Mario's Charge / Super Charge and Goombario's Charge alike: scale 1.2 then 0.8).
Per frame (verified against emulator logs, charge_verify.py):
  1. script: effect creation = rand_int(360) base angle, then per part (10): rand_int(10) speed, rand_int(10) phase
     (unk_14 = -phase); the new effect is updated in the same frame
  2. coin (status-bar coin, rand_int(100) every 24 frames, 48 after a roll >= 70) -- order vs effects: COIN_FIRST
  3. effect updates, in creation order: part0 life (removed when it drops below 0), then each part: unk_14++,
     on reaching 10 -> 0 and unk_3C = rand_int(359)
  4. per-frame rand_int(1)
rand_int(n) is the game's (rngsim.py): internal(max) with rejection."""
import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
M32 = 0xFFFFFFFF
def adv(s): return (s * 0x5D588B65 + 1) & M32
def internal(s, mx):
    d = M32 // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    mx = abs(mx)
    if mx == 0: return s, 0
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)
COIN_FIRST = True
class Effect:
    def __init__(self, s, scale0):
        s, base = rand_int(s, 360)
        self.scale0 = scale0; self.life = 45; self.t = 0; self.alpha0 = 0; self.parts = []
        for i in range(1, 11):
            s, sp = rand_int(s, 10); s, ph = rand_int(s, 10)
            speed = -(sp + 4); u14 = -ph
            posx = (10 - u14) * (-speed)
            self.parts.append({'speed': speed, 'u14': u14, 'posx': float(posx), 'th': (i - 1) * 36 + base,
                               'scale': 1.0 - (i % 3) * 0.3, 'alpha': 0})
        self.s = s
    def update(self, s, out):
        self.life -= 1; self.t += 1
        if self.life < 0: return s, False
        if self.life < 16: self.alpha0 = self.life * 16
        if self.t < 16: self.alpha0 = self.t * 16 + 15
        for p in self.parts:
            p['u14'] += 1
            if p['u14'] >= 10:
                p['u14'] = 0; p['posx'] = -10 * p['speed']
                s, p['th'] = rand_int(s, 359); out.append(('r', p['th']))
            p['posx'] += p['speed']
            ang = p['u14'] * 180 / 10
            p['alpha'] = 0 if (ang < 0 or ang > 180) else int(math.sin(math.radians(ang)) * 255)
        return s, True
def simulate(seed, nframes, spawns=(0, 3), scales=(1.2, 0.8), coin_frames=(), coin_rule=None, snapshot=None):
    """seed = gRandSeed at the start of frame 0 (frame 0 = first effect's creation). coin_frames: frames with a coin
    draw (or coin_rule = (first_frame,) to follow the 24/48 rule from the rolls). Returns per-frame list of
    (draws, visible rays) where a visible ray is (effect index, theta, alpha_total, D0, D1) in world units."""
    s = seed; effs = []; frames = []; coin_next = coin_rule[0] if coin_rule else None
    cf = set(coin_frames)
    for f in range(nframes):
        out = []
        for k, sf in enumerate(spawns):
            if f == sf:
                e = Effect(s, scales[k]); s = e.s; e.idx = k; effs.append(e); out.append(('init', k))
        def coin(s):
            nonlocal coin_next
            if f in cf or (coin_next is not None and f == coin_next):
                s, v = rand_int(s, 100); out.append(('c', v))
                if coin_next is not None: coin_next = f + (48 if v >= 70 else 24)
            return s
        if COIN_FIRST: s = coin(s)
        alive = []
        for e in effs:
            s, ok = e.update(s, out)
            if ok: alive.append(e)
        effs = alive
        if not COIN_FIRST: s = coin(s)
        s, _ = rand_int(s, 1)
        vis = []
        for e in effs:
            for i, p in enumerate(e.parts):
                a = e.alpha0 * p['alpha'] / 255.0 / 255.0
                if a > 0:
                    vis.append((e.idx, i, p['th'] % 360, a, e.scale0 * (p['posx'] + 20), e.scale0 * (p['posx'] + 20 + 128 * p['scale'])))
        frames.append({'draws': out, 'vis': vis, 'seed_end': s,
                       'parts': {e.idx: [(p['th'], p['u14'], p['posx'], p['alpha']) for p in e.parts] for e in effs} if snapshot else None})
    return frames
