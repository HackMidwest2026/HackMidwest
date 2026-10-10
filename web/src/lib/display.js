// Display helpers: map API issues and categories onto the CityCare visual language.
import { AlertTriangle, Building2, CircleHelp, Droplets, Lightbulb, PawPrint, Trash2, TreePine } from 'lucide-react'

export const CATEGORY_META = {
  streets: { label: 'Pothole', filterLabel: 'Streets', icon: AlertTriangle, dot: 'bg-red-500' },
  traffic_lighting: { label: 'Light', filterLabel: 'Lighting', icon: Lightbulb, dot: 'bg-amber-500' },
  water: { label: 'Water', filterLabel: 'Water', icon: Droplets, dot: 'bg-blue-500' },
  trash: { label: 'Trash', filterLabel: 'Sanitation', icon: Trash2, dot: 'bg-slate-500' },
  parks_trees: { label: 'Tree', filterLabel: 'Trees', icon: TreePine, dot: 'bg-green-600' },
  property: { label: 'Property', filterLabel: 'Property', icon: Building2, dot: 'bg-purple-500' },
  animals: { label: 'Animal', filterLabel: 'Animals', icon: PawPrint, dot: 'bg-orange-500' },
  other: { label: 'Other', filterLabel: 'Other', icon: CircleHelp, dot: 'bg-slate-400' },
}

export const categoryMeta = (id) => CATEGORY_META[id] || CATEGORY_META.other

export const TIER_META = {
  P1: { label: 'P1 CRITICAL', level: 1, badge: 'bg-red-100 text-red-700', border: 'border-l-red-500', dot: 'bg-[#DC2626]' },
  P2: { label: 'PRIORITY 2', level: 2, badge: 'bg-amber-100 text-amber-700', border: 'border-l-amber-500', dot: 'bg-[#D97706]' },
  P3: { label: 'PRIORITY 3', level: 3, badge: 'bg-teal-100 text-teal-700', border: 'border-l-teal-500', dot: 'bg-[#0D9488]' },
  P4: { label: 'PRIORITY 4', level: 4, badge: 'bg-slate-100 text-slate-600', border: 'border-l-slate-400', dot: 'bg-slate-500' },
}

export const tierMeta = (tier) => TIER_META[tier] || { label: 'SCORING…', level: 5, badge: 'bg-slate-100 text-slate-500', border: 'border-l-slate-300', dot: 'bg-slate-400' }

export const STATUS_META = {
  new: { label: 'New', pill: 'bg-slate-100 text-slate-700' },
  triaged: { label: 'Awaiting approval', pill: 'bg-blue-100 text-blue-800' },
  approved: { label: 'Approved', pill: 'bg-emerald-100 text-emerald-800' },
  assigned: { label: 'Crew assigned', pill: 'bg-[#FFEDD5] text-[#C2410C]' },
  in_progress: { label: 'In progress', pill: 'bg-indigo-100 text-indigo-800' },
  resolved: { label: 'Resolved', pill: 'bg-emerald-100 text-emerald-800' },
  rejected: { label: 'Rejected', pill: 'bg-rose-100 text-rose-700' },
}

export const statusMeta = (s) => STATUS_META[s] || { label: s, pill: 'bg-slate-100 text-slate-700' }

export const OPEN_STATUSES = new Set(['new', 'triaged', 'approved', 'assigned', 'in_progress'])
export const ACTIVE_WORK = new Set(['approved', 'assigned', 'in_progress'])

export const issueCode = (id) => `#${id}`
/** First part of an address ("12 Main St, Springfield, IL" -> "12 Main St"). */
export const shortAddress = (a) => (a || '').split(',')[0]

/** "City, Region" from the configured city profile, or '' when none is set. */
export const cityLabel = (meta) => [meta?.city?.name, meta?.city?.region].filter(Boolean).join(', ')

export function timeAgo(iso) {
  if (!iso) return ''
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m ago`
  return `${Math.floor(s / 86400)}d ago`
}

/** Remaining time against the SLA, measured from the first report. */
export function slaRemaining(issue) {
  if (!issue.suggested_sla_hours || !issue.first_reported_at) return null
  const due = new Date(issue.first_reported_at).getTime() + issue.suggested_sla_hours * 3600000
  const ms = due - Date.now()
  const h = Math.floor(Math.abs(ms) / 3600000)
  const m = Math.floor((Math.abs(ms) % 3600000) / 60000)
  const text = h >= 48 ? `${Math.floor(h / 24)}d ${h % 24}h` : `${h}h ${m}m`
  return { overdue: ms < 0, text: ms < 0 ? `${text} overdue` : text }
}

export function formatBytes(n) {
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}
