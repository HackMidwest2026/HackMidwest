import { useEffect, useState } from 'react'
import { api } from './api.js'
import DispatcherView from './components/DispatcherView.jsx'
import ResidentView from './components/ResidentView.jsx'

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash || '#/')
  useEffect(() => {
    const on = () => setHash(window.location.hash || '#/')
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return hash
}

export default function App() {
  const route = useHashRoute()
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(e.message))
  }, [])

  const isDispatch = route.startsWith('#/dispatch')
  return (
    <div className={isDispatch ? 'app app-dispatch' : 'app app-resident'}>
      <header className="topbar">
        <a className="brand" href="#/">
          <span className="brand-mark">◆</span> CityOps <span className="brand-sub">Kansas City 311</span>
        </a>
        <nav>
          <a className={!isDispatch ? 'active' : ''} href="#/">
            Report a problem
          </a>
          <a className={isDispatch ? 'active' : ''} href="#/dispatch">
            Dispatcher
          </a>
          {meta && <span className={`mode mode-${meta.mode}`}>{meta.mode === 'bedrock' ? 'Bedrock agents' : 'Mock agents'}</span>}
        </nav>
      </header>
      {error && <div className="banner error">Can't reach the API: {error}</div>}
      {meta && (isDispatch ? <DispatcherView meta={meta} /> : <ResidentView meta={meta} />)}
    </div>
  )
}
