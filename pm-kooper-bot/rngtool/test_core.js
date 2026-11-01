const R = require('./pmrng_core.js');
const fs = require('fs');
// 1) Time Out table vs the emulator-validated pattern (first-state seeds, coin at frame 1, confirm 14+d)
for (const [sd, exp] of [[0x12345678, 'SS....SSS.S...S...S.S..S..S.S....S.....S'], [0x31415926, '........S..SSSSSS..SS..S......SS.S......'], [0x0badf00d, '....SS.....S.........S..S..S.SS..S..S...']]) {
  let p = ''; for (let d = 0; d < 40; d++) p += R.timeOutRoll(sd, 1, 14 + d, 0) <= 30 ? 'S' : '.';
  console.log(sd.toString(16), p === exp ? 'MATCH' : 'MISMATCH ' + p);
}
// 2) seed search speed on the recorded coin pattern (true seed f99b3efc)
const draws = JSON.parse(fs.readFileSync('../data/coin_pattern_2302.json'));
const pat = draws.slice(0, 45).map(d => d.shine ? 'S' : '.').join('');
const t0 = Date.now(); const span = 1 << 26;
const hits = R.searchRange(pat, 0, span, 8);
const dt = (Date.now() - t0) / 1000;
console.log('searched 2^26 seeds in', dt.toFixed(2), 's -> full 2^32 single thread ~', (dt * 64).toFixed(0), 's');
console.log('true seed matches:', R.matches(0xf99b3efc, pat), 'pattern', pat);
