import {
  AlertTriangle,
  ArrowUpRight,
  Car,
  CheckCircle2,
  Compass,
  Cpu,
  Droplets,
  Lightbulb,
  MapPin,
  Search,
  Send,
  Sparkles,
  Trash2,
  TreePine,
  Upload,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, newRunId, subscribe } from '../api.js'
import { CATEGORY_META, formatBytes, issueCode, OPEN_STATUSES, shortAddress, statusMeta, tierMeta } from '../lib/display.js'
import AddressAutocomplete from './AddressAutocomplete.jsx'
import AgentTrace from './AgentTrace.jsx'
import CityMap from './CityMap.jsx'


const PICKER = [
  { id: '', label: 'Auto', icon: Sparkles },
  { id: 'streets', label: 'Pothole', icon: AlertTriangle },
  { id: 'traffic_lighting', label: 'Light', icon: Lightbulb },
  { id: 'water', label: 'Water', icon: Droplets },
  { id: 'trash', label: 'Trash', icon: Trash2 },
  { id: 'parks_trees', label: 'Tree', icon: TreePine },
]

const FILTERS = ['streets', 'water', 'traffic_lighting', 'trash']

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = reject
    r.readAsDataURL(file)
  })
}

export default function CitizenPortal({ meta, data, selectedIssue, onSelectIssue, onSwitchToDispatch }) {
  const { issues, crews } = data
  // Optional examples from the configured city profile (the sample data is Kansas City).
  const exampleReport = meta.city?.examples?.report_text
  const exampleAddress = meta.city?.examples?.address
  const [view, setView] = useState(null) // current map center, used to bias address search
  const [formOpen, setFormOpen] = useState(true)
  const [categoryHint, setCategoryHint] = useState('')
  const [address, setAddress] = useState('')
  const [pin, setPin] = useState(null)
  const [text, setText] = useState('')
  const [photo, setPhoto] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)
  const [nearby, setNearby] = useState([])
  const [filter, setFilter] = useState('all')
  const [layers, setLayers] = useState({ p1Heatmap: false, fieldTelemetry: false, wardGrid: false })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [events, setEvents] = useState([])
  const runId = useRef(null)
  const fileInput = useRef(null)

  useEffect(
    () =>
      subscribe({
        onTrace: (e) => {
          if (e.run_id && e.run_id === runId.current) setEvents((prev) => [...prev, e])
        },
      }),
    [],
  )

  // "Matching nearby reports" preview whenever the pin moves.
  useEffect(() => {
    if (!pin) return setNearby([])
    let cancelled = false
    api
      .nearby(pin.lat, pin.lng, text)
      .then((list) => !cancelled && setNearby(list))
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [pin?.lat, pin?.lng]) // eslint-disable-line react-hooks/exhaustive-deps

  async function placePin(latlng, knownAddress) {
    const p = { lat: +latlng.lat.toFixed(6), lng: +latlng.lng.toFixed(6) }
    setPin(p)
    setFormOpen(true)
    if (knownAddress) return setAddress(knownAddress)
    try {
      setAddress((await api.reverseGeocode(p.lat, p.lng)).address)
    } catch {
      setAddress(`${p.lat}, ${p.lng}`)
    }
  }

  async function findAddress(q = address || text) {
    setError(null)
    if (!q.trim()) return
    const g = await api.geocode(q, pin || view || meta.center)
    if (g.found) placePin({ lat: g.lat, lng: g.lng }, g.address)
    else setError(g.reason)
  }

  function useMyLocation() {
    navigator.geolocation?.getCurrentPosition(
      (pos) => placePin({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setError('Could not get your location. Tap the map or type a cross street.'),
    )
  }

  function choosePhoto(file) {
    if (photoPreview) URL.revokeObjectURL(photoPreview)
    setPhoto(file || null)
    setPhotoPreview(file ? URL.createObjectURL(file) : null)
    // Clear the native input too, so picking the same file again still fires onChange.
    if (!file && fileInput.current) fileInput.current.value = ''
  }

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setEvents([])
    if (!text.trim() && !photo) return setError('Describe the problem in a few words, or attach a photo.')
    runId.current = newRunId()
    setBusy(true)
    try {
      const body = {
        text,
        client_run_id: runId.current,
        ...(categoryHint && { category_hint: categoryHint }),
        ...(pin && { lat: pin.lat, lng: pin.lng, address }),
      }
      if (photo) body.photo = await readAsDataUrl(photo)
      const r = await api.submitReport(body)
      setResult(r)
      data.replaceIssue(r.issue)
      onSelectIssue(r.issue.issue_id)
      // Ready for the next report; the confirmation and agent trace stay visible.
      clearFields()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  /** Empty every input: description, location, pin, photo, category and the nearby-incident hint. */
  function clearFields() {
    setText('')
    setAddress('')
    setPin(null)
    setNearby([])
    choosePhoto(null)
    setCategoryHint('')
  }

  function resetForm() {
    clearFields()
    setResult(null)
    setEvents([])
    setError(null)
  }

  const openIssues = issues.filter((i) => OPEN_STATUSES.has(i.status))
  const count = (cat) => openIssues.filter((i) => i.category === cat).length
  const sel = selectedIssue
  const assignedCrew = sel?.assigned_crew ? crews.find((c) => c.crew_id === sel.assigned_crew) : null
  const nearest = nearby[0]

  return (
    <div className="relative w-full h-[calc(100vh-64px)] overflow-hidden bg-[#FAF8FF]">
      {/* Top overlay row: report button (when the card is closed) + category filters.
          Kept clear of the map controls on the right and, on wider screens, of the report card. */}
      <div
        className={`absolute top-3 right-14 z-[1000] flex items-center gap-2 pointer-events-none ${
          formOpen ? 'left-3 md:left-[26rem]' : 'left-3 md:left-4'
        }`}
      >
        {!formOpen && (
          <button
            onClick={() => setFormOpen(true)}
            className="pointer-events-auto shrink-0 bg-[#00236F] hover:bg-[#1E3A8A] text-white px-3 py-2 rounded-lg text-xs font-semibold shadow-lg flex items-center gap-2"
          >
            <AlertTriangle className="w-4 h-4" />
            <span className="hidden sm:inline">Report an Issue</span>
            <span className="sm:hidden">Report</span>
          </button>
        )}
      <div className="pointer-events-auto min-w-0 lg:mx-auto flex items-center gap-1.5 bg-white/90 backdrop-blur-md p-1 rounded-full shadow-sm border border-slate-200/90 overflow-x-auto">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 text-xs font-semibold rounded-full whitespace-nowrap transition-colors ${filter === 'all' ? 'bg-[#00236F] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
        >
          All Incidents ({openIssues.length})
        </button>
        {FILTERS.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-3 py-1 text-xs font-medium rounded-full whitespace-nowrap flex items-center gap-1.5 transition-colors ${
              filter === cat ? 'bg-[#00236F] text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${CATEGORY_META[cat].dot}`} />
            <span>
              {CATEGORY_META[cat].filterLabel} ({count(cat)})
            </span>
          </button>
        ))}
      </div>
      </div>

      <div className="w-full h-full">
        <CityMap
          mode="citizen"
          meta={meta}
          issues={issues}
          crews={crews}
          selectedId={sel?.issue_id}
          onSelect={onSelectIssue}
          reportPin={formOpen && !result ? pin : null}
          onReportPin={formOpen ? (ll) => placePin(ll) : undefined}
          layers={layers}
          onToggleLayer={(k) => setLayers((l) => ({ ...l, [k]: !l[k] }))}
          filterCategory={filter}
          flyTo={pin}
          zoom={meta.city?.default_zoom || 12}
          onViewChange={setView}
        />
      </div>

      {/* Report an Issue card */}
      {formOpen ? (
        <div className="absolute z-[1000] inset-x-0 bottom-0 top-[42%] rounded-t-2xl md:inset-auto md:top-3 md:left-4 md:bottom-4 md:w-96 md:rounded-xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-2xl flex flex-col overflow-hidden animate-in md:slide-in-from-left-4">
          <div className="p-4 border-b border-slate-100 flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#00236F] flex items-center justify-center text-white shrink-0 shadow-sm">
              <AlertTriangle className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-base font-bold text-slate-900 tracking-tight leading-tight">Report an Issue</h2>
              <p className="text-xs text-slate-500 mt-0.5">AI agents triage it and route it to the right city crew</p>
              <p className="text-[11px] text-[#2563EB] mt-0.5 md:hidden">Tap the map above to drop your pin</p>
            </div>
            <button onClick={() => setFormOpen(false)} title="Close form to explore the map" className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100">
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={submit} className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {/* 1. Category */}
            <div>
              <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2 font-mono">1. Category</label>
              <div className="grid grid-cols-6 gap-1.5">
                {PICKER.map(({ id, label, icon: Icon }) => {
                  const on = categoryHint === id
                  return (
                    <button
                      key={label}
                      type="button"
                      onClick={() => setCategoryHint(id)}
                      title={id ? `Hint: ${label}` : 'Let the Intake agent decide from your description'}
                      className={`flex flex-col items-center justify-center py-2.5 px-1 rounded-lg border text-center transition-all ${
                        on
                          ? 'border-[#00236F] bg-blue-50/50 text-[#00236F] ring-1 ring-[#00236F] font-semibold'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <Icon className={`w-4 h-4 mb-1 ${on ? 'text-[#00236F]' : 'text-slate-500'}`} />
                      <span className="text-[11px] truncate w-full">{label}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 2. Location */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider font-mono">2. Pin Location</label>
                <button type="button" onClick={useMyLocation} className="text-[11px] text-[#2563EB] hover:text-[#1E3A8A] font-medium flex items-center gap-1 hover:underline">
                  <Compass className="w-3.5 h-3.5" />
                  <span>Use my location</span>
                </button>
              </div>
              <div className="relative flex gap-1.5">
                <AddressAutocomplete
                  value={address}
                  onChange={setAddress}
                  onSelect={(sug) => placePin({ lat: sug.lat, lng: sug.lng }, sug.address)}
                  onSubmitText={() => findAddress()}
                  near={pin || view || meta.center}
                  inputClassName="w-full pl-8 pr-3 py-2 bg-slate-50/80 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] outline-none"
                  placeholder={exampleAddress ? `Address or cross streets, e.g. ${exampleAddress}` : 'Street address or cross streets'}
                />
                <button type="button" onClick={() => findAddress()} title="Find on map" className="px-2.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50">
                  <Search className="w-3.5 h-3.5" />
                </button>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">ⓘ Tap the map or drag the pin to fine-tune the exact spot</p>
            </div>

            {/* 3. Evidence & AI triage */}
            <div>
              <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5 font-mono">3. Evidence</label>
              <input ref={fileInput} type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => choosePhoto(e.target.files?.[0])} />
              {photo ? (
                <div className="border border-slate-200 rounded-lg p-2.5 bg-slate-50/60 mb-2 relative">
                  <div className="flex items-start gap-2.5">
                    <img src={photoPreview} alt="Attached evidence" className="w-12 h-12 rounded object-cover border border-slate-200" />
                    <div className="flex-1 min-w-0 pr-6">
                      <div className="text-xs font-medium text-slate-800 truncate font-mono">
                        {photo.name} ({formatBytes(photo.size)})
                      </div>
                      <div className="mt-1 inline-flex items-center gap-1 text-[10px] text-[#0D9488] font-semibold bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200/60">
                        <Sparkles className="w-3 h-3" />
                        <span>Attached for the dispatcher</span>
                      </div>
                    </div>
                    <button type="button" onClick={() => choosePhoto(null)} className="absolute top-2 right-2 text-slate-400 hover:text-slate-600 p-0.5" title="Remove photo">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => fileInput.current?.click()}
                  className="w-full border-2 border-dashed border-slate-200 hover:border-slate-300 rounded-lg p-3 text-center mb-2 bg-slate-50/40"
                >
                  <Upload className="w-4 h-4 mx-auto text-slate-400 mb-1" />
                  <span className="text-[11px] text-slate-600">Click to attach photo evidence (optional)</span>
                </button>
              )}

              <textarea
                rows={3}
                value={text}
                onChange={(e) => {
                  setText(e.target.value)
                  if (result) {
                    setResult(null)
                    setEvents([])
                  }
                }}
                placeholder="Describe the issue in your own words: hazards, what happened, how bad it is…"
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] outline-none resize-none leading-relaxed"
              />
              {!text && exampleReport && (
                <button
                  type="button"
                  onClick={() => {
                    setText(exampleReport)
                    if (!pin) findAddress(exampleReport)
                  }}
                  className="text-[11px] text-[#2563EB] hover:underline"
                >
                  Use the demo example
                </button>
              )}

              {nearest && !result && (
                <div className="mt-2.5 p-2.5 bg-[#FFF7ED] border border-[#FED7AA] rounded-lg text-slate-800 text-[11px] flex items-start gap-2">
                  <ArrowUpRight className="w-4 h-4 text-[#EA580C] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-900">
                      {nearby.length} open incident{nearby.length === 1 ? '' : 's'} within 120 m.
                    </span>{' '}
                    Nearest: <span className="font-mono font-bold text-[#EA580C]">{issueCode(nearest.issue_id)}</span> ({nearest.summary.slice(0, 48)}
                    {nearest.summary.length > 48 ? '…' : ''}, {nearest.report_count} report{nearest.report_count === 1 ? '' : 's'}). If it's the same problem, the Dedup agent links your
                    report to it.
                  </div>
                </div>
              )}
            </div>

            {error && <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg">{error}</div>}

            {result && (
              <div className="p-2.5 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg space-y-1.5 animate-in">
                <div className="flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>{result.merged ? `Merged into ${issueCode(result.issue.issue_id)}` : `New incident ${issueCode(result.issue.issue_id)} opened`}</span>
                </div>
                <div className="text-[11px] leading-snug">
                  {result.merged
                    ? `Your report joins ${result.issue.report_count - 1} other report${result.issue.report_count === 2 ? '' : 's'} about the same problem. `
                    : ''}
                  Priority <span className={`px-1 rounded font-mono font-bold ${tierMeta(result.issue.priority_tier).badge}`}>{result.issue.priority_tier}</span> (
                  {result.issue.priority_score}/100), recommended for <strong>{result.issue.recommended_department_name}</strong>. A dispatcher approves every assignment.
                </div>
                <div className="flex items-center gap-3 pt-0.5">
                  <button type="button" onClick={onSwitchToDispatch} className="font-semibold underline hover:text-black">
                    View in Dispatch &rarr;
                  </button>
                  <button type="button" onClick={resetForm} className="text-emerald-700 hover:underline">
                    Report another
                  </button>
                </div>
              </div>
            )}

            {(busy || events.length > 0) && (
              <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-2.5">
                <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-700 font-mono uppercase tracking-wider">
                  <Cpu className="w-3.5 h-3.5 text-[#0D9488]" />
                  Strands agents at work
                </div>
                <AgentTrace events={events} compact className="max-h-56" emptyText="Starting the pipeline…" />
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 px-4 bg-[#00236F] hover:bg-[#1E3A8A] active:scale-[0.99] disabled:opacity-70 text-white rounded-lg font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2"
            >
              {busy ? (
                <span>Agents triaging your report…</span>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Incident to CityCare</span>
                </>
              )}
            </button>
            {/* The sheet covers Leaflet's attribution on phones, so repeat it here. */}
            <p className="md:hidden text-center text-[10px] text-slate-400">Map data © OpenStreetMap contributors</p>
          </form>
        </div>
      ) : null}

      {/* Selected incident card */}
      {sel && (
        <div
          className={`absolute z-[1000] bottom-6 inset-x-3 sm:inset-x-auto sm:right-4 sm:bottom-6 sm:w-80 bg-white/95 backdrop-blur-md rounded-xl border border-slate-200/90 shadow-xl p-3.5 text-xs animate-in ${
            formOpen ? 'hidden md:block' : ''
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <div className="font-mono font-bold text-slate-800 text-xs">{issueCode(sel.issue_id)} Selected</div>
            <div className="flex items-center gap-1.5">
              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${statusMeta(sel.status).pill}`}>{statusMeta(sel.status).label}</span>
              <button onClick={() => onSelectIssue(null)} className="text-slate-400 hover:text-slate-700" aria-label="Close">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
          <div className="flex items-start gap-2.5 mt-2">
            <div className={`w-7 h-7 rounded-md flex items-center justify-center text-white shrink-0 shadow-sm ${tierMeta(sel.priority_tier).dot}`}>
              {(() => {
                const Icon = (CATEGORY_META[sel.category] || CATEGORY_META.other).icon
                return <Icon className="w-4 h-4" />
              })()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-bold text-slate-900 text-xs leading-tight">{sel.summary}</div>
              <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                <span className="truncate">{shortAddress(sel.address)}</span>
              </div>
            </div>
          </div>
          <div className="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-600 flex items-center gap-2">
            <span className="font-mono text-slate-500">{sel.neighborhood}</span>
            <span className={`px-1 rounded font-mono font-bold text-[10px] ${tierMeta(sel.priority_tier).badge}`}>{sel.priority_tier}</span>
            {assignedCrew && (
              <span className="text-[#0D9488] font-medium flex items-center gap-1 truncate">
                <Car className="w-3 h-3 shrink-0" />
                {assignedCrew.name}
              </span>
            )}
            <button onClick={onSwitchToDispatch} className="text-[#2563EB] hover:underline font-semibold ml-auto whitespace-nowrap">
              Open in Console &rarr;
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
