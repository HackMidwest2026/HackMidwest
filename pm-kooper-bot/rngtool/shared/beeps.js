//@ Shared by the Time Out Timer (page_template.html) and the High Power Bounce Manipulator (powerbounce/hpbm_template.html).
//@ Web Audio beeps scheduled on the performance.now() clock. Inlined at build time (shared/inline.py); //@ lines are dropped.
let ac = null;
function audio() { if (!ac) { try { ac = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} } if (ac && ac.state === 'suspended') ac.resume(); return ac; }
function beepAt(perfMs, freq, dur) {
  const a = audio(); if (!a) return;
  const t = a.currentTime + (perfMs - performance.now()) / 1000; if (t < a.currentTime) return;
  const o = a.createOscillator(), g = a.createGain(); o.frequency.value = freq; o.type = 'square';
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.25, t + 0.005); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(a.destination); o.start(t); o.stop(t + dur + 0.02);
  beeps.push(o);
}
let beeps = [];
function cancelBeeps() { if (beeps.length && typeof slog === 'function') slog('beepsCancelled', { n: beeps.length }); beeps.forEach(o => { try { o.stop(); } catch (e) {} }); beeps = []; }
