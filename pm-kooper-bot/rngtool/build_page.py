"""Build the Time Out Timer pages: timeout_timer_standalone.html (open from disk for OBS mode) and the claude.ai
version, which also carries the standalone file (base64) for its Save for OBS mode button."""
import base64, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared'))
from inline import inline
D = os.environ.get('TOT_OUT') or '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer'   # TOT_OUT: another folder (parallel worktrees)
os.makedirs(D, exist_ok=True)
t = inline(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'page_template.html')).read())
H = os.path.dirname(os.path.abspath(__file__))
t = t.replace('/*CHG_CAMS*/null', open(os.path.join(H, 'readouts', 'data', 'charge_cams_mario_route.json')).read().strip(), 1)
t = t.replace('/*CHG_MARIO*/null', open(os.path.join(H, 'charge_live', 'mario_ref.json')).read().strip(), 1)
t = t.replace('/*CHG_WASM*/', open(os.path.join(H, 'charge_live', 'kernel.wasm.b64')).read().strip(), 1)
t = t.replace('/*CHG_CAMS_FB2*/null', open(os.path.join(H, 'readouts', 'data', 'charge_cams_mario_fb2.json')).read().strip(), 1)
t = t.replace('/*CHG_MARIO_FB2*/null', open(os.path.join(H, 'charge_live', 'mario_ref_fb2.json')).read().strip(), 1)
core = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pmrng_core.js')).read()
assert '</script' not in core
standalone = t.replace('/*CORE*/', core)
open(os.path.join(D, 'timeout_timer_standalone.html'), 'w').write(standalone)
b64 = base64.b64encode(standalone.encode()).decode()
art = standalone.replace('<script id="core-src">', '<script type="text/plain" id="standalone">' + b64 + '</script>\n<script id="core-src">', 1)
open(os.path.join(D, 'timeout_timer.html'), 'w').write(art)
print('standalone', len(standalone), 'artifact', len(art))
