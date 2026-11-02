//@ Shared by both pages: the status-bar coin detector, inlined as a FRAGMENT into each page's onFrame(t) body. It reads
//@ the coin box, keeps V.present / V.wasGone, calls coinBack(hiddenMs) when the coin returns, hudWatch(t, present), and
//@ addShine(t, true) on each shine onset; it leaves present, white and thr declared for the rest of onFrame.
//@ Inlined at build time (shared/inline.py); //@ lines are dropped.
  // coin box: gold fraction (is the coin there?) and white fraction (the shine flash)
  const d = sample(V.boxes.coin, 32, 32); let gold = 0, white = 0;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i], g = d[i + 1], b = d[i + 2];
    if (r > 200 && g > 200 && b > 190) white++;
    else if (r > 140 && g > 95 && b < 120 && r > b + 60 && g > 0.6 * r) gold++;
  }
  gold /= 1024; white /= 1024;
  // the coin counts as on screen only with the status bar's tan (and the coin's gold) around it: white alone is a
  // speech bubble (the quiz door's text sat in the coin box for ~2 minutes and looked like a coin that never shone),
  // and orange without green (g > 0.6 r) is lava glow
  const present = gold > 0.3;
  if (!present) { if (V.present) V.absentSince = t; V.presentSince = 0; if (t - V.absentSince > 400) V.wasGone = true; }
  else { if (!V.presentSince) V.presentSince = t; if (V.wasGone && t - V.presentSince > 1000) { V.wasGone = false; coinBack(V.presentSince - V.absentSince); } }
  V.present = present; hudWatch(t, present);
  const steady = present && !V.wasGone && V.presentSince && t - V.presentSince > 1000;   // shines count only on a steady coin
  // per-loop maxima of the flash level, for the automatic threshold
  if (t - V.winStart > 24 * FRAME) { if (present && !V.inShine) V.peaks.push(V.winMax); if (V.peaks.length > 60) V.peaks.shift(); V.winMax = 0; V.winStart = t; }
  if (present) V.winMax = Math.max(V.winMax, white);
  const thr = threshold();
  if (steady && !V.inShine && white > thr && t - V.lastOnset > 40 * FRAME) {
    V.inShine = true; V.lastOnset = t; V.below = 0; V.curPeak = white; V.shines++;
    (V.hist = V.hist || []).push(t); addShine(t, true);
  } else if (V.inShine) {
    V.curPeak = Math.max(V.curPeak, white);
    if (white < thr * 0.6) { if (++V.below >= 3) { V.inShine = false; V.shinePeaks.push(V.curPeak); if (V.shinePeaks.length > 20) V.shinePeaks.shift(); } } else V.below = 0;
  }
