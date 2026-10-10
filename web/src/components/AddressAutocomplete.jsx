import { Building2, Landmark, MapPin, Navigation } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { api } from '../api.js'

const KIND_ICON = { intersection: Navigation, place: Landmark, neighborhood: Building2, address: MapPin }

/**
 * Address input with a suggestions dropdown. Typing queries /api/address-suggest
 * (KC intersections and landmarks, plus OpenStreetMap street addresses); picking one calls
 * onSelect({ label, address, lat, lng }). Keyboard: ↑/↓ to move, Enter to pick, Esc to close.
 */
export default function AddressAutocomplete({ value, onChange, onSelect, onSubmitText, placeholder, inputClassName = '' }) {
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [loading, setLoading] = useState(false)
  const typed = useRef(false) // only search on user typing, not when a pin fills the field
  const listId = useId()

  useEffect(() => {
    if (!typed.current) return
    const q = value.trim()
    if (q.length < 2) {
      setItems([])
      setOpen(false)
      return
    }
    let cancelled = false
    setLoading(true)
    const t = setTimeout(() => {
      api
        .addressSuggest(q)
        .then((list) => {
          if (cancelled) return
          setItems(list)
          setActive(list.length ? 0 : -1)
          setOpen(true)
        })
        .catch(() => !cancelled && setItems([]))
        .finally(() => !cancelled && setLoading(false))
    }, 180)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [value])

  function pick(item) {
    typed.current = false
    setOpen(false)
    setItems([])
    onSelect(item)
  }

  function onKeyDown(e) {
    if (e.key === 'ArrowDown' && items.length) {
      e.preventDefault()
      setOpen(true)
      setActive((i) => (i + 1) % items.length)
    } else if (e.key === 'ArrowUp' && items.length) {
      e.preventDefault()
      setActive((i) => (i <= 0 ? items.length - 1 : i - 1))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (open && items[active]) pick(items[active])
      else onSubmitText?.()
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="relative flex-1">
      <MapPin className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
      <input
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open && active >= 0 ? `${listId}-${active}` : undefined}
        autoComplete="off"
        value={value}
        onChange={(e) => {
          typed.current = true
          onChange(e.target.value)
        }}
        onKeyDown={onKeyDown}
        onFocus={() => items.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        className={inputClassName}
        placeholder={placeholder}
      />
      {open && (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 top-full mt-1 z-[1200] max-h-64 overflow-y-auto bg-white border border-slate-200 rounded-lg shadow-xl py-1"
        >
          {items.length === 0 && <li className="px-3 py-2 text-[11px] text-slate-400">{loading ? 'Searching…' : 'No matches. Try cross streets, e.g. "Troost & 39th".'}</li>}
          {items.map((s, i) => {
            const Icon = KIND_ICON[s.kind] || MapPin
            return (
              <li
                key={`${s.source}-${s.label}-${i}`}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === active}
                // mousedown (not click) so the input's blur doesn't close the list first
                onMouseDown={(e) => {
                  e.preventDefault()
                  pick(s)
                }}
                onMouseEnter={() => setActive(i)}
                className={`px-3 py-1.5 flex items-start gap-2 cursor-pointer ${i === active ? 'bg-blue-50' : 'hover:bg-slate-50'}`}
              >
                <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${s.kind === 'intersection' ? 'text-[#1E3A8A]' : 'text-slate-400'}`} />
                <span className="min-w-0">
                  <span className="block text-xs font-medium text-slate-800 truncate">{s.label}</span>
                  {s.sublabel && <span className="block text-[10px] text-slate-500 truncate">{s.sublabel}</span>}
                </span>
              </li>
            )
          })}
          {items.some((s) => s.source === 'photon') && <li className="px-3 pt-1 text-[9px] text-slate-400 border-t border-slate-100 mt-1">Addresses © OpenStreetMap contributors (Photon)</li>}
        </ul>
      )}
    </div>
  )
}
