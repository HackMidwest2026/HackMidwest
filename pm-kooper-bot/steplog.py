"""Run a script while logging every emulator step, following savestate saves/loads so the final log is the single
input sequence that leads from the base state to wherever the script ends (retries that reload a state drop out).
Logs persist across processes in DB (json: state path -> step list). usage: steplog.py DB SCRIPT ARGS..."""
import json, os, runpy, sys
import emu
db_path = sys.argv[1]; script = sys.argv[2]; sys.argv = [script] + sys.argv[3:]
db = json.load(open(db_path)) if os.path.exists(db_path) else {}
cur = []
o_step, o_save, o_load = emu.Emu.step, emu.Emu.save, emu.Emu.load
def step(self, b=0, x=0, y=0, n=1):
    o_step(self, b, x, y, n); cur.append([b, x, y, n])
def save(self, path):
    o_save(self, path); db[os.path.abspath(path)] = list(cur)
    json.dump(db, open(db_path, 'w'))
def load(self, path, frame=0):
    global cur
    o_load(self, path, frame); cur = list(db.get(os.path.abspath(path), []))
emu.Emu.step, emu.Emu.save, emu.Emu.load = step, save, load
try:
    runpy.run_path(script, run_name='__main__')
finally:
    db['__last__'] = list(cur); json.dump(db, open(db_path, 'w'))
