import { AlertTriangle, Eye, EyeOff, KeyRound, Loader2, Lock, Mail, Radio, ShieldCheck, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api.js'

function Field({ icon: Icon, label, children }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold text-slate-600 mb-1">{label}</span>
      <span className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg focus-within:border-[#1E3A8A] focus-within:ring-2 focus-within:ring-blue-100 transition-all">
        <Icon className="w-4 h-4 text-slate-400 shrink-0" />
        {children}
      </span>
    </label>
  )
}

const inputClass = 'flex-1 min-w-0 bg-transparent outline-none text-sm text-slate-900 placeholder:text-slate-400'

/** Dispatcher log in / sign up. Shown in place of the Dispatch console until signed in. */
export default function AuthScreen({ onSignedIn, onSwitchToCitizen, cityName }) {
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '', code: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [codeRequired, setCodeRequired] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.authConfig().then((c) => setCodeRequired(c.signup_code_required)).catch(() => {})
  }, [])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const switchTab = (t) => {
    setTab(t)
    setError(null)
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { user } =
        tab === 'login'
          ? await api.login(form.email, form.password)
          : await api.signup({ name: form.name, email: form.email, password: form.password, ...(codeRequired && { code: form.code }) })
      onSignedIn(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const signup = tab === 'signup'
  return (
    <div className="absolute inset-0 overflow-y-auto bg-gradient-to-br from-[#00164E] via-[#00236F] to-[#0B3A6E]">
      {/* faint grid, a nod to the map */}
      <div
        className="absolute inset-0 opacity-[0.07] pointer-events-none"
        style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }}
      />
      <div className="relative min-h-full flex items-center justify-center p-4">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-3 mb-5 text-white">
            <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center">
              <Radio className="w-5 h-5 text-teal-300" />
            </div>
            <div>
              <div className="font-bold text-lg leading-tight">Dispatch Command</div>
              <div className="text-xs text-[#BFDBFE]">{cityName ? `${cityName} Operations` : 'City Operations'} · dispatchers only</div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-2xl border border-white/20 overflow-hidden animate-in">
            <div className="grid grid-cols-2 p-1 m-4 mb-0 bg-slate-100 rounded-lg text-xs font-semibold" role="tablist">
              {[
                ['login', 'Log in'],
                ['signup', 'Sign up'],
              ].map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={tab === id}
                  onClick={() => switchTab(id)}
                  className={`py-1.5 rounded-md transition-all ${tab === id ? 'bg-white text-[#00236F] shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                >
                  {label}
                </button>
              ))}
            </div>

            <form onSubmit={submit} className="p-4 space-y-3">
              <p className="text-xs text-slate-500">
                {signup ? 'Create a dispatcher account to triage and approve incidents.' : 'Sign in to review the agents’ recommendations and dispatch crews.'}
              </p>
              {signup && (
                <Field icon={User} label="Full name">
                  <input className={inputClass} value={form.name} onChange={set('name')} placeholder="Jordan Rivera" autoComplete="name" required maxLength={80} />
                </Field>
              )}
              <Field icon={Mail} label="Work email">
                <input className={inputClass} type="email" value={form.email} onChange={set('email')} placeholder="you@city.gov" autoComplete="email" required autoFocus />
              </Field>
              <Field icon={Lock} label="Password">
                <input
                  className={inputClass}
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={set('password')}
                  placeholder={signup ? 'At least 8 characters' : 'Your password'}
                  autoComplete={signup ? 'new-password' : 'current-password'}
                  minLength={signup ? 8 : undefined}
                  required
                />
                <button type="button" onClick={() => setShowPassword((v) => !v)} className="text-slate-400 hover:text-slate-600" aria-label={showPassword ? 'Hide password' : 'Show password'}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </Field>
              {signup && codeRequired && (
                <Field icon={KeyRound} label="Dispatcher sign-up code">
                  <input className={inputClass} value={form.code} onChange={set('code')} placeholder="From your operations lead" autoComplete="off" required />
                </Field>
              )}

              {error && (
                <div className="flex items-start gap-2 p-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs" role="alert">
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full py-2 bg-[#00236F] hover:bg-[#1E3A8A] disabled:opacity-60 text-white rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition-colors"
              >
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                {signup ? 'Create account' : 'Log in'}
              </button>

              <p className="text-center text-xs text-slate-500">
                {signup ? 'Already have an account? ' : 'New dispatcher? '}
                <button type="button" onClick={() => switchTab(signup ? 'login' : 'signup')} className="text-[#2563EB] font-semibold hover:underline">
                  {signup ? 'Log in' : 'Create an account'}
                </button>
              </p>
            </form>
          </div>

          <button onClick={onSwitchToCitizen} className="w-full mt-4 text-xs text-[#DBEAFE] hover:text-white">
            Reporting a problem? Go to the Citizen Portal →
          </button>
        </div>
      </div>
    </div>
  )
}
