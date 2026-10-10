// OpenStreetMap geocoding through Photon (https://photon.komoot.io): free, no API key, and
// built for search-as-you-type. Works for any location. Results are biased toward a point
// (the map view or the configured city center) rather than restricted to one city.
// Cached, with a short timeout so the UI never waits on it.
// Set PHOTON_URL=off to disable (offline demos), or point it at a self-hosted Photon.
import { city, cityProfile } from './data.js'

const BASE = process.env.PHOTON_URL ?? 'https://photon.komoot.io'
const TIMEOUT_MS = 1500
const cache = new Map()

export const photonEnabled = () => Boolean(BASE) && BASE !== 'off'

async function get(path, params) {
  if (!photonEnabled()) return null
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== '')).toString()
  const url = `${BASE.replace(/\/$/, '')}${path}?${qs}`
  if (cache.has(url)) return cache.get(url)
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS), headers: { 'User-Agent': 'CityCare/0.1 (hackathon demo)' } })
    if (!res.ok) return null
    const data = await res.json()
    if (cache.size > 500) cache.delete(cache.keys().next().value)
    cache.set(url, data)
    return data
  } catch {
    return null // offline, blocked or slow: callers fall back to local data
  }
}

function describe(p = {}) {
  const street = [p.housenumber, p.street].filter(Boolean).join(' ')
  const main = p.name && p.name !== p.street ? p.name : street || p.name || ''
  const place = [p.city || p.town || p.village || p.county, p.state, p.countrycode && p.countrycode.toUpperCase() !== cityProfile.country_code.toUpperCase() ? p.country : null]
  const rest = [p.name && street && p.name !== street ? street : null, p.district || p.locality, ...place].filter(Boolean)
  return { main, rest: [...new Set(rest)].join(', '), area: p.district || p.locality || p.city || p.town || p.village || p.county || null }
}

function toSuggestion(f) {
  const [lng, lat] = f.geometry.coordinates
  const { main, rest, area } = describe(f.properties)
  return { label: main, sublabel: rest, address: [main, rest].filter(Boolean).join(', '), lat, lng, area, kind: 'address', source: 'photon' }
}

/** Search suggestions near `bias` ({ lat, lng }), defaulting to the configured city center. */
export async function photonSuggest(query, { limit = 5, bias = city.center } = {}) {
  const data = await get('/api/', { q: query, limit, lat: bias?.lat, lon: bias?.lng, lang: 'en' })
  return (data?.features || []).filter((f) => f.geometry?.type === 'Point').map(toSuggestion).filter((s) => s.label)
}

/** Best single match for free text, or null. */
export async function photonGeocode(text, bias) {
  return (await photonSuggest(text, { limit: 1, bias }))[0] || null
}

/** Address for a point, or null. */
export async function photonReverse({ lat, lng }) {
  const data = await get('/reverse', { lat, lon: lng, lang: 'en' })
  const f = data?.features?.[0]
  return f ? toSuggestion(f) : null
}
