"""screenshot each saved per-frame state (s%04d.st) in a video-enabled emulator: load, step one neutral frame,
capture to f%04d.png, delete the state. usage: render_states.py <dir>"""
import glob, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
d = sys.argv[1]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rst')
for sp in sorted(glob.glob(os.path.join(d, 's*.st'))):
    k = int(os.path.basename(sp)[1:5])
    e.load(sp); e.step(0, 0, 0, 2)
    subprocess.run(['import', '-window', 'root', os.path.join(d, 'f%04d.png' % k)], check=True)
    os.remove(sp)
