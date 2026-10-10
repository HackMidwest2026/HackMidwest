import { ChevronLeft, ChevronRight, ImageOff, Sparkles, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { timeAgo } from '../lib/display.js'

const SEVERITY_PILL = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-amber-100 text-amber-800',
  low: 'bg-slate-100 text-slate-600',
}

/**
 * In-app photo viewer (lightbox) for report photos.
 * photos: [{ report_id, photo_url, raw_text, created_at, photo_analysis }]
 * Keyboard: ← / → to move between photos, Esc to close.
 */
export default function PhotoViewer({ photos, startIndex = 0, onClose }) {
  const [index, setIndex] = useState(startIndex)
  const [failed, setFailed] = useState(false)
  const photo = photos[index]
  const many = photos.length > 1
  const go = (d) => {
    setFailed(false)
    setIndex((i) => (i + d + photos.length) % photos.length)
  }

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowRight' && many) go(1)
      else if (e.key === 'ArrowLeft' && many) go(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [many, onClose]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!photo) return null
  const a = photo.photo_analysis
  return (
    <div className="fixed inset-0 z-[1300] bg-slate-950/85 backdrop-blur-sm flex flex-col" onClick={onClose} role="dialog" aria-modal="true" aria-label="Report photo">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-3 text-white text-xs shrink-0" onClick={(e) => e.stopPropagation()}>
        <div className="font-mono">
          {photo.report_id}
          {many && <span className="text-slate-400"> · {index + 1} / {photos.length}</span>}
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10" aria-label="Close photo">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Image */}
      <div className="flex-1 min-h-0 relative flex items-center justify-center px-4 sm:px-16">
        {failed ? (
          <div className="text-slate-300 text-sm flex flex-col items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <ImageOff className="w-8 h-8" />
            This photo is no longer available.
          </div>
        ) : (
          <img
            key={photo.photo_url}
            src={photo.photo_url}
            alt={a?.shows || 'Report photo'}
            onError={() => setFailed(true)}
            onClick={(e) => e.stopPropagation()}
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl animate-in"
          />
        )}
        {many && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation()
                go(-1)
              }}
              className="absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white"
              aria-label="Previous photo"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                go(1)
              }}
              className="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white"
              aria-label="Next photo"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </>
        )}
      </div>

      {/* Caption: the resident's words and what the Vision agent saw */}
      <div className="shrink-0 px-4 py-3 flex justify-center" onClick={(e) => e.stopPropagation()}>
        <div className="w-full max-w-2xl bg-white rounded-xl p-3 text-xs text-slate-700 space-y-1.5">
          <div className="flex items-start gap-2">
            <span className="font-mono text-slate-400 shrink-0">{timeAgo(photo.created_at)}</span>
            <span className="italic">“{photo.raw_text}”</span>
          </div>
          {a?.analyzed ? (
            <div className="flex items-start gap-2 text-[11px] text-slate-600 border-t border-slate-100 pt-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#0D9488] shrink-0 mt-0.5" />
              <span>
                <span className="font-semibold text-[#0D9488]">Vision agent:</span> {a.shows}
                {a.severity && <span className={`ml-1.5 px-1.5 rounded font-mono text-[10px] font-bold ${SEVERITY_PILL[a.severity] || SEVERITY_PILL.low}`}>{a.severity.toUpperCase()}</span>}
                {a.hazards?.length > 0 && <span className="text-slate-500"> · {a.hazards.map((h) => h.replaceAll('_', ' ')).join(', ')}</span>}
                {a.is_city_issue === false && <span className="text-amber-700"> · may not show a city issue</span>}
              </span>
            </div>
          ) : (
            a?.note && <div className="text-[11px] text-slate-400 border-t border-slate-100 pt-1.5">Photo not analyzed: {a.note}</div>
          )}
        </div>
      </div>
    </div>
  )
}
