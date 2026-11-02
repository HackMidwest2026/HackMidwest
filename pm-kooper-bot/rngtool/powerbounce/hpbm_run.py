"""Emulator test of the High Power Bounce Manipulator, closed loop: Blooper's Power Bounce target screen, the emulator's
video frame by frame into the page (hpbm_live.js, simulated 29.97 fps clock), the runner confirms on the page's final
beep and presses A one frame before each landing; the bounce count is read from Blooper's HP in RAM and typed into the
page (its try log and calibration).
DIAGNOSTIC: each rung reloads states/blooper_pb.st and writes a random seed (an unknown fight, as after reloading a
save); action commands on (the save is from before the Lucky Star).
Runner model: confirm on the frame of the final beep + OFFSET (per rung, from RUNGS 'K:offset').
usage: (from anywhere) DISPLAY=:93 M64P_GFX=<glide64mk2 .so> M64P_DATA=<dir with Glide64mk2.ini> python3 hpbm_run.py OUT SEED
env RUNGS='12:0,15:0,18:0,15:1'"""
import subprocess, sys, os, io, json, random, base64
from PIL import Image, ImageFilter
HPBM_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import SEED, SEED2
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True); rnd = random.Random(int(sys.argv[2], 16))
FIGHT = os.environ.get('FIGHT', 'blooper'); STATE = 'states/blooper_pb.st' if FIGHT == 'blooper' else os.environ.get('FB2STATE', 'states/fb2_t7like_pb.st')
LAND = (lambda n: 50 + 26 * n) if FIGHT == 'blooper' else (lambda n: 44 + 27 * n)      # press 1 frame before landing n+1
os.environ['HPBM_SET'] = json.dumps(dict(json.loads(os.environ.get('HPBM_SET', '{}')), fight=FIGHT))
RUNGS = [tuple(int(x) for x in r.split(':')) for r in os.environ.get('RUNGS', '12:0,15:0,18:0,15:1').split(',')]
FMS = 1001 / 30
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hpbm%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
node = subprocess.Popen(['node', os.path.join(HPBM_DIR, "hpbm_live.js")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
def page(o):
    node.stdin.write(json.dumps(o) + '\n'); node.stdin.flush(); l = node.stdout.readline()
    if not l: raise RuntimeError('page host died')
    return json.loads(l)
mj = open(OUT + '/run.mjpeg', 'wb'); frames = []
VF = [0]; R = [None]
def grab():
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '640x480!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    im = Image.frombytes('RGB', (640, 480), raw).filter(ImageFilter.GaussianBlur(0.5))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=85); jpg = b.getvalue(); mj.write(jpg); return jpg
def hp(): return e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)
def step(btn=0, note=None):
    e.step(btn, 0, 0, 2); VF[0] += 1
    r = page({'f': VF[0], 'jpg': base64.b64encode(grab()).decode()}); R[0] = r
    frames.append({'f': VF[0], 'seed': e.u32(SEED), 'btn': btn, 'hp': hp(), 'bs': bstate(e), 'lock': r['lock'], 'shines': r['shines'], 'plan': r['plan'], 'head': r['head'], 'note': note, 'waited': r['waited']})
    return r
T0 = page({'cmd': 'eval', 'js': 'window.__t0'})['r']
events = []
def rung(K, OFFSET):
    e.load(STATE); e.step(0, 0, 0, 2)
    s = rnd.getrandbits(32); e.w32(SEED, s); e.w32(SEED2, s)            # DIAGNOSTIC: unknown fight (random seed)
    e.w8(PLAYER_DATA + 0xA, 1)                                          # DIAGNOSTIC: action commands on
    h0 = hp(); page({'cmd': 'eval', 'js': 'window.__hpbm.setK(%d); (function(){const el=document.getElementById("s-hp"); el.value=%d; el.dispatchEvent(new Event("change"));})()' % (K, h0)})
    f0 = VF[0]; print('== %s rung K=%d offset %+d seed %08x enemy HP %d' % (FIGHT, K, OFFSET, s, h0), flush=True)
    lockF = None; waited = 0
    for i in range(6000):
        r = R[0]; P = r and r.get('plan')
        if r and r['lock'] and lockF is None: lockF = VF[0] - f0; print('   lock after %d frames (%.1f s), search pause %d ms' % (lockF, lockF * FMS / 1000, waited), flush=True)
        if P and P['tPress'] > r['t'] + FMS:
            at = int(round((P['tPress'] - T0) / FMS)) + OFFSET
            if at > VF[0] + 1:
                while VF[0] + 1 < at: step(); Q = R[0].get('plan')
                Q = R[0].get('plan')
                if not Q or Q['tPress'] != P['tPress']: continue
                c = VF[0] + 1; step(A, 'confirm')
                press = {c + LAND(n) for n in range(40)}; hits = 0; last = hp()
                for j in range(1300):
                    st = bstate(e)
                    step(A if (VF[0] + 1) in press and st in (17, 18, 19) else 0, 'bounce')
                    h = hp()
                    if h < last: hits += 1
                    last = h
                    if j > 60 and st not in (17, 18, 19) and bstate(e) not in (17, 18, 19): break
                for j in range(30): step()
                lg = page({'cmd': 'eval', 'js': 'window.__hpbm.st.awaiting = window.__hpbm.st.awaiting || window.__hpbm.st.plan; window.__hpbm.st.plan = null; window.__hpbm.logTry(%d); window.__hpbm.st.tries[window.__hpbm.st.tries.length-1]' % hits})['r']
                ev = {'K': K, 'offset': OFFSET, 'seed': s, 'lock_frames': lockF, 'planned': P['count'], 'd': P['d'], 'got': hits, 'near': P['near'], 'try': lg, 'confirm_vf': c, 'hp_before': h0, 'hp_after': hp()}
                events.append(ev); json.dump({'events': events, 'frames': frames, 'T0': T0}, open(OUT + '/hpbm.json', 'w')); print('   RESULT planned %d got %d (target %d) implied %s' % (P['count'], hits, K, lg['implied']), flush=True)
                return ev
        r = step(); waited += r['waited']
    events.append({'K': K, 'noplan': True}); print('   no plan', flush=True)
for K, off in RUNGS: rung(K, off)
mj.close()
lg = page({'cmd': 'log'})
json.dump({'events': events, 'frames': frames, 'page': lg, 'T0': T0}, open(OUT + '/hpbm.json', 'w'))
print('CAL', json.dumps(lg['cal'])); print('SUMMARY', lg['summary']); print('errs', lg['errs'], flush=True)
node.stdin.close()
