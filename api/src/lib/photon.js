// Optional street-address suggestions from Photon (https://photon.komoot.io), a free
// OpenStreetMap geocoder built for search-as-you-type. No API key. Limited to the
// Kansas City area, cached, and given a short timeout so the UI never waits on it.
// Set PHOTON_URL=off to disable (offline demos), or point it at a self-hosted Photon.

const BASE = process.env.PHOTON_URL ?? 'https://photon.komoot.io'
const BBOX = '-94.77,38.83,-94.38,39.33' // minLon,minLat,maxLon,maxLat around Kansas City, MO
const cache = new Map()

function label(p) {
  const street = [p.housenumber, p.street].filter(Boolean).join(' ')
  const main = p.name && p.name !== p.street ? p.name : street || p.name
  const rest = [p.name && street && p.name !== street ? street : null, p.district || p.locality, p.city, p.state].filter(Boolean)
  return { main, rest: [...new Set(rest)].join(', ') }
}

export async function photonSuggest(query, limit = 5) {
  if (!BASE || BASE === 'off') return []
  const key = query.trim().toLowerCase()
  if (cache.has(key)) return cache.get(key)
  const url = `${BASE.replace(/\/$/, '')}/api/?q=${encodeURIComponent(query)}&limit=${limit}&bbox=${BBOX}&lang=en`
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(1500), headers: { 'User-Agent': 'CityCare-HackMidwest/0.1' } })
    if (!res.ok) return []
    const data = await res.json()
    const out = (data.features || [])
      .filter((f) => f.geometry?.type === 'Point')
      .map((f) => {
        const [lng, lat] = f.geometry.coordinates
        const { main, rest } = label(f.properties || {})
        return { label: main, sublabel: rest, address: [main, rest].filter(Boolean).join(', '), lat, lng, kind: 'address', source: 'photon' }
      })
      .filter((s) => s.label)
    if (cache.size > 300) cache.delete(cache.keys().next().value)
    cache.set(key, out)
    return out
  } catch {
    return [] // offline, blocked or slow: local suggestions still work
  }
}
