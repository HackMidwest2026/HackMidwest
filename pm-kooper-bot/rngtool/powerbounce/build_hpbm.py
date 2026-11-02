"""Build the High Power Bounce Manipulator: high_power_bounce_manipulator_standalone.html (open from disk, camera mode) and
the claude.ai version, which carries the standalone file (base64) for its Save for OBS mode button. Same shared capture,
coin-detector and beep code as the Time Out Timer (shared/inline.py), plus pmrng_core.js and the boss models."""
import base64, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'shared')); from inline import inline
D = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/hpbm'
os.makedirs(D, exist_ok=True)
t = inline(open(os.path.join(HERE, 'hpbm_template.html')).read())
core = open(os.path.join(ROOT, 'pmrng_core.js')).read(); bl = open(os.path.join(HERE, 'blmodel.js')).read(); fb = open(os.path.join(HERE, 'fb2model.js')).read()
for x in (core, bl, fb): assert '</script' not in x
standalone = t.replace('/*CORE*/', core).replace('/*BLMODEL*/', bl).replace('/*FB2MODEL*/', fb)
open(os.path.join(D, 'high_power_bounce_manipulator_standalone.html'), 'w').write(standalone)
b64 = base64.b64encode(standalone.encode()).decode()
art = standalone.replace('<script id="core-src">', '<script type="text/plain" id="standalone">' + b64 + '</script>\n<script id="core-src">', 1)
open(os.path.join(D, 'high_power_bounce_manipulator.html'), 'w').write(art)
print('standalone', len(standalone), 'artifact', len(art))
