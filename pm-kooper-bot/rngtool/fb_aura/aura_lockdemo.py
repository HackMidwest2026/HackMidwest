"""Lock test: observed aura angles (true draw + reading error) -> aura_lock (C) -> is the found seed the true one?
Truth comes from the frame model (aura_model.Aura, which matched the emulator on 5 seeds x 2000 frames) in the
boss_2304_route_menu.st situation (part counters, bolt phases and first coin frame as measured there), from a random
seed, starting at a random frame of the 20-frame cycle. The search is told the part counters and the sky-bolt phase
(both readable from the screen); the low-bolt phase (130) and the coin phase (48) are searched.
usage: python3 aura_lockdemo.py TRIALS DELTA_SEARCH ERR_MAX FRAMES    (needs gcc)"""
import sys, os, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aura_model import Aura, bolt_frames, SKY, LOW, rand_int, adv
HERE = os.path.dirname(os.path.abspath(__file__))
T0 = [11, 16, 7, 1, 12, 14, 10, 18, 19, 19, 5, 3, 11, 14, 6, 11]      # route menu state, frame 0
SKY0, LOW0, COIN0 = 29, 19, 28
EXE = '/tmp/aura_lock_%d' % os.getpid()


def scenario(seed, skip, N):
    """frames skip .. skip+N-1 of the menu from a seed at frame 0; returns observations and the truth"""
    B = {}
    for f in bolt_frames(SKY0, 0, SKY, skip + N + 10) + bolt_frames(LOW0, 0, LOW, skip + N + 10): B[f] = B.get(f, 0) + 1
    m = Aura(seed, T0, COIN0, B)
    for f in range(skip): m.frame()
    t_at = list(m.t)
    obs, truth_states = [], []
    for f in range(N):
        o = m.frame(); obs.append([v for _, v in o['angles']])
    p220 = (SKY0 - skip) % 220
    return t_at, p220, obs


def first_state(seed, skip, A):
    """state right after the first aura draw of frame skip+A (replay with the model's order)"""
    B = {}
    for f in bolt_frames(SKY0, 0, SKY, skip + A + 10) + bolt_frames(LOW0, 0, LOW, skip + A + 10): B[f] = B.get(f, 0) + 1
    m = Aura(seed, T0, COIN0, B)
    for f in range(skip + A): m.frame()
    s = m.s
    for _ in range(B.get(m.f, 0)): s, _ = rand_int(s, 359)
    if m.f == m.nc: s, _ = rand_int(s, 100)
    s, _ = rand_int(s, 359)
    return s


if __name__ == '__main__':
    trials, dS, err, N = (int(x) for x in sys.argv[1:5])
    subprocess.run(['gcc', '-O2', '-o', EXE, os.path.join(HERE, 'aura_lock.c')], check=True, stderr=subprocess.DEVNULL)
    R = random.Random(11); ok = 0; unique_at = []
    for t in range(trials):
        seed = R.getrandbits(32); skip = R.randrange(0, 400)
        t_at, p220, obs = scenario(seed, skip, N)
        noisy = [[(a + R.randint(-err, err)) % 360 for a in fr] for fr in obs]
        txt = '%d %d %d\n%s\n' % (N, dS, p220, ' '.join(map(str, t_at))) + ''.join('%d %s\n' % (len(fr), ' '.join(map(str, fr))) for fr in noisy)
        out = subprocess.run([EXE], input=txt, capture_output=True, text=True).stdout
        A = next(i for i, fr in enumerate(obs) if len(fr) >= 3)
        truth = first_state(seed, skip, A)
        lines = out.strip().split('\n')
        surv = [int(l.split(': ')[1].split()[0]) for l in lines if l.startswith('after +')]
        one = next((k + 1 for k, v in enumerate(surv) if v == 1), None)
        fin = lines[-1]; nseeds = int(fin.split('surviving: ')[1].split(';')[0]); found = int(fin.split('= ')[1].split(',')[0], 16)
        good = nseeds == 1 and found == truth; ok += good
        # frames until the (seed, phase, coin) survivors stop shrinking, counted from the first observed frame
        print('trial %d seed %08x start f%d: anchor f%d (%d draws), %s, distinct seeds left %d, true seed found: %s'
              % (t, seed, skip, A, len(obs[A]), lines[0].split(', ')[1], nseeds, found == truth), flush=True)
        print('   distinct seeds left after anchor +1, +2, ...: %s; unique from +%s (= %s frames from the first observed frame)'
              % (surv[:10], one, None if one is None else A + one + 1))
        unique_at.append(None if one is None else A + one + 1)
    u = sorted(x for x in unique_at if x is not None)
    if u: print('frames of aura watched until one seed is left: median %d, max %d (%.2f s)' % (u[len(u) // 2], u[-1], u[-1] / 30))
    print('locked on the true seed: %d/%d (search delta %d, reading error up to +-%d deg, %d frames = %.2f s)' % (ok, trials, dS, err, N, N / 30))
