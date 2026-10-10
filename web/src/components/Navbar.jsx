import { AlertTriangle, ArrowRightLeft, HeartPulse, Radio } from 'lucide-react'

export default function Navbar({ mode, onSetMode, stream, engine, p1Count, cityName }) {
  const live = stream === 'live'
  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-3 md:px-6 flex items-center justify-between z-[1100] shrink-0 select-none shadow-xs gap-3">
      <a href="#/" className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-lg bg-[#00236F] flex items-center justify-center text-white shadow-sm shrink-0">
          <HeartPulse className="w-5 h-5 stroke-[2.2]" />
        </div>
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="font-bold text-slate-900 text-sm md:text-base tracking-tight leading-tight hidden min-[420px]:block">CityCare</h1>
          <span className="text-xs text-slate-400 hidden lg:inline">/</span>
          <span className="text-xs text-slate-500 font-medium hidden lg:inline truncate">{cityName || 'City Services'}</span>
        </div>
      </a>

      <div className="flex items-center gap-1 sm:gap-2">
        <button
          onClick={() => onSetMode('citizen')}
          className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
            mode === 'citizen' ? 'bg-[#00236F] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Citizen Portal</span>
          <span className="sm:hidden">Report</span>
        </button>
        <button
          onClick={() => onSetMode('dispatch')}
          className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
            mode === 'dispatch' ? 'bg-[#00236F] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Radio className={`w-3.5 h-3.5 ${mode === 'dispatch' ? 'text-teal-300' : 'text-teal-600'}`} />
          <span className="hidden sm:inline">Dispatch Command</span>
          <span className="sm:hidden">Dispatch</span>
          {p1Count > 0 && <span className="hidden sm:inline px-1.5 rounded text-[10px] font-mono font-bold bg-[#DC2626] text-white">{p1Count} P1</span>}
        </button>
      </div>

      <div className="flex items-center gap-3">
        <div
          className="flex items-center gap-2 text-xs font-medium text-slate-700 bg-slate-50 px-2.5 py-1 rounded-full border border-slate-200"
          title={engine === 'bedrock' ? 'Agents running on Claude via Amazon Bedrock' : 'Agents running on the rule-based mock engine'}
        >
          <span className={`w-2 h-2 rounded-full ${live ? 'bg-[#059669] animate-pulse' : 'bg-amber-500'}`} />
          <span className="hidden lg:inline">{live ? 'Agents online' : 'Reconnecting…'}</span>
          <span className={`hidden md:inline px-1.5 rounded text-[10px] font-mono font-bold ${engine === 'bedrock' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
            {engine === 'bedrock' ? 'BEDROCK' : 'MOCK'}
          </span>
        </div>
        <button
          onClick={() => onSetMode(mode === 'citizen' ? 'dispatch' : 'citizen')}
          className="text-xs font-semibold text-[#1E3A8A] hover:bg-blue-50 px-2.5 py-1 rounded border border-blue-200 hidden xl:flex items-center gap-1.5 whitespace-nowrap transition-colors"
        >
          <ArrowRightLeft className="w-3.5 h-3.5" />
          <span>Switch to {mode === 'citizen' ? 'Dispatch Console' : 'Citizen Portal'}</span>
        </button>
      </div>
    </header>
  )
}
