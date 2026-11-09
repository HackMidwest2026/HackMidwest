"""Final Bowser phase 2 T1 -> T6 end to end: emulator renders -> the capture simulation -> the page (test_fb14_page.js),
and the page's beeped frames pressed in the emulator (JP; Glide64 on an X display).

From BUILD/t1_menu.st (route_build.py; DIAGNOSTIC: gRandSeed written there, setup only). Per turn t = 1..4:
  a. render: PRE idle frames in Mario's menu, Mario's action (Super Charge / the Jelly, confirm delay 0; the "+3" popup
     closed with A on confirm + K), the partner menu, its inputs up to the last A (Cloud Nine's target on Mario /
     Strategies -> Do Nothing), then WAIT idle frames on that screen;
  b. that render, after the turns already played, through t6_capsim.py and fed to the page in real time; the page's last
     plan for this turn gives the clock frame to confirm on (clock frame 0 = T1's Mario confirm);
  c. the confirm pressed on that frame in the emulator (and, from the same state, one frame early and late for the
     outcome table), Bowser's turn played to the next menu with no input (Cloud Nine: its three A presses);
then T5 (Peach Beam, A every 20 frames outside menus for the text) and the T6 Super Charge (its popup left alone),
rendered and fed after all of it: the page's T6 lock (narrowed by the carried stream) against the true seed.
Writes OUT/report.json (per turn: the plan, the confirm pressed, Bowser's attack and dodge value, miss at -1/0/+1; T6:
the lock, its time, the truth). Needs the page served at URLBASE (tot.html) with OUT under it.
Env: START=4 begins at the build's T4 menu; STOP_ON_HIT=1 stops after a turn where Bowser hit (the route is off then);
LATEMS (default 25) drops a picture later than that; WAIT frames on each lever screen (default 400).
Run from /tmp/claude-0/pm/bot1: DISPLAY=:93 M64P_GFX=... M64P_DATA=... PYTHONPATH=. python3 fb14_e2e.py BUILD SEEDHEX OUT URLBASE [TURNS=4] [T6=1]"""
import sys, os, json, subprocess, random, struct, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
from route_build import TURNS

HERE = os.path.dirname(os.path.abspath(__file__)); RNG = os.path.dirname(HERE)
WAIT = int(os.environ.get('WAIT', '400'))


class Seg:
    """a rendered stretch: its screenshots (shot i = after step i of the stretch) and the seed before each step"""
    def __init__(self, r, d):
        self.r, self.d, self.n, self.s0, self.bs = r, d, 0, [], []
        os.makedirs(d, exist_ok=True)

    def step(self, b=0, y=0, shot=True):
        self.s0.append(self.r.e.u32(SEED)); self.r.step(b, y); self.bs.append(bstate(self.r.e))
        if shot: subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/s%04d.png' % (self.d, self.n)], check=True)
        self.n += 1

    def load(self, path, shot=True):
        """a savestate, and the frame the emulator runs on loading it (route.Run.load steps once): that frame is the
        stretch's step 0, with its picture, so the video and the frame count have no gap where a stretch begins"""
        e = self.r.e; e.load(path); self.s0.append(e.u32(SEED)); e.step(0, 0, 0, 2); self.bs.append(bstate(e))
        if shot: subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/s%04d.png' % (self.d, self.n)], check=True)
        self.n += 1

    def idle(self, k, shot=True):
        for i in range(k): self.step(0, 0, shot)

    def seq(self, items, shot=True):
        for b, y, n in items:
            self.step(b, y, shot)
            for i in range(n - 1): self.step(0, 0, shot)


def capsim(d, n, out, seed):
    subprocess.run([sys.executable, os.path.join(HERE, 't6_capsim.py'), d, '0', str(n - 1), out, str(seed)], check=True, stdout=subprocess.DEVNULL)
    jd = out + '_j'; shutil.rmtree(jd, ignore_errors=True); os.makedirs(jd)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', out + '.mkv', '-q:v', '3', '-start_number', '0', jd + '/f%05d.jpg'], check=True)
    return sorted(os.listdir(jd))


def mario_items(t):
    ma, mv, pa = TURNS[t - 1]
    r = Run.__new__(Run)
    items = (r.moves(mv['wheel']) + [(A, 0, 20)] + r.moves(mv['sub']) + [(A, 0, 15)])
    return items, pa


def partner_items(pa):
    if pa == 'cloud_nine': return [(A, 0, 20), (0, DOWN, 10), (0, DOWN, 10), (A, 0, 15)]
    return [(0, UP, 10), (A, 0, 20), (0, DOWN, 10)]


