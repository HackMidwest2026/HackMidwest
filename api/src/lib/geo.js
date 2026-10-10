// Small offline gazetteer for Kansas City. Good enough for a demo, swappable for
// Amazon Location Service or Nominatim later.
import { city } from './data.js'

const M_PER_DEG_LAT = 111320

export function distanceM(a, b) {
  const R = 6371000
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(b.lat - a.lat)
  const dLng = toRad(b.lng - a.lng)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

function mPerDegLng(lat) {
  return M_PER_DEG_LAT * Math.cos((lat * Math.PI) / 180)
}

function distanceToStreetM(street, { lat, lng }) {
  return street.axis === 'ns' ? Math.abs(lng - street.lng) * mPerDegLng(lat) : Math.abs(lat - street.lat) * M_PER_DEG_LAT
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function mentionedStreets(text) {
  const t = ` ${text.toLowerCase().replace(/[^a-z0-9 ]/g, ' ')} `
  const hits = []
  for (const s of city.streets) {
    for (const alias of [s.name.toLowerCase(), ...s.aliases]) {
      const idx = t.search(new RegExp(`\\b${escapeRe(alias)}\\b`))
      if (idx >= 0) {
        hits.push({ street: s, idx })
        break
      }
    }
  }
  return hits.sort((a, b) => a.idx - b.idx).map((h) => h.street)
}

/** Geocode free text like "Troost near 39th" to the intersection of the first N-S and E-W streets named. */
export function geocodeAddress(text) {
  const streets = mentionedStreets(text || '')
  const ns = streets.find((s) => s.axis === 'ns')
  const ew = streets.find((s) => s.axis === 'ew')
  if (ns && ew) {
    return { found: true, lat: ew.lat, lng: ns.lng, address: `${ns.name} & ${ew.name}, Kansas City, MO`, precision: 'intersection' }
  }
  const only = ns || ew
  if (only) {
    return { found: false, reason: `Only one street recognised (${only.name}); need a cross street.`, street: only.name }
  }
  return { found: false, reason: 'No known Kansas City street names found.' }
}

export function nearestStreets({ lat, lng }, maxM = 400) {
  return city.streets
    .map((s) => ({ ...s, distance_m: Math.round(distanceToStreetM(s, { lat, lng })) }))
    .filter((s) => s.distance_m <= maxM)
    .sort((a, b) => a.distance_m - b.distance_m)
}

export function neighborhoodFor({ lat, lng }) {
  let best = null
  for (const n of city.neighborhoods) {
    const d = distanceM({ lat, lng }, n)
    if (!best || d < best.d) best = { name: n.name, d }
  }
  return best && best.d < 4000 ? best.name : 'Kansas City'
}

/** Reverse geocode to the nearest gazetteer intersection. */
export function reverseGeocode({ lat, lng }) {
  const near = nearestStreets({ lat, lng }, 1500)
  const ns = near.find((s) => s.axis === 'ns')
  const ew = near.find((s) => s.axis === 'ew')
  const neighborhood = neighborhoodFor({ lat, lng })
  if (ns && ew) {
    return { address: `${ns.name} & ${ew.name}, Kansas City, MO`, neighborhood, offset_m: Math.round(Math.hypot(ns.distance_m, ew.distance_m)) }
  }
  return { address: `${lat.toFixed(5)}, ${lng.toFixed(5)}, Kansas City, MO`, neighborhood, offset_m: null }
}

const ROAD_RANK = { arterial: 3, collector: 2, residential: 1 }

/** Highest road class among streets within ~45 m of the point (default residential). */
export function roadType({ lat, lng }) {
  const near = nearestStreets({ lat, lng }, 45)
  if (!near.length) return { road_type: 'residential', street: null, note: 'No mapped street within 45 m; assumed residential.' }
  const best = near.reduce((a, b) => (ROAD_RANK[b.road_type] > ROAD_RANK[a.road_type] ? b : a))
  return { road_type: best.road_type, street: best.name, distance_m: best.distance_m }
}

export function nearbySensitiveSites({ lat, lng }, radiusM = 200) {
  return city.sensitive_sites
    .map((s) => ({ ...s, distance_m: Math.round(distanceM({ lat, lng }, s)) }))
    .filter((s) => s.distance_m <= radiusM)
    .sort((a, b) => a.distance_m - b.distance_m)
}
