// Location resolution for any place: local city data first (fast, offline), then
// OpenStreetMap via Photon, then raw coordinates.
import { geocodeAddress, neighborhoodFor, reverseGeocode, suggestAddresses } from './geo.js'
import { photonGeocode, photonReverse, photonSuggest } from './photon.js'

/** { address, area } for a point. */
export async function describePoint(point) {
  const local = reverseGeocode(point)
  // Trust local intersections only when the point is actually near one.
  if (local.covered && local.offset_m != null && local.offset_m < 300) return { address: local.address, area: local.neighborhood }
  const osm = await photonReverse(point)
  if (osm) return { address: osm.address, area: neighborhoodFor(point) || osm.area }
  return { address: local.address, area: local.neighborhood }
}

/** Geocode free text (a report or a typed address) to { lat, lng, address, area } or null. */
export async function locateText(text, bias) {
  const local = geocodeAddress(text)
  if (local.found) return { lat: local.lat, lng: local.lng, address: local.address, area: neighborhoodFor(local) }
  const osm = await photonGeocode(text, bias)
  return osm ? { lat: osm.lat, lng: osm.lng, address: osm.address, area: neighborhoodFor(osm) || osm.area } : null
}

/** Autocomplete: local suggestions first, then OpenStreetMap results near `bias`. */
export async function suggest(query, bias, limit = 10) {
  const local = suggestAddresses(query, 8)
  const wantRemote = local.length < 5 || /\d+\s+\w/.test(query)
  const remote = wantRemote ? await photonSuggest(query, { limit: 6, bias }) : []
  const seen = new Set(local.map((s) => s.label.toLowerCase()))
  return [...local, ...remote.filter((s) => !seen.has(s.label.toLowerCase()))].slice(0, limit)
}
