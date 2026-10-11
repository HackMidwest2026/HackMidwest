import { Component } from 'react'

/**
 * Catches render errors below it so one broken panel can't blank the whole page.
 * Shows the error with a retry button (or `fallback(error, reset)` if given) and logs it.
 */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error(`[CityCare] ${this.props.name || 'UI'} crashed:`, error, info?.componentStack)
  }

  reset = () => this.setState({ error: null })

  render() {
    const { error } = this.state
    if (!error) return this.props.children
    if (this.props.fallback) return this.props.fallback(error, this.reset)
    return (
      <div className="h-full w-full flex items-center justify-center p-6 bg-[#FAF8FF]">
        <div className="max-w-md w-full bg-white border border-rose-200 rounded-xl shadow p-4 text-xs">
          <div className="font-bold text-rose-700 text-sm mb-1">Something went wrong in {this.props.name || 'the app'}.</div>
          <pre className="whitespace-pre-wrap break-words text-rose-900 bg-rose-50 rounded p-2 font-mono text-[11px] max-h-48 overflow-auto">{String(error?.message || error)}</pre>
          <div className="flex gap-2 mt-3">
            <button onClick={this.reset} className="px-3 py-1.5 bg-[#1E3A8A] text-white rounded font-semibold">
              Try again
            </button>
            <button onClick={() => window.location.reload()} className="px-3 py-1.5 border border-slate-200 rounded font-medium text-slate-700">
              Reload page
            </button>
          </div>
        </div>
      </div>
    )
  }
}
