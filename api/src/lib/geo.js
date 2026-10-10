// Optional offline gazetteer for the configured city (data/city.json): grid streets,
// neighborhoods and sensitive sites. Everything here degrades gracefully when the city file
// has no such data, and lib/locate.js falls back to OpenStreetMap (Photon) for any location.
import { city, cityProfile } from './data.js'

const withSuffix = (s) => `${s}${cityProfile.address_suffix}`

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

// Phrases that contain a street alias but mean something else in a 311 report ("water main").
const NOT_A_STREET = /\b(water|gas|sewer|storm) mains?\b|\bmains? (break|broke|leak)\w*/g

const normalize = (text) => ` ${(text || '').toLowerCase().replace(NOT_A_STREET, ' ').replace(/[^a-z0-9&\- ]/g, ' ')} `

/** Every mention of a known street, with its position in the normalized text. */
function streetMentions(t) {
  const hits = []
  for (const s of city.streets) {
    for (const alias of [s.name.toLowerCase(), ...s.aliases]) {
      for (const m of t.matchAll(new RegExp(`\\b${escapeRe(alias)}\\b`, 'g'))) hits.push({ street: s, idx: m.index })
    }
  }
  return hits.sort((a, b) => a.idx - b.idx)
}

const findLandmark = (t) => (city.landmarks || []).find((l) => [l.name.toLowerCase(), ...l.aliases].some((a) => t.includes(a)))

/**
 * Geocode free text like "Troost near 39th" to an intersection. When several streets are
 * named, the N-S / E-W pair mentioned closest together wins ("water main break at Broadway
 * and Westport Rd" -> Broadway & Westport Rd). Falls back to a named landmark.
 */
export function geocodeAddress(text) {
  const t = normalize(text)
  const hits = streetMentions(t)
  let best = null
  for (const a of hits.filter((h) => h.street.axis === 'ns')) {
    for (const b of hits.filter((h) => h.street.axis === 'ew')) {
      const gap = Math.abs(a.idx - b.idx)
      if (!best || gap < best.gap) best = { ns: a.street, ew: b.street, gap }
    }
  }
  if (best) {
    const { ns, ew } = best
    return { found: true, lat: ew.lat, lng: ns.lng, address: withSuffix(`${ns.name} & ${ew.name}`), precision: 'intersection' }
  }
  const landmark = findLandmark(t)
  if (landmark) {
    return { found: true, lat: landmark.lat, lng: landmark.lng, address: withSuffix(landmark.name), precision: 'landmark' }
  }
  const only = hits[0]?.street
  if (only) {
    return { found: false, reason: `Only one street recognised (${only.name}); need a cross street.`, street: only.name }
  }
  return { found: false, reason: 'No known street names found in the local street data.' }
}

function cityLabelShort() {
  return [cityProfile.name, cityProfile.region].filter(Boolean).join(', ')
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
  return best && best.d < 4000 ? best.name : null
}

/**
 * Reverse geocode to the nearest local intersection. `covered` is false when the point is
 * outside the local street data; callers then ask OpenStreetMap (see lib/locate.js).
 */
export function reverseGeocode({ lat, lng }) {
  const near = nearestStreets({ lat, lng }, 1500)
  const ns = near.find((s) => s.axis === 'ns')
  const ew = near.find((s) => s.axis === 'ew')
  const neighborhood = neighborhoodFor({ lat, lng })
  if (ns && ew) {
    return { address: withSuffix(`${ns.name} & ${ew.name}`), neighborhood, offset_m: Math.round(Math.hypot(ns.distance_m, ew.distance_m)), covered: true }
  }
  return { address: `${lat.toFixed(5)}, ${lng.toFixed(5)}`, neighborhood, offset_m: null, covered: false }
}

const ROAD_RANK = { arterial: 3, collector: 2, residential: 1 }

/** Highest road class among streets within ~45 m of the point (default residential). */
export function roadType({ lat, lng }) {
  const near = nearestStreets({ lat, lng }, 45)
  if (!near.length) return { road_type: 'unknown', street: null, note: 'No street class data for this spot; no road-class points.' }
  const best = near.reduce((a, b) => (ROAD_RANK[b.road_type] > ROAD_RANK[a.road_type] ? b : a))
  return { road_type: best.road_type, street: best.name, distance_m: best.distance_m }
}

export function nearbySensitiveSites({ lat, lng }, radiusM = 200) {
  return city.sensitive_sites
    .map((s) => ({ ...s, distance_m: Math.round(distanceM({ lat, lng }, s)) }))
    .filter((s) => s.distance_m <= radiusM)
    .sort((a, b) => a.distance_m - b.distance_m)
}

// ---------- address autocomplete (offline gazetteer) ----------

const ROAD_ORDER = { arterial: 0, collector: 1, residential: 2 }
const SEPARATORS = /\s*(?:&|\/|@|,|\band\b|\bat\b|\bnear\b|\bby\b|\bx\b)\s*/i

function norm(s) {
  return (s || '').toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim()
}

/** How well a typed fragment matches a street (0 = no match). Handles "39", "39th", "troo", "paseo blvd". */
function streetScore(street, fragment) {
  const f = norm(fragment)
  if (!f) return 0
  const names = [norm(street.name), ...street.aliases.map(norm)]
  let best = 0
  for (const n of names) {
    if (n === f) best = Math.max(best, 4)
    else if (n.startsWith(f)) best = Math.max(best, 3)
    else if (n.split(' ').some((w) => w.startsWith(f))) best = Math.max(best, 2)
    else if (f.length >= 3 && n.includes(f)) best = Math.max(best, 1)
  }
  return best
}

