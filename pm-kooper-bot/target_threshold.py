"""How far right can Laki's stale target be for the hold-up ending to still clip? From a top-right state, shift the
stale target and the fill points between it and the rock (history x < 570) by K units in RAM (positive = right),
then run the rta_holdup2 search (A + down N, stopping hammer frame, C-down frame) for each K.
usage: target_threshold.py START K [K ...]"""
import os, sys
from multiprocessing import Pool
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
HIST, PTR = 0x8010CEF8, 0x8010D17C
def run(K):
    from emu import Emu
    import rta_holdup2
    w = '/dev/shm/pmbot/tt%d' % os.getpid()
    e = Emu(os.environ['PM_ROM'], w)
    e.load(sys.argv[1]); e.step(0, 0, 0, 2)
    for i in range(40):
        if e.f32(HIST + 16 * i + 4) < 570: e.wf32(HIST + 16 * i + 4, e.f32(HIST + 16 * i + 4) + K)
    tgt = e.f32(HIST + 16 * e.u32(PTR) + 4)
    e.save(w + '/s.st')
    del e
    os.environ['START'] = w + '/s.st'
    return K, tgt, w + '/s.st'
if __name__ == '__main__':
    import subprocess
    for K in map(float, sys.argv[2:]):
        r = subprocess.run([sys.executable, '-c', 'import sys; sys.argv=%r; import target_threshold as t; print(t.run(%r))' % (sys.argv, K)], capture_output=True, text=True)
        K_, tgt, st = eval(r.stdout.strip().splitlines()[-1])
        out = subprocess.run([sys.executable, 'rta_holdup2.py', '29', '30', '31', '32', '33', '34'], capture_output=True, text=True, env=dict(os.environ, START=st)).stdout
        clips = [l for l in out.splitlines() if 'CLIP' in l]
        best = max((float(l.split('speed ')[1].split()[0]) for l in out.splitlines() if 'speed' in l), default=0)
        print('K %+5.1f  stale target x %.1f: %s' % (K, tgt, ('CLIPS (%d ways), best %.2f' % (len(clips), best)) if clips else 'no clip (best %.2f)' % best), flush=True)
