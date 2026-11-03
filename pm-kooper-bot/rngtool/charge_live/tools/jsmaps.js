/* The page's own ray maps (charge_live.js: chgMarioShift, chgMaps) from game-frame rasters, for the native harness.
 * usage: node jsmaps.js FRAMES.u8 OUT.bin   (FRAMES.u8 from gameframes.py: 50 x 480 x 640 uint8) */
const fs = require('fs'), path = require('path'), D = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(D, 'charge_live.js'), 'utf8')
  .replace('/*CHG_CAMS*/null', fs.readFileSync(path.join(D, '..', 'readouts', 'data', 'charge_cams_mario_route.json'), 'utf8'))
  .replace('/*CHG_MARIO*/null', fs.readFileSync(path.join(D, 'mario_ref.json'), 'utf8'));
const stub = 'const $ = () => null, num = () => 0, slog = () => {}, FRAME = 1000 / 29.97, isRoute = () => false, RT = () => [], routeStep = 0, zw = {}, V = {}, R = {}, st = {};\n';
const api = new Function(stub + src + '\nreturn { chgMaps, chgMarioShift, CHG_CAMS };')();
const buf = fs.readFileSync(process.argv[2]), G = [];
for (let n = 0; n < 48; n++) G.push({ Y: new Uint8Array(buf.buffer, buf.byteOffset + n * 640 * 480, 640 * 480) });
const fr = n => ({ Y: new Uint8Array(buf.buffer, buf.byteOffset + n * 640 * 480, 640 * 480) });
let t = Date.now(); const sh = api.chgMarioShift([fr(50), fr(51), fr(0), fr(1)].map(f => f.Y)); const ms = Date.now() - t;
const dxw = Math.abs(sh.dx) >= 3 && sh.ncc > 0.6 ? sh.dx * 0.37 : 0, c = api.CHG_CAMS.centre;
t = Date.now(); const M = api.chgMaps(G, [c[0] + dxw, c[1], c[2]]); const mm = Date.now() - t;
const h = Buffer.alloc(8); h.writeInt32LE(48, 0); h.writeInt32LE(96, 4);
fs.writeFileSync(process.argv[3], Buffer.concat([h, Buffer.from(M.S.buffer), Buffer.from(M.C.buffer)]));
console.log('Mario', sh.dx.toFixed(1), 'px (ncc ' + sh.ncc.toFixed(2) + '), centre +' + dxw.toFixed(2), 'units; maps', mm, 'ms');
