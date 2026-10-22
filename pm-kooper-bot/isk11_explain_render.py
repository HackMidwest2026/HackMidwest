"""Video-enabled screenshotter for isk11_explain_record.py: load each DIR/s%05d.st, step one frame, grab the X
screen to DIR/f%05d.png, delete the state. Exits when DIR/DONE exists and no states remain. usage: ... DIR"""
import glob, os, subprocess, sys, time
from emu import Emu
d = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ierr%d' % os.getpid())
while True:
    ss = sorted(glob.glob(os.path.join(d, 's*.st')))
    if not ss:
        if os.path.exists(os.path.join(d, 'DONE')): break
        time.sleep(0.5); continue
    for sp in ss:
        try:
            k = int(os.path.basename(sp)[1:6]); time.sleep(0.05)
            e.load(sp); e.step(0, 0, 0, 2)
            subprocess.run(['import', '-window', 'root', os.path.join(d, 'f%05d.png' % k)], check=True)
            os.remove(sp)
        except Exception as ex:
            print('skip', sp, ex)