def play_after_confirm(seg, pa, shot, cap=4000):
    """the confirm A, then (Cloud Nine) its three A presses, Bowser's turn to the next Mario menu"""
    seg.step(A, 0, shot); k0 = seg.n
    if pa == 'cloud_nine':
        for i in range(259):
            k = seg.n - k0; seg.step(A if k in (132, 152, 172) else 0, 0, shot)
    n = 0
    while bstate(seg.r.e) != 13 and n < cap: seg.step(0, 0, shot); n += 1


def outcome(r):
    return dict(hp=r.e.s8(PLAYER_DATA + 2), ko=r.partner_ko(), charges=r.e.s8(BSTATUS + 0x97), menu=bstate(r.e) == 13)


def run_page(urlbase, out, manifest, tag):
    mf = os.path.join(out, 'manifest_%s.json' % tag); json.dump(manifest, open(mf, 'w'))
    p = subprocess.run(['node', os.path.join(RNG, 'test_fb14_page.js'), urlbase, mf], capture_output=True, text=True, env=dict(os.environ))
    line = [l for l in p.stdout.splitlines() if l.startswith('{')]
    res = json.loads(line[-1]) if line else dict(error=p.stderr[-2000:])
    json.dump(res, open(os.path.join(out, 'page_%s.json' % tag), 'w'))
    return res


