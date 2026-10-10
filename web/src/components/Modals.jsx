import { Radio, Send, Truck, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { issueCode } from '../lib/display.js'

function ModalShell({ title, icon: Icon, iconClass, onClose, width = 'max-w-md', children }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="fixed inset-0 z-[1250] bg-black/40 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className={`bg-white rounded-xl shadow-2xl border border-slate-200 w-full ${width} overflow-hidden text-xs animate-in`} onClick={(e) => e.stopPropagation()}>
        <div className="p-3.5 bg-[#00164E] text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`w-4 h-4 ${iconClass}`} />
            <span className="font-bold">{title}</span>
          </div>
          <button onClick={onClose} className="text-slate-300 hover:text-white" aria-label="Close">
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

const SUGGESTIONS = ['What are the most dangerous open issues in Midtown?', "What's most urgent in Westport?", 'How many issues are open?']

/** Supervisor channel: plain-English questions answered by the Supervisor agent. */
export function SupervisorModal({ onClose }) {
  const [log, setLog] = useState([])
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const bottom = useRef(null)

  useEffect(() => bottom.current?.scrollIntoView({ block: 'nearest' }), [log.length, busy])

  async function ask(q) {
    const text = (q ?? question).trim()
    if (!text) return
    setQuestion('')
    setBusy(true)
    setLog((l) => [...l, { who: 'you', text, at: new Date() }])
    try {
      const { answer } = await api.chat(text)
      setLog((l) => [...l, { who: 'agent', text: answer, at: new Date() }])
    } catch (e) {
      setLog((l) => [...l, { who: 'error', text: e.message, at: new Date() }])
    } finally {
      setBusy(false)
    }
  }

  const time = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return (
    <ModalShell title="Supervisor Channel: City Supervisor Agent" icon={Radio} iconClass="text-emerald-400" onClose={onClose} width="max-w-lg">
      <div className="p-4 space-y-3 h-80 overflow-y-auto">
        {log.length === 0 && (
          <div className="space-y-2">
            <p className="text-slate-500">Ask about open issues. The supervisor agent queries live data and can consult the Priority and Router agents.</p>
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => ask(s)} className="block w-full text-left p-2 rounded-lg border border-dashed border-slate-300 text-[#1E3A8A] hover:bg-blue-50/60">
                {s}
              </button>
            ))}
          </div>
        )}
        {log.map((m, i) =>
          m.who === 'you' ? (
            <div key={i} className="bg-blue-50 p-2.5 rounded-lg border border-blue-200 ml-8">
              <div className="flex items-center justify-between text-[10px] text-blue-600 font-mono mb-1">
                <span className="font-bold text-[#1E3A8A]">Dispatcher</span>
                <span>{time(m.at)}</span>
              </div>
              <p className="text-blue-900">{m.text}</p>
            </div>
          ) : (
            <div key={i} className={`p-2.5 rounded-lg border mr-4 ${m.who === 'error' ? 'bg-rose-50 border-rose-200' : 'bg-slate-50 border-slate-200'}`}>
              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono mb-1">
                <span className="font-bold text-slate-800">City Supervisor Agent</span>
                <span>{time(m.at)}</span>
              </div>
              <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{m.text}</p>
            </div>
          ),
        )}
        {busy && <div className="text-slate-400 font-mono text-[11px]">Supervisor agent is querying issues…</div>}
        <div ref={bottom} />
      </div>
      <form
        className="p-3 border-t border-slate-200 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          ask()
        }}
      >
        <input
          autoFocus
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask the supervisor agent about open issues…"
          className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg outline-none focus:border-[#1E3A8A]"
        />
        <button disabled={busy} className="px-3 py-1.5 bg-[#1E3A8A] text-white font-semibold rounded-lg flex items-center gap-1.5 disabled:opacity-60">
          <Send className="w-3.5 h-3.5" /> Ask
        </button>
      </form>
    </ModalShell>
  )
}

/** Pick a crew other than the recommendation, then approve. */
export function AssignModal({ issue, crews, onClose, onAssigned, showToast }) {
  const [busy, setBusy] = useState(false)
  const recommendedDept = issue.recommended_department
  const ordered = [...crews].sort(
    (a, b) => (b.department_id === recommendedDept) - (a.department_id === recommendedDept) || a.open_jobs / a.capacity - b.open_jobs / b.capacity,
  )

  async function assign(crew) {
    setBusy(true)
    try {
      const updated = await api.approve(issue.issue_id, { crew_id: crew.crew_id })
      onAssigned(updated)
      showToast(`${crew.name} assigned to ${issueCode(issue.issue_id)}`, crew.crew_id === issue.recommended_crew ? 'Matches the Router agent recommendation.' : 'Dispatcher override of the Router agent recommendation.')
      onClose()
    } catch (e) {
      showToast('Assignment failed', e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <ModalShell title={`Assign Crew to ${issueCode(issue.issue_id)}`} icon={Truck} iconClass="text-teal-400" onClose={onClose} width="max-w-sm">
      <div className="p-4 space-y-2 max-h-[60vh] overflow-y-auto">
        <p className="text-slate-600 mb-2">Crews in {issue.recommended_department_name || 'the recommended department'} are listed first.</p>
        {ordered.map((c) => {
          const load = c.open_jobs / c.capacity
          return (
            <button
              key={c.crew_id}
              disabled={busy}
              onClick={() => assign(c)}
              className={`w-full text-left p-2.5 rounded-lg border hover:border-[#1E3A8A] hover:bg-blue-50/50 flex items-center justify-between gap-2 transition-colors ${
                c.department_id === recommendedDept ? 'border-slate-200' : 'border-slate-100 opacity-70'
              }`}
            >
              <div className="min-w-0">
                <div className="font-bold text-slate-900 truncate">
                  {c.name}
                  {c.crew_id === issue.recommended_crew && <span className="ml-1.5 px-1 rounded bg-teal-100 text-teal-800 text-[9px] font-mono">RECOMMENDED</span>}
                </div>
                <div className="text-[10px] text-slate-400 truncate">{c.department_name}</div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold shrink-0 ${load >= 0.9 ? 'bg-rose-100 text-rose-700' : load >= 0.7 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
                {c.open_jobs}/{c.capacity}
              </span>
            </button>
          )
        })}
      </div>
    </ModalShell>
  )
}
