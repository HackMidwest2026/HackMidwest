"""Frame-fed end to end of the Jr. Troopa Charge-lock route: emulator renders through the capture simulation into the page
(../test_jr_page.js), and the page's planned presses played in the emulator.
Per lever (T3 Bomb, T4 Maple Syrup, T5 Do Nothing, T6 Power Bounce), in order:
  1. render the fight (jc_render.py, Glide64 screenshots) with every earlier lever pressed on the page's planned frame,
     up to this lever's target screen and 5 s on it (screenshots only from the first frame that differs from the last
     render: the emulator is deterministic);
  2. the capture simulation of all of it (jc_capsim.py: ../fb2_route/t6_capsim.py's, cached per game frame), as JPEG
     frames, served on 127.0.0.1;
  3. the page fed those frames in real time (it saves the target screens the runner would save, from the frames named
     below); its plan for this lever (the clock frame of its tracker, whose frame 0 is its lock's Charge confirm + 13)
     is this lever's press, as a log frame.
Then each planned press and the frames next to it (-1, +1) are played without screenshots (the rest of the fight as
planned) and the outcome read off the emulator log: Close Call dodged, Power Bounce bounces.
usage: python3 jc_e2e_page.py SEEDHEX OUTDIR [LEVERS=all] (DISPLAY with Xvfb, M64P_GFX = glide64mk2, M64P_DBG=1; a page
       build at PAGE = the standalone page; the page test runs from ../ with node). Writes OUTDIR/result.json."""
import sys, os, json, subprocess, shutil, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SEED, OUT = sys.argv[1], sys.argv[2]
LEVERS = ['T3 Bomb', 'T4 Syrup', 'T5 Nothing', 'T6 Bounce']
if len(sys.argv) > 3 and sys.argv[3] != 'all': LEVERS = LEVERS[:int(sys.argv[3])]
PAGE = os.environ.get('PAGE', '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html')
PORT = int(os.environ.get('PORT', '8771'))
PROF = {'T3 Bomb': 'jrcc_bomb', 'T4 Syrup': 'jrcc_syrup', 'T5 Nothing': 'jrcc_nothing', 'T6 Bounce': 'jrpb5'}
ORIGIN = {0: 'T1 Charge', 4: 'T3 Charge', 8: 'T5 Charge'}
# target-screen boxes in capture units (the route clips' OBS layout): the name box at the top left (hand on Jr. Troopa /
# on Mario: raster 108..200 x 132..162) and Bombette's Strategies panel
NAMEBOX = {'x': 0.3508, 'y': 0.2614, 'w': 0.117, 'h': 0.069}
STRATBOX = json.loads(os.environ.get('STRATBOX', '{"x": 0.27, "y": 0.27, "w": 0.30, "h": 0.17}'))
SHOTS = os.path.join(OUT, 'shots'); os.makedirs(SHOTS, exist_ok=True)
ENV = dict(os.environ)
def render(spec, log, shotfrom, shots=True):
    json.dump(spec, open(os.path.join(OUT, 'spec.json'), 'w'))
    env = dict(ENV, SHOTFROM=str(shotfrom))
    if not shots: env.pop('M64P_GFX', None)
    args = ['python3', os.path.join(HERE, 'jc_render.py'), SEED, os.path.join(OUT, 'spec.json'), log] + ([SHOTS] if shots else [])
    r = subprocess.run(args, env=env, capture_output=True, text=True); print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:], flush=True)
    return json.load(open(log))
def capsim(n):
    fr = os.path.join(OUT, 'frames'); shutil.rmtree(fr, ignore_errors=True)
    subprocess.run(['python3', os.path.join(HERE, 'jc_capsim.py'), SHOTS, str(n), fr, '7'], check=True, capture_output=True)
    return json.load(open(fr + '.json'))['shown'], len(os.listdir(fr))
def capidx(shown, g):
    return next(i for i, x in enumerate(shown) if x >= g)
def page(shown, nfr, R):
    S = R['screens']; T = []
    if 'T1 Bomb' in S: T.append(['jr_K', capidx(shown, S['T1 Bomb'] + 12), NAMEBOX])
    if 'T2 Whacka' in S: T.append(['jr_M', capidx(shown, S['T2 Whacka'] + 12), NAMEBOX])
    if 'T5 Nothing' in S: T.append(['jr_S', capidx(shown, S['T5 Nothing'] + 8), STRATBOX])
    json.dump({'targets': T}, open(os.path.join(OUT, 'pspec.json'), 'w'))
    shutil.copy(PAGE, os.path.join(OUT, 'tot.html'))
    r = subprocess.run(['node', os.path.join(ROOT, 'test_jr_page.js'), 'http://127.0.0.1:%d' % PORT, 'frames', str(nfr), os.path.join(OUT, 'pspec.json')], cwd=ROOT, capture_output=True, text=True, env=dict(ENV, CRATE='33.367'))
    try: return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: print(r.stdout[-2000:], r.stderr[-2000:]); raise