if __name__ == '__main__':
    build, seed, out, urlbase = sys.argv[1], int(sys.argv[2], 16), os.path.abspath(sys.argv[3]), sys.argv[4]
    turns = int(sys.argv[5]) if len(sys.argv) > 5 else 4; do_t6 = (sys.argv[6] if len(sys.argv) > 6 else '1') == '1'
    start = int(os.environ.get('START', '1'))      # START=4: from the build's T4 menu (the page starts on T4's step)
    rel = os.path.relpath(out, os.environ.get('SERVE_ROOT', os.path.dirname(out)))
    rng = random.Random(seed); os.makedirs(out, exist_ok=True)
    r = Run('e2e', log=False)
    r.load(build + '/t%d_menu.st' % start); r.seed(seed)            # DIAGNOSTIC: gRandSeed at that menu (setup only)
    X = os.path.join(out, 'x1.st'); r.e.save(X)
    report = dict(seed='%08x' % seed, turns=[]); frames = []; G = 0; GM1 = None; refM = refS = None; truth = []   # truth: the seed before every global step
    for t in range(start, turns + 1):
        items, pa = mario_items(t)
        sa = Seg(r, os.path.join(out, 't%da' % t)); sa.load(X)
        pre = rng.randint(40, 80); sa.idle(pre)
        sa.seq(items); M = sa.n; sa.step(A)                         # Mario's confirm on step M of the stretch
        if t == start: GM1 = G + M
        K = rng.randint(78, 100) if t != 3 else -1
        while bstate(r.e) != 14 and sa.n - M < 600: sa.step(A if (K >= 0 and sa.n - M == K) else 0)
        sa.idle(20); sa.seq(partner_items(pa)); R0 = sa.n
        Y = os.path.join(out, 'y%d.st' % t); r.e.save(Y)
        sa.idle(WAIT)
        if pa == 'cloud_nine' and refM is None: refM = ('a', t, R0 + 10)
        if pa != 'cloud_nine' and refS is None: refS = ('a', t, R0 + 10)
        jpg = capsim(sa.d, sa.n, os.path.join(out, 't%da_cap' % t), seed + t)
        segA = ['%s/t%da_cap_j/%s' % (rel, t, f) for f in jpg]
        man = dict(frames=frames + segA, step='charge' if start == 1 else 'lever', turn=start, lateMs=int(os.environ.get('LATEMS', '25')))
        # the reference screens: capture frames of those game frames (2 per game frame)
        for nm, ref in (('refM', refM), ('refS', refS)):
            if ref and ref[1] == t: man[nm] = len(frames) + 2 * ref[2]
            elif ref: man[nm] = report['ref_' + nm]
        for nm in ('refM', 'refS'):
            if nm in man: report['ref_' + nm] = man[nm]
        res = run_page(urlbase, out, man, 't%d' % t)
        plans = [p for p in res.get('plans', []) if p.get('turn') == t and p.get('target') is not None]
        tgt = plans[0]['target'] if plans else None      # the first beeps are the ones pressed
        d = (GM1 + tgt) - (G + R0) - 1 if tgt is not None else None    # Y holds step R0 - 1's end: loading it runs step R0, then d idle steps, then the confirm
        blind = d is None or d < 0 or d >= WAIT
        if blind: d = WAIT // 2
        row = dict(turn=t, pre=pre, K=K, M=G + M, R0=G + R0, plan=plans[0] if plans else None, nplans=len(plans), confirm_global=G + R0 + 1 + d, blind=blind,
                   page=dict(late=res.get('late'), fb14=res.get('fb14'), errors=res.get('pageErrors'), events=[e for e in res.get('events', []) if e.get('ev', '').startswith('fb14') or e.get('ev', '').startswith('charge')][-30:]))
        # the neighbours: from Y, confirm at d - 1 and d + 1 (no shots)
        nb = {}
        for dd in (-1, 1):
            tmp = Seg(r, os.path.join(out, 'tmp')); tmp.load(Y, False); tmp.idle(d + dd, False); play_after_confirm(tmp, pa, False); nb[dd] = outcome(r)
        sb = Seg(r, os.path.join(out, 't%db' % t)); sb.load(Y, False); sb.idle(d, False); sb.n = 0
        play_after_confirm(sb, pa, True); oc = outcome(r)
        nxt = os.path.join(out, 'x%d.st' % (t + 1)); r.e.save(nxt); X = nxt
        row.update(outcome=oc, minus1=nb[-1], plus1=nb[1], s0_rays0_true='%08x' % sa.s0[M + 13] if t != 3 else None)
        MHP = int(os.environ.get('MARIO_HP', '5'))          # v86: the build's Mario HP (MARIO_HP=10: the runner's T1-T4, route_build.py)
        ok = lambda o, tt: o['hp'] == MHP and (tt != 4 or (o['ko'] and o['ko'][0] != 0))
        row.update(miss=ok(oc, t), miss_m1=ok(nb[-1], t), miss_p1=ok(nb[1], t))
        print(json.dumps({k: v for k, v in row.items() if k != 'page'}), flush=True)
        report['turns'].append(row)
        if not row['miss'] and os.environ.get('STOP_ON_HIT'): print('Bowser hit: the route is off (Peach heals Mario); stopping', flush=True); do_t6 = False; break
        # the actual stretch: segment a up to the confirm, then segment b
        jb = capsim(sb.d, sb.n, os.path.join(out, 't%db_cap' % t), seed + 10 + t)
        na = 2 * (R0 + 1 + d)                                      # capture frames of a before the confirm's picture
        frames = frames + segA[:na] + ['%s/t%db_cap_j/%s' % (rel, t, f) for f in jb]
        G += R0 + 1 + d + sb.n; truth += sa.s0[:R0] + sb.s0
        json.dump(dict(GM1=GM1, s0=['%08x' % x for x in truth]), open(os.path.join(out, 'truth.json'), 'w'))
        json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=1)
    if do_t6:
        # T5 and the T6 Charge up to just before the earliest popup A (+77): the frames are the same whatever K is
        s5 = Seg(r, os.path.join(out, 't56')); s5.load(X)
        s5.idle(rng.randint(40, 80)); s5.seq([(0, DOWN, 10)] * 2 + [(A, 0, 20)] + [(0, UP, 10)] + [(A, 0, 20)]); PB = s5.n; s5.step(A)
        n = 0
        while bstate(r.e) != 13 and n < 3000: s5.step(A if (n % 20 == 19 and bstate(r.e) not in (13, 14, 17)) else 0); n += 1
        hp5 = r.e.s8(PLAYER_DATA + 2)
        s5.idle(rng.randint(40, 90)); s5.seq([(0, UP, 10)] * 2 + [(A, 0, 20)] + [(0, DOWN, 10)] * 2 + [(A, 0, 15)]); M6 = s5.n; s5.step(A)
        s5.idle(76); Z = os.path.join(out, 'z6.st'); r.e.save(Z); nZ = s5.n          # Z holds step M6 + 76's end
        s5.idle(64)                                                                   # (pass 1: the popup closes by itself)
        j5 = capsim(s5.d, s5.n, os.path.join(out, 't56_cap'), seed + 56)
        lateMs = int(os.environ.get('LATEMS', '25'))
        man = dict(frames=frames + ['%s/t56_cap_j/%s' % (rel, f) for f in j5], step='charge' if start == 1 else 'lever', turn=start, lateMs=lateMs, refM=report.get('ref_refM'), refS=report.get('ref_refS'))
        res = run_page(urlbase, out, man, 't6')
        ev = lambda R, k: [e for e in R.get('events', []) if e.get('ev') == k]
        lock = ev(res, 'chargeLock'); planK = ev(res, 'fb2PlanK'); Kp = planK[0].get('k') if planK and planK[0].get('k') else None
        report['t6'] = dict(PB=G + PB, M6=G + M6, hp_after_t5=hp5, s0_rays0_true='%08x' % s5.s0[M6 + 13], lock=lock[-1] if lock else None,
                            narrow=ev(res, 'chargeNarrow'), t6cands=ev(res, 'fb14T6Cands'), peach=ev(res, 'fb14Peach'), planK=planK[:1], fb2=res.get('fb2'), errors=res.get('pageErrors'))
        x = s5.s0[PB]; k = 0
        while x != s5.s0[M6 + 13] and k < 20000: x = (x * 0x5D588B65 + 1) & 0xFFFFFFFF; k += 1
        report['t6'].update(steps_pb_to_rays0=k, frames_pb_to_rays0=M6 + 13 - PB)
        print(json.dumps(report['t6'])[:3000], flush=True)
        # pass 2: the popup A on the planned K (no plan: K = 100), Bowser's turn, the T7 Power Bounce target screen, a wait
        K = Kp if Kp is not None and 78 <= Kp <= 136 else 100
        s7 = Seg(r, os.path.join(out, 't67')); s7.load(Z, False); s7.n = 0              # the load runs step M6 + 77
        while 78 + s7.n < K: s7.step(0)                                                # steps M6 + 78 .. M6 + K - 1
        s7.step(A); n = 0                                                              # the popup A on M6 + K
        while not (n > 80 and bstate(r.e) == 13) and n < 1500: s7.step(0); n += 1
        hp6 = r.e.s8(PLAYER_DATA + 2); s7.idle(20)
        s7.seq([(A, 0, 20)] + [(0, DOWN, 10)] + [(A, 0, 15)]); R7 = s7.n; Y7 = os.path.join(out, 'y7.st'); r.e.save(Y7)
        s7.idle(WAIT)
        j7 = capsim(s7.d, s7.n, os.path.join(out, 't67_cap'), seed + 67)
        # the video: T5 / T6 to step M6 + 76 (its picture is shot M6 + 77), then pass 2 (its first shot is step M6 + 77's)
        f56 = ['%s/t56_cap_j/%s' % (rel, f) for f in j5][:2 * (nZ + 1)]
        man = dict(frames=frames + f56 + ['%s/t67_cap_j/%s' % (rel, f) for f in j7], step='charge' if start == 1 else 'lever', turn=start, lateMs=lateMs, refM=report.get('ref_refM'), refS=report.get('ref_refS'),
                   refB=len(frames) + len(f56) + 2 * (R7 + 10))
        res = run_page(urlbase, out, man, 't7')
        planT7 = ev(res, 'fb2PlanT7'); d = planT7[0].get('d') if planT7 and planT7[0].get('d') is not None else None
        kSeen = ev(res, 'fb2K')
        # press: the page's d is confirm-relative (T6 confirm = step M6); Y7 holds the end of step M6 + 78 + R7 - 1
        out7 = {}
        for dd in ((-1, 0, 1) if d is not None else (None,)):
            r.e.load(Y7); r.e.step(0, 0, 0, 2); at = M6 + 79 + R7                       # the next step (the load ran M6 + 78 + R7)
            want = (d + dd) if d is not None else at + WAIT // 2 - M6
            while at < M6 + want: r.step(0); at += 1
            dc = at; r.step(A); at += 1
            for i in range(27 * 14 + 100):
                kk = at - dc; r.step(A if kk >= 44 and (kk - 44) % 27 == 0 else 0); at += 1
            bh = r.bowser_hp(); lost = 80 - (bh[0] if bh else 0); cum = [sum(max(1, 15 - j) for j in range(n2)) for n2 in range(1, 12)]
            out7[str(dd)] = dict(bowser_hp=bh, bounces=(next((n2 + 1 for n2, c in enumerate(cum) if c >= lost), None) if lost > 0 else 0) if lost < 84 else '7+ (dead)')
        report['t7'] = dict(K_pressed=K, K_planned=Kp, closecall=hp6 == 5, hp_after_t6=hp6, kSeen=kSeen[:1], planT7=planT7[:1], pressed=out7, fb2=res.get('fb2'), errors=res.get('pageErrors'), late=res.get('late'))
        print(json.dumps(report['t7'])[:3000], flush=True)
        truth += s5.s0; json.dump(dict(GM1=GM1, s0=['%08x' % x for x in truth]), open(os.path.join(out, 'truth.json'), 'w'))
    json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=1)
