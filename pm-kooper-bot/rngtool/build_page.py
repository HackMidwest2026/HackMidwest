"""Build the Time Out Timer pages: timeout_timer_standalone.html (open from disk for OBS mode) and the claude.ai
version, which also carries the standalone file (base64) for its Save for OBS mode button."""
import base64, os
D = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer'
os.makedirs(D, exist_ok=True)
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'page_template.html')).read()
core = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pmrng_core.js')).read()
assert '</script' not in core
standalone = t.replace('/*CORE*/', core)
open(os.path.join(D, 'timeout_timer_standalone.html'), 'w').write(standalone)
b64 = base64.b64encode(standalone.encode()).decode()
art = standalone.replace('<script id="core-src">', '<script type="text/plain" id="standalone">' + b64 + '</script>\n<script id="core-src">', 1)
open(os.path.join(D, 'timeout_timer.html'), 'w').write(art)
print('standalone', len(standalone), 'artifact', len(art))
