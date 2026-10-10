import { useEffect, useRef, useState } from 'react'
import { api, subscribe } from '../api.js'
import IssueMap from './IssueMap.jsx'
import TracePanel from './TracePanel.jsx'

const EXAMPLE = 'Huge pothole on Troost near 39th, almost wrecked my car'

function newRunId() {
  return crypto.randomUUID ? crypto.randomUUID() : `run-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = reject
    r.readAsDataURL(file)
  })
}

export default function ResidentView({ meta }) {
  const [text, setText] = useState('')
  const [pin, setPin] = useState(null)
  const [address, setAddress] = useState('')
  const [photo, setPhoto] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [events, setEvents] = useState([])
  const runId = useRef(null)

  useEffect(
    () =>
      subscribe({
        onTrace: (e) => {
          if (e.run_id && e.run_id === runId.current) setEvents((prev) => [...prev, e])
        },
      }),
    [],
  )

  async function dropPin(latlng) {
    const p = { lat: +latlng.lat.toFixed(6), lng: +latlng.lng.toFixed(6) }
    setPin(p)
    try {
      setAddress((await api.reverseGeocode(p.lat, p.lng)).address)
    } catch {
      setAddress('')
    }
  }

  async function locateFromText() {
    const g = await api.geocode(text)
    if (g.found) {
      setPin({ lat: g.lat, lng: g.lng })
      setAddress(g.address)
    } else setError(g.reason)
  }

  function useMyLocation() {
    navigator.geolocation?.getCurrentPosition(
      (pos) => dropPin({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setError('Could not get your location. Tap the map instead.'),
    )
  }

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setEvents([])
    if (!text.trim()) return setError('Tell us what the problem is.')
    runId.current = newRunId()
    setBusy(true)
    try {
      const body = { text, client_run_id: runId.current, ...(pin && { lat: pin.lat, lng: pin.lng }), ...(address && { address }) }
      if (photo) body.photo = await readAsDataUrl(photo)
      const r = await api.submitReport(body)
      setResult(r)
      if (!pin) setPin({ lat: r.report.lat, lng: r.report.lng })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const issue = result?.issue
  return (
    <main className="resident">
      <section className="panel resident-form">
        <h1>Report a problem</h1>
        <p className="muted">Potholes, streetlights, trash, water, trees… Describe it in your own words and drop a pin.</p>
        <form onSubmit={submit}>
          <label htmlFor="report-text">What's wrong?</label>
          <textarea id="report-text" rows={3} value={text} onChange={(e) => setText(e.target.value)} placeholder={EXAMPLE} />
          {!text && (
            <button type="button" className="link" onClick={() => setText(EXAMPLE)}>
              Use the demo example
            </button>
          )}

          <label>Where? Tap the map{pin ? '' : ', or name a cross street above'}.</label>
          <IssueMap center={pin || meta.center} pin={pin} onMapClick={dropPin} flyTo={pin} zoom={pin ? 15 : 12} className="map-small" />
          <div className="row">
            <span className="address">{address || (pin ? `${pin.lat}, ${pin.lng}` : 'No pin yet')}</span>
            <button type="button" className="secondary small" onClick={locateFromText} disabled={!text}>
              Find streets in text
            </button>
            <button type="button" className="secondary small" onClick={useMyLocation}>
              My location
            </button>
          </div>

          <label htmlFor="report-photo">Photo (optional)</label>
          <input id="report-photo" type="file" accept="image/*" capture="environment" onChange={(e) => setPhoto(e.target.files?.[0] || null)} />

          {error && <div className="banner error">{error}</div>}
          <button type="submit" className="primary" disabled={busy}>
            {busy ? 'Agents working…' : 'Submit report'}
          </button>
        </form>

        {issue && (
          <div className="result-card">
            <h2>Thanks, we've got it.</h2>
            <p>
              {result.merged
                ? `Your report was merged with ${issue.report_count - 1} other report${issue.report_count === 2 ? '' : 's'} about the same problem`
                : 'Your report opened a new issue'}{' '}
              <strong>#{issue.issue_id}</strong>.
            </p>
            <p>
              Priority <span className={`tier tier-${issue.priority_tier}`}>{issue.priority_tier}</span> ({issue.priority_score}/100). Recommended for{' '}
              <strong>{issue.recommended_department_name}</strong>. A city dispatcher will review it shortly.
            </p>
          </div>
        )}
      </section>
      <TracePanel events={events} title="What the agents are doing" emptyText="Submit a report to watch the agents triage it live." />
    </main>
  )
}
