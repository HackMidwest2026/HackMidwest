import { Radio, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { AUTH_REQUIRED, api } from './api.js'
import AuthScreen from './components/AuthScreen.jsx'
import CitizenPortal from './components/CitizenPortal.jsx'
import DispatchConsole from './components/DispatchConsole.jsx'
import Navbar from './components/Navbar.jsx'
import { cityLabel } from './lib/display.js'
import { useCityData } from './lib/useCityData.js'

function useHashMode() {
  const read = () => (window.location.hash.startsWith('#/dispatch') ? 'dispatch' : 'citizen')
  const [mode, setModeState] = useState(read)
  useEffect(() => {
    const on = () => setModeState(read())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  const setMode = useCallback((m) => {
    window.location.hash = m === 'dispatch' ? '#/dispatch' : '#/'
  }, [])
  return [mode, setMode]
}

export default function App() {
  const [mode, setMode] = useHashMode()
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [toast, setToast] = useState(null)
  const toastTimer = useRef(null)

  const showToast = useCallback((message, sub) => {
    clearTimeout(toastTimer.current)
    setToast({ message, sub })
    toastTimer.current = setTimeout(() => setToast(null), 6000)
  }, [])

  const data = useCityData({
    onPipelineEvent: (e) => {
      // Announce single-report runs in the console; batch runs report their own summary.
      if (e.report_id && e.data?.issue_id && window.location.hash.startsWith('#/dispatch')) {
        showToast(e.data.merged ? `New report merged into #${e.data.issue_id}` : `New incident #${e.data.issue_id} opened`, 'Triaged by the agents. Awaiting your approval.')
      }
    },
  })

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setMetaError(e.message))
  }, [])

  // Signed-in dispatcher: undefined while checking, null when signed out.
  const [user, setUser] = useState(undefined)
  useEffect(() => {
    api.me().then((r) => setUser(r.user)).catch(() => setUser(null))
    const expired = () => setUser(null)
    window.addEventListener(AUTH_REQUIRED, expired)
    return () => window.removeEventListener(AUTH_REQUIRED, expired)
  }, [])
  const logout = useCallback(async () => {
    await api.logout().catch(() => {})
    setUser(null)
    setSelectedId(null)
  }, [])

  const selectedIssue = data.issues.find((i) => i.issue_id === selectedId) || null
  const p1Count = data.issues.filter((i) => i.priority_tier === 'P1' && !['resolved', 'rejected'].includes(i.status)).length

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#FAF8FF]">
      <Navbar mode={mode} onSetMode={setMode} stream={data.stream} engine={meta?.mode} p1Count={p1Count} cityName={cityLabel(meta)} />

      <main className="flex-1 relative overflow-hidden">
        {(metaError || data.error) && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1200] bg-rose-50 border border-rose-200 text-rose-800 text-xs px-3 py-2 rounded-lg shadow">
            Can't reach the CityCare API: {metaError || data.error}
          </div>
        )}
        {meta &&
          (mode === 'citizen' ? (
            <CitizenPortal meta={meta} data={data} selectedIssue={selectedIssue} onSelectIssue={setSelectedId} onSwitchToDispatch={() => setMode('dispatch')} />
          ) : (
            user === undefined ? null : user ? (
              <DispatchConsole meta={meta} data={data} user={user} onLogout={logout} selectedIssue={selectedIssue} onSelectIssue={setSelectedId} showToast={showToast} onSwitchToCitizen={() => setMode('citizen')} />
            ) : (
              <AuthScreen
                cityName={meta.city?.name}
                onSwitchToCitizen={() => setMode('citizen')}
                onSignedIn={(u) => {
                  setUser(u)
                  showToast(`Welcome, ${u.name.split(' ')[0]}`, 'Signed in to Dispatch Command.')
                }}
              />
            )
          ))}
      </main>

      {toast && (
        <div className="fixed bottom-6 right-6 z-[1300] bg-[#00164E] text-white p-3.5 rounded-xl shadow-2xl border border-blue-800 flex items-start gap-3 max-w-sm animate-in">
          <div className="w-8 h-8 rounded-lg bg-[#0D9488] flex items-center justify-center shrink-0 mt-0.5 text-white">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>
          <div className="flex-1 min-w-0 text-xs">
            <div className="font-bold text-white leading-tight">{toast.message}</div>
            {toast.sub && <div className="text-slate-300 text-[11px] mt-0.5 leading-snug">{toast.sub}</div>}
          </div>
          <button onClick={() => setToast(null)} className="text-slate-400 hover:text-white p-0.5" aria-label="Dismiss">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}
