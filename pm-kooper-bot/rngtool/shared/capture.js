//@ Shared by both pages: camera / window capture (OBS Virtual Camera only), background frame reading, frame timestamps,
//@ box sampling and the automatic shine threshold. Needs a global V (capture state), $, num, audio, onFrame and the
//@ cam-* / cap-target elements. Inlined at build time (shared/inline.py); //@ lines are dropped.
function camMsg(t) { $('cam-msg').textContent = t; }
async function listCams() {
  try {
    const ds = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput'); const sel = $('cam-sel'), cur = sel.value;
    const obs = ds.filter(d => /obs/i.test(d.label));
    sel.innerHTML = '<option value="window">A window (OBS projector, no Virtual Camera)</option>' +
      (obs.length ? obs.map(d => '<option value="' + d.deviceId + '">' + d.label.replace(/</g, '&lt;') + '</option>').join('') : '<option value="">OBS Virtual Camera</option>');
    sel.value = [...sel.options].some(o => o.value === cur) ? cur : (cur === '' && obs.length ? obs[0].deviceId : 'window');
  } catch (e) {}
}
const VIDEO = { width: { ideal: 1280, max: 1920 }, height: { ideal: 720, max: 1080 }, frameRate: { ideal: 60 } };
async function openCamera(id) {
  // only ever keep the OBS Virtual Camera open: a capture card opened here would be taken away from OBS
  let s = await navigator.mediaDevices.getUserMedia({ video: Object.assign({}, VIDEO, id ? { deviceId: { exact: id } } : {}) });
  const label = s.getVideoTracks()[0].label || '';
  if (/obs/i.test(label)) return s;
  s.getTracks().forEach(t => t.stop());
  const obs = (await navigator.mediaDevices.enumerateDevices()).find(d => d.kind === 'videoinput' && /obs/i.test(d.label));
  if (!obs) throw { name: 'NoObsCamera', message: label };
  s = await navigator.mediaDevices.getUserMedia({ video: Object.assign({}, VIDEO, { deviceId: { exact: obs.deviceId } }) });
  return s;
}
async function startCam() {
  audio();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { camMsg('This browser view has no camera access. Use Save for OBS mode, then open the saved file in Chrome.'); return; }
  const id = $('cam-sel').value, win = id === 'window';
  try {
    V.stream = win ? await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: { ideal: 60 } }, audio: false, selfBrowserSurface: 'exclude', surfaceSwitching: 'exclude' })
                   : await openCamera(id);
  } catch (e) {
    V.stream = null;
    if (e && e.name === 'NoObsCamera') camMsg('Chrome opened "' + e.message + '", which is not the OBS Virtual Camera, so it was closed again. In OBS press Start Virtual Camera, then try again, or use the window source.');
    else if (e && e.name === 'NotReadableError') camMsg('The camera is busy or would not start. Start Virtual Camera in OBS first, or use the window source.');
    else camMsg((win ? 'Window capture' : 'Camera') + ' blocked or cancelled (' + (e && e.name || 'error') + '). Inside claude.ai this is expected: use Save for OBS mode and open the file in Chrome.');
    return;
  }
  const track = V.stream.getVideoTracks()[0];
  track.addEventListener('ended', stopCam);
  V.video.srcObject = V.stream; await V.video.play().catch(() => {});
  $('cam-start').disabled = true; $('cam-stop').disabled = false; $('cap-target').disabled = false;
  const st0 = track.getSettings ? track.getSettings() : {};
  camMsg('Watching ' + (track.label || (win ? 'a window' : 'the camera')) + (st0.width ? ' (' + st0.width + '×' + st0.height + (st0.frameRate ? ' at ' + Math.round(st0.frameRate) + ' fps' : '') + ')' : '') + '. Drag the boxes on the preview if they are not on the coin and the target name.');
  if (!win) listCams();
  V.lastVfc = performance.now(); schedule(); startBackground(track);
}
// Chrome stops video callbacks when this window is hidden or covered (e.g. behind OBS). Read frames straight from the
// track as a fallback so detection keeps running there.
function startBackground(track) {
  if (typeof MediaStreamTrackProcessor === 'undefined') return;
  let rd;
  try { V.bgTrack = track.clone(); rd = new MediaStreamTrackProcessor({ track: V.bgTrack }).readable.getReader(); } catch (e) { return; }
  (async () => {
    for (;;) {
      let r; try { r = await rd.read(); } catch (e) { break; }
      if (r.done) break;
      const fr = r.value;
      try { if (V.force === 'bg' || performance.now() - V.lastVfc > 150) { V.src = fr; onFrame(performance.now()); V.bgFrames = (V.bgFrames || 0) + 1; } }
      finally { V.src = null; fr.close(); }
    }
  })();
}
function stopCam() { if (V.stream) V.stream.getTracks().forEach(t => t.stop()); if (V.bgTrack) V.bgTrack.stop(); V.stream = null; V.bgTrack = null; $('cam-start').disabled = false; $('cam-stop').disabled = true; camMsg('Stopped.'); }
// frame timestamp on the performance.now() clock (the beeps are scheduled on it). Some capture sources report
// captureTime on another clock; anything more than a second away from now is not trusted.
function frameTime(now, meta) {
  const pn = performance.now(), ok = x => typeof x === 'number' && x > 0 && Math.abs(x - pn) < 1000;
  return ok(meta.captureTime) ? meta.captureTime : ok(meta.expectedDisplayTime) ? meta.expectedDisplayTime : now;
}
function schedule() {
  if (!V.stream) return;
  if (V.video.requestVideoFrameCallback) V.video.requestVideoFrameCallback((now, meta) => { if (V.force !== 'bg') { V.lastVfc = performance.now(); onFrame(frameTime(now, meta)); } schedule(); });
  else requestAnimationFrame(() => { V.lastVfc = performance.now(); onFrame(performance.now()); schedule(); });
}
function dims() { return V.src ? [V.src.displayWidth, V.src.displayHeight] : [V.video.videoWidth, V.video.videoHeight]; }
function region(b) { const [w, h] = dims(); return [b.x * w, b.y * h, Math.max(1, b.w * w), Math.max(1, b.h * h)]; }
function sample(b, ow, oh) { sctx.drawImage(V.src || V.video, ...region(b), 0, 0, ow, oh); return sctx.getImageData(0, 0, ow, oh).data; }
function median(a) { if (!a.length) return 0; const b = a.slice().sort((x, y) => x - y); return b[b.length >> 1]; }
function threshold() {
  const manual = num('wthr'); if (manual > 0) return manual;
  const normal = median(V.peaks.slice(-30)), shine = median(V.shinePeaks.slice(-10));
  if (V.shinePeaks.length >= 2 && shine > normal * 1.5) return (normal + shine) / 2;
  return Math.max(0.02, normal * 2.5 + 0.005);
}
