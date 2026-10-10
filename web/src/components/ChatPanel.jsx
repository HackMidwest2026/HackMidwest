import { useState } from 'react'
import { api } from '../api.js'

const SUGGESTIONS = ['What are the most dangerous open issues in Midtown?', "What's most urgent in Westport?", 'How many issues are open?']

export default function ChatPanel() {
  const [question, setQuestion] = useState('')
  const [log, setLog] = useState([])
  const [busy, setBusy] = useState(false)

  async function ask(q) {
    const text = (q ?? question).trim()
    if (!text) return
    setQuestion('')
    setBusy(true)
    setLog((l) => [...l, { role: 'you', text }])
    try {
      const { answer } = await api.chat(text)
      setLog((l) => [...l, { role: 'supervisor', text: answer }])
    } catch (e) {
      setLog((l) => [...l, { role: 'error', text: e.message }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel chat">
      <div className="panel-head">
        <h2>Ask the supervisor</h2>
      </div>
      <div className="chat-log">
        {log.length === 0 &&
          SUGGESTIONS.map((s) => (
            <button key={s} className="suggestion" onClick={() => ask(s)}>
              {s}
            </button>
          ))}
        {log.map((m, i) => (
          <div key={i} className={`msg msg-${m.role}`}>
            {m.text}
          </div>
        ))}
        {busy && <div className="msg msg-supervisor muted">Thinking…</div>}
      </div>
      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault()
          ask()
        }}
      >
        <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about open issues…" />
        <button className="primary" disabled={busy}>
          Ask
        </button>
      </form>
    </section>
  )
}