def outcome(R, name):
    L = R['log']; f = next(c[0] for c in R['confirms'] if c[1] == name)
    if name == 'T6 Bounce':
        caps = [140, 98, 68, 47]; hits = 2
        for i, o in enumerate([78, 105, 132, 159]):
            x = [c for c in L[f + o]['c'] if c[1] == 100 and c[0] != 0x80146D54] if f + o < len(L) else []
            if not x or x[0][2] > caps[i]: break
            hits += 1
        return hits
    for g in range(f, min(len(L), f + 400)):
        for c in L[g]['c']:
            if c[0] == 0x80277518: return 'dodge' if c[2] < 30 else 'hit'
    return None
srv = subprocess.Popen(['python3', '-m', 'http.server', '--bind', '127.0.0.1', str(PORT)], cwd=OUT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
res = {'seed': SEED, 'levers': {}}
at = {}; shotfrom = int(os.environ.get('FIRST_SHOTFROM', 0))   # screenshots already there from an identical first render
try:
    for lev in LEVERS:
        t0 = time.time()
        R = render({'at': at, 'stop': lev, 'stopwait': 150}, os.path.join(OUT, 'r_%s.json' % lev.replace(' ', '')), shotfrom)
        if R.get('error'): res['levers'][lev] = {'error': R['error']}; break
        shown, nfr = capsim(len(R['log']))
        P = page(shown, nfr, R)
        json.dump(P, open(os.path.join(OUT, 'page_%s.json' % lev.replace(' ', '')), 'w'))
        plans = [x for x in P['plans'] if x.get('prof') == PROF[lev]]
        org = P['JRT']['origin'] if P['JRT']['origin'] is not None else 0
        c0 = next(c[0] for c in R['confirms'] if c[1] == ORIGIN[org])
        entry = {'screen': R['screens'][lev], 'origin': ORIGIN[org], 'originLog': c0, 'plans': [{'t': x['t'], 'target': x['target'], 'p': x['mix']['p'], 'p4': x['mix'].get('p4'), 'doubt': x['mix'].get('doubt'), 'states': x['mix'].get('groups'), 'capPress': x['capPress']} for x in plans],
                 'lock': P['locks'], 'inputs': P['JRT']['inputs'], 'out': P['JRT']['out'], 'cross': P['JRT']['cross'], 'step': P['stepName'], 'late': P['late'], 'errors': P['pageErrors'], 'secs': round(time.time() - t0)}
        if plans:
            last = entry['plans'][0]                                # the first beeped plan (the runner on the screen presses it)
            h = [x for x in P['JRT']['hist'] if x['at'] <= last['t']]   # the tracker that made it: its Charge is its clock's frame 0 - 13
            org = h[-1]['k'] if h else org; c0 = next(c[0] for c in R['confirms'] if c[1] == ORIGIN[org]); entry['origin'] = ORIGIN[org]; entry['originLog'] = c0
            X = c0 + 13 + last['target']
            # the time the page beeped the press, as a game frame (capture frame -> the game frame on screen then)
            ci = int(last['capPress']); entry['beepGameFrame'] = shown[min(len(shown) - 1, ci)] if ci >= 0 else None
            entry['press'] = X; at[lev] = X; shotfrom = min(X - 2, len(R['log']))   # frames before the press are the last render's
        else: entry['press'] = None; print(lev, 'no plan:', P['headline'], P['detail'], flush=True)
        res['levers'][lev] = entry; print(lev, json.dumps(entry)[:600], flush=True)
        json.dump(res, open(os.path.join(OUT, 'result.json'), 'w'), indent=1)
        if entry['press'] is None: break
    # the planned presses and their neighbours in the emulator (no screenshots)
    for lev in at:
        res['levers'][lev]['emu'] = {}
        for d in (-1, 0, 1):
            a2 = {k: v for k, v in at.items() if k != lev}; a2[lev] = at[lev] + d
            later = [k for k in a2 if LEVERS.index(k) > LEVERS.index(lev)]
            for k in later: a2.pop(k)
            R = render({'at': a2, 'stop': LEVERS[LEVERS.index(lev) + 1] if LEVERS.index(lev) + 1 < len(LEVERS) else None, 'stopwait': 300}, os.path.join(OUT, 'p.json'), 10 ** 9, shots=False)
            res['levers'][lev]['emu'][d] = outcome(R, lev)
        print(lev, 'emulator at -1/0/+1:', res['levers'][lev]['emu'], flush=True)
        json.dump(res, open(os.path.join(OUT, 'result.json'), 'w'), indent=1)
finally:
    srv.terminate()
print(json.dumps(res)[:3000])
