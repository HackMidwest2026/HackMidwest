"""Render savestates to PNGs with the video plugin (boot 150 steps first; set DISPLAY and M64P_GFX).
usage: shot_states.py OUTDIR STATE [STATE ...]"""
import os, subprocess, sys
from emu import Emu
od = sys.argv[1]; os.makedirs(od, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ss%d' % os.getpid())
for i in range(150): e.step(0, 0, 0, 2)
for st in sys.argv[2:]:
    e.load(st); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    subprocess.run(['import', '-window', 'root', os.path.join(od, os.path.basename(st).replace('.st', '.png'))], check=True)