function matchStreets(fragment, axis) {
  return city.streets
    .filter((s) => !axis || s.axis === axis)
    .map((s) => ({ s, score: streetScore(s, fragment) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score || a.s.name.localeCompare(b.s.name, undefined, { numeric: true }))
    .map((x) => x.s)
}

function intersection(a, b) {
  const ns = a.axis === 'ns' ? a : b
  const ew = a.axis === 'ns' ? b : a
  const point = { lat: ew.lat, lng: ns.lng }
  return {
    label: `${ns.name} & ${ew.name}`,
    sublabel: [neighborhoodFor(point), cityLabelShort()].filter(Boolean).join(' · '),
    address: withSuffix(`${ns.name} & ${ew.name}`),
    ...point,
    kind: 'intersection',
    source: 'gazetteer',
  }
}

// Numbered east-west streets (39th St -> 39) with their latitude, for house-number estimates.
const NUMBERED = city.streets
  .filter((s) => s.axis === 'ew' && /^\d+(st|nd|rd|th) St$/.test(s.name))
  .map((s) => ({ n: parseInt(s.name, 10), lat: s.lat }))
  .sort((a, b) => a.n - b.n)

function latForBlock(house) {
  const n = house / (cityProfile.address_grid?.house_number_per_block || 100)
  if (!NUMBERED.length) return null
  if (n < NUMBERED[0].n || n > NUMBERED.at(-1).n) return null
  const hi = NUMBERED.findIndex((x) => x.n >= n)
  const b = NUMBERED[hi]
  const a = NUMBERED[Math.max(0, hi - 1)]
  if (b.n === a.n) return b.lat
  return +(a.lat + ((n - a.n) / (b.n - a.n)) * (b.lat - a.lat)).toFixed(6)
}

/**
 * Suggestions for a partly typed location: "troost & 39", "39th and tro", "main", "westport",
 * "children's mercy". Returns intersections, landmarks and neighborhoods.
 */
export function suggestAddresses(query, limit = 8) {
  const q = norm(query)
  if (q.length < 2) return []
  const out = []
  const seen = new Set()
  const push = (s) => {
    if (out.length < limit && !seen.has(s.label)) {
      seen.add(s.label)
      out.push(s)
    }
  }

  const pushPlaces = () => {
    for (const site of city.sensitive_sites) {
      if (norm(site.name).includes(q)) {
        push({ label: site.name, sublabel: [site.type.replace('_', ' '), neighborhoodFor(site)].filter(Boolean).join(' · '), address: withSuffix(site.name), lat: site.lat, lng: site.lng, kind: 'place', source: 'gazetteer' })
      }
    }
    for (const n of city.neighborhoods) {
      if (norm(n.name).includes(q)) {
        push({ label: n.name, sublabel: ['Neighborhood', cityLabelShort()].filter(Boolean).join(' · '), address: withSuffix(n.name), lat: n.lat, lng: n.lng, kind: 'neighborhood', source: 'gazetteer' })
      }
    }
  }

  // "4500 Main" in grid cities (profile.address_grid): house number / per_block ≈ the numbered
  // cross street (4500 ≈ 45th St). Skipped for cities without such a grid.
  const numbered = cityProfile.address_grid && /^(\d{3,5})\s+(.+)$/.exec(q)
  if (numbered) {
    const house = Number(numbered[1])
    for (const st of matchStreets(numbered[2], 'ns').slice(0, 2)) {
      const lat = latForBlock(house)
      if (lat != null) {
        const point = { lat, lng: st.lng }
        push({
          label: `${house} ${st.name}`,
          sublabel: ['Approximate', reverseGeocode(point).address.split(',')[0], neighborhoodFor(point)].filter(Boolean).join(' · '),
          address: withSuffix(`${house} ${st.name}`),
          ...point,
          kind: 'address',
          source: 'gazetteer',
        })
      }
    }
  }

  const parts = (query || '').split(SEPARATORS).map(norm).filter(Boolean)
  if (parts.length >= 2) {
    // "A & B": first fragment picks streets, second picks cross streets on the other axis.
    for (const a of matchStreets(parts[0]).slice(0, 3)) {
      for (const b of matchStreets(parts[1], a.axis === 'ns' ? 'ew' : 'ns').slice(0, limit)) push(intersection(a, b))
    }
    pushPlaces()
  } else {
    // One fragment: maybe "troost 39" (two streets without a separator), else list a street's crossings.
    const words = q.split(' ')
    for (let i = 1; i < words.length && out.length === 0; i++) {
      const left = words.slice(0, i).join(' ')
      const right = words.slice(i).join(' ')
      for (const a of matchStreets(left).slice(0, 2)) {
        for (const b of matchStreets(right, a.axis === 'ns' ? 'ew' : 'ns').slice(0, limit)) push(intersection(a, b))
      }
    }
    // Named places before a street's crossings, so "westport" offers the neighborhood first.
    pushPlaces()
    for (const s of matchStreets(q).slice(0, 2)) {
      const crossings = city.streets
        .filter((x) => x.axis !== s.axis)
        // Busiest cross streets first so the list starts with useful corners.
        .sort((x, y) => ROAD_ORDER[x.road_type] - ROAD_ORDER[y.road_type])
      for (const c of crossings) push(intersection(s, c))
    }
  }

  return out
}
