import { useCallback, useEffect, useState } from 'react'

// Theme preference: 'system' (follow the OS), 'light' or 'dark'. index.html applies the saved
// choice before first paint; this hook keeps <html class="dark"> in sync afterwards.
const KEY = 'citycare-theme'
const ORDER = ['system', 'light', 'dark']

function readPreference() {
  try {
    const v = localStorage.getItem(KEY)
    return ORDER.includes(v) ? v : 'system'
  } catch {
    return 'system'
  }
}

const systemDark = () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false

export function useTheme() {
  const [preference, setPreference] = useState(readPreference)
  const [osDark, setOsDark] = useState(systemDark)

  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!mq) return
    const on = (e) => setOsDark(e.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])

  const dark = preference === 'dark' || (preference === 'system' && osDark)
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  const cycle = useCallback(() => {
    setPreference((p) => {
      const next = ORDER[(ORDER.indexOf(p) + 1) % ORDER.length]
      try {
        localStorage.setItem(KEY, next)
      } catch {
        // Private mode or blocked storage: the choice lasts for this visit only.
      }
      return next
    })
  }, [])

  return { preference, dark, cycle }
}
