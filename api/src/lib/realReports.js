// Real 311 service requests from a city's open-data portal (Socrata), used as the issue
// history the app starts with. Defaults to Kansas City (data.kcmo.org).
//
// The portal's dataset id and column names change over the years, so nothing is hard-coded:
// the importer finds the newest 311 dataset in the portal's catalog (or uses SEED_DATASET),
// reads its column list, and picks the columns it needs by name and type.
//
// Recent open requests become seed reports. Each successful download is cached in STATE_DIR
// so a restart without internet still shows real data; with no download and no cache the
// app falls back to the bundled sample reports.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { config } from '../config.js'
import { distanceM } from './geo.js'
import { city, cityProfile } from './data.js'

const TIMEOUT_MS = 20000

export function seedSettings(env = process.env) {
  const num = (k, d) => (env[k] === undefined || env[k] === '' ? d : Number(env[k]))
  return {
    source: (env.SEED_SOURCE || 'socrata').trim().toLowerCase(), // "socrata" (real data) or "sample"
    domain: (env.SEED_DOMAIN || 'data.kcmo.org').trim(),
    dataset: (env.SEED_DATASET || '').trim(), // Socrata id like abcd-1234; found automatically if empty
    days: num('SEED_DAYS', 60), // only requests opened in the last N days
    limit: num('SEED_LIMIT', 150), // at most this many reports
    radiusKm: num('SEED_RADIUS_KM', 40), // ignore points farther than this from the city center
    appToken: (env.SOCRATA_APP_TOKEN || '').trim(), // optional; raises Socrata's rate limit
  }
}

// ---------- category mapping ----------

// 311 request types (city wording) -> CityCare category/subcategory. First match wins.
const TYPE_MAP = [
  [/pot ?hole/, 'streets', 'pothole'],
  [/sidewalk/, 'streets', 'sidewalk'],
  [/curb/, 'streets', 'curb'],
  [/street ?light|light ?out|lighting|lamp/, 'traffic_lighting', 'streetlight_out'],
  [/signal/, 'traffic_lighting', 'traffic_signal'],
  [/\bsigns?\b|signage/, 'traffic_lighting', 'sign_damaged'],
  [/water main|main break/, 'water', 'main_break'],
  [/manhole/, 'water', 'open_manhole'],
  [/sewer|backup|back-up/, 'water', 'sewer_backup'],
  [/flood|drainage|storm ?water|inlet|ditch/, 'water', 'flooding'],
  [/leak|water/, 'water', 'leak'],
  [/illegal dump|dumping/, 'trash', 'illegal_dumping'],
  [/bulky/, 'trash', 'bulky_item'],
  [/missed|trash|recycl|garbage|refuse|solid waste|collection|cart/, 'trash', 'missed_pickup'],
  [/graffiti/, 'property', 'graffiti'],
  [/abandoned (auto|vehicle|car)|vehicle/, 'property', 'abandoned_vehicle'],
  [/weed|grass|overgrown|vegetation|nuisance/, 'property', 'overgrown_lot'],
  [/dangerous|vacant|structure|building/, 'property', 'dangerous_building'],
  [/tree|limb|branch|forestry/, 'parks_trees', 'fallen_tree'],
  [/park/, 'parks_trees', 'park_damage'],
  [/dead animal/, 'animals', 'dead_animal'],
  [/animal|stray|dog|cat\b/, 'animals', 'stray'],
  [/street|pavement|road|asphalt|alley/, 'streets', 'street_damage'],
]

export function mapType(text) {
  const t = (text || '').toLowerCase()
  const hit = TYPE_MAP.find(([re]) => re.test(t))
  return hit ? { category: hit[1], subcategory: hit[2] } : null
}

const CLOSED = /clos|resolv|complet|cancel|duplicate|withdrawn|invalid|no action/i

// ---------- column detection ----------

const pickByName = (cols, patterns) => {
  for (const re of patterns) {
    const c = cols.find((col) => re.test(col.fieldName))
    if (c) return c.fieldName
  }
  return null
}

/** Choose the columns we need from a Socrata column list [{ fieldName, dataTypeName }]. */
export function detectColumns(columns) {
  const cols = columns.filter((c) => c.fieldName && !c.fieldName.startsWith(':'))
  const dates = cols.filter((c) => /calendar_date|floating_timestamp|fixed_timestamp/.test(c.dataTypeName || ''))
  const opened =
    dates.find((c) => /creat|open|report|request|receiv|submit|start/.test(c.fieldName)) ||
    dates.find((c) => !/clos|resolv|complet|updat|modif|due|end/.test(c.fieldName))
  const point = cols.find((c) => /^(point|location)$/.test(c.dataTypeName || ''))
  return {
    id: pickByName(cols, [/^case_?id$/, /^case_?(no|num|number)$/, /^(service_)?request_?(id|number|no)$/, /^sr_?(id|number|no)$/, /^incident_?(id|number)$/, /^id$/, /case|ticket/]),
    opened: opened?.fieldName || null,
    openedIsDate: !!opened,
    status: pickByName(cols, [/^status$/, /^case_?status$/, /^(current|request)_?status$/, /status/]),
    text: [
      pickByName(cols, [/^request_?type$/, /^type$/, /^issue_?type$/, /^service_?type$/, /^case_?type$/]),
      pickByName(cols, [/^category$/, /^request_?category$/]),
      pickByName(cols, [/^detail$/, /^type_?detail$/, /^sub_?type$/, /^description$/, /^request_?description$/]),
    ].filter((v, i, a) => v && a.indexOf(v) === i),
    department: pickByName(cols, [/^department$/, /^work_?group$/, /^dept/]),
    address: pickByName(cols, [/^street_?address$/, /^incident_?address$/, /^address$/, /^location_?address$/, /address/]),
    neighborhood: pickByName(cols, [/^neighborhood$/, /neighborhood/]),
    url: pickByName(cols, [/^case_?url$/, /url/]),
    point: point?.fieldName || null,
    lat: pickByName(cols.filter((c) => c.dataTypeName === 'number' || c.dataTypeName === 'text'), [/^latitude$/, /^lat$/, /latitude/, /^y_?coord/, /^ycoordinate$/]),
    lng: pickByName(cols.filter((c) => c.dataTypeName === 'number' || c.dataTypeName === 'text'), [/^longitude$/, /^lon$/, /^lng$/, /longitude/, /^x_?coord/, /^xcoordinate$/]),
  }
}

function coords(row, cols) {
  const p = cols.point && row[cols.point]
  let lat
  let lng
  if (p?.coordinates) [lng, lat] = p.coordinates
  else if (p && (p.latitude || p.longitude)) [lat, lng] = [p.latitude, p.longitude]
  if (lat == null && cols.lat) [lat, lng] = [row[cols.lat], row[cols.lng]]
  lat = Number(lat)
  lng = Number(lng)
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 && (lat || lng) ? { lat, lng } : null
}

const clean = (s) => String(s ?? '').replace(/\s+/g, ' ').trim()

/** One Socrata row -> a seed report, or null if it can't be placed or categorized. */
export function rowToReport(row, cols, { center, radiusKm, now = Date.now() }) {
  const pos = coords(row, cols)
  if (!pos || (center && distanceM(pos, center) > radiusKm * 1000)) return null
  const parts = cols.text.map((f) => clean(row[f])).filter(Boolean)
  const unique = parts.filter((p, i) => parts.findIndex((q) => q.toLowerCase() === p.toLowerCase()) === i)
  const typeText = unique.join(' - ')
  // The request type decides; the department only helps when the type is vague.
  const mapped = mapType(typeText) || mapType(clean(row[cols.department]))
  if (!mapped) return null
  const openedAt = cols.opened && row[cols.opened] ? new Date(row[cols.opened]) : null
  const created = openedAt && !Number.isNaN(openedAt.getTime()) && openedAt.getTime() <= now ? openedAt.toISOString() : null
  const address = clean(row[cols.address])
  const id = clean(row[cols.id])
  return {
    raw_text: typeText || mapped.subcategory.replace(/_/g, ' '),
    lat: +pos.lat.toFixed(6),
    lng: +pos.lng.toFixed(6),
    address: address ? `${address.replace(/,?\s*$/, '')}${/,/.test(address) ? '' : cityProfile.name ? `, ${cityProfile.name}${cityProfile.region ? `, ${cityProfile.region}` : ''}` : ''}` : null,
    category_hint: mapped.category,
    ...(created ? { created_at: created } : { days_ago: 1 }),
    source: 'open_data_311',
    external_id: id || null,
    external_status: clean(row[cols.status]) || null,
    ...(cols.url && row[cols.url] ? { external_url: typeof row[cols.url] === 'object' ? row[cols.url].url : clean(row[cols.url]) } : {}),
  }
}

// ---------- Socrata API ----------

// SEED_DOMAIN is a host (data.kcmo.org) or a full base URL (http://localhost:9999 in tests).
const baseUrl = (domain) => (/^https?:\/\//.test(domain) ? domain.replace(/\/$/, '') : `https://${domain}`)
const hostOf = (domain) => new URL(baseUrl(domain)).host

async function getJson(url, appToken) {
  const res = await fetch(url, {
    signal: AbortSignal.timeout(TIMEOUT_MS),
    headers: { Accept: 'application/json', 'User-Agent': 'CityCare/0.1 (hackathon demo)', ...(appToken && { 'X-App-Token': appToken }) },
  }).catch((err) => {
    throw new Error(`can't reach ${new URL(url).host} (${err.cause?.code || err.cause?.message || err.name})`)
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} from ${new URL(url).host}`)
  return res.json()
}

/** Find the newest 311 service-request dataset on a Socrata portal. */
export async function findDataset(s) {
  const q = new URLSearchParams({ domains: hostOf(s.domain), search_context: hostOf(s.domain), q: '311', only: 'datasets', limit: '50' })
  const { results = [] } = await getJson(`${baseUrl(s.domain)}/api/catalog/v1?${q}`, s.appToken)
  const candidates = results
    .map((r) => r.resource || {})
    .filter((r) => /311/.test(r.name || '') && /request|case|call|service/i.test(r.name || ''))
    .filter((r) => !/summary|count|by month|by year|statistic|dashboard|performance/i.test(r.name || ''))
    .filter((r) => (r.columns_datatype || []).some((t) => /point|location/.test(t)) || (r.columns_field_name || []).some((f) => /lat|y_?coord/.test(f)))
    .sort((a, b) => String(b.data_updated_at || '').localeCompare(String(a.data_updated_at || '')))
  if (!candidates.length) throw new Error(`no 311 service request dataset found on ${s.domain}; set SEED_DATASET`)
  return { id: candidates[0].id, name: candidates[0].name }
}

export async function fetchRealReports(s = seedSettings()) {
  const ds = s.dataset ? { id: s.dataset, name: s.dataset } : await findDataset(s)
  const view = await getJson(`${baseUrl(s.domain)}/api/views/${ds.id}.json`, s.appToken)
  const cols = detectColumns(view.columns || [])
  if (!cols.point && !cols.lat) throw new Error(`dataset ${ds.id} has no location column`)
  if (!cols.text.length) throw new Error(`dataset ${ds.id} has no request type column`)

  const since = new Date(Date.now() - s.days * 86400000).toISOString().slice(0, 19)
  const params = new URLSearchParams({ $limit: String(Math.max(s.limit * 8, 1000)) })
  if (cols.opened && cols.openedIsDate) {
    params.set('$where', `${cols.opened} >= '${since}'`)
    params.set('$order', `${cols.opened} DESC`)
  } else {
    params.set('$order', ':created_at DESC') // row creation time, when the dataset has no usable date column
  }
  const rows = await getJson(`${baseUrl(s.domain)}/resource/${ds.id}.json?${params}`, s.appToken)

  const center = city.center ? { lat: city.center.lat, lng: city.center.lng } : null
  const newest = (a, b) => String(b.created_at || '').localeCompare(String(a.created_at || ''))
  const all = rows.map((r) => rowToReport(r, cols, { center, radiusKm: s.radiusKm })).filter(Boolean).sort(newest)
  const open = all.filter((r) => !r.external_status || !CLOSED.test(r.external_status))
  // Prefer requests still open; top up with recently closed ones if there are few.
  const chosen = (open.length >= Math.min(20, s.limit) ? open : [...open, ...all.filter((r) => !open.includes(r))]).slice(0, s.limit)
  if (!chosen.length) throw new Error(`dataset ${ds.id} returned no usable requests from the last ${s.days} days`)
  return {
    reports: chosen.reverse(), // the newest `limit` requests, oldest first (the order they were reported)
    meta: { domain: s.domain, dataset: ds.id, dataset_name: view.name || ds.name, fetched_at: new Date().toISOString(), rows: rows.length, usable: all.length, open: open.length, columns: cols },
  }
}

// ---------- seed selection with cache and fallback ----------

const cachePath = () => join(config.stateDir, 'real_311_cache.json')
let memo = null

/**
 * The reports to start the app with: { reports, source, description }.
 * Real 311 data when available (fresh, else cached), otherwise the bundled sample.
 * `refresh` re-downloads instead of reusing this process's last result.
 */
export async function loadSeedReports(sampleReports, { refresh = false, settings = seedSettings(), log = console } = {}) {
  if (settings.source === 'sample') return { reports: sampleReports, source: 'sample', description: 'bundled sample reports (SEED_SOURCE=sample)' }
  if (memo && !refresh) return memo
  try {
    const { reports, meta } = await fetchRealReports(settings)
    try {
      mkdirSync(config.stateDir, { recursive: true })
      writeFileSync(cachePath(), JSON.stringify({ meta, reports }))
    } catch {
      // The cache is a convenience; a read-only disk is fine.
    }
    memo = { reports, source: 'live', description: `${reports.length} real 311 requests from ${meta.dataset_name} (${settings.domain}, dataset ${meta.dataset})`, meta }
    return memo
  } catch (err) {
    try {
      const cached = JSON.parse(readFileSync(cachePath(), 'utf8'))
      log.warn(`[seed] Could not download 311 data (${err.message}). Using the copy saved ${cached.meta.fetched_at}.`)
      memo = { reports: cached.reports, source: 'cache', description: `${cached.reports.length} real 311 requests saved ${cached.meta.fetched_at} from ${cached.meta.dataset_name}`, meta: cached.meta }
      return memo
    } catch {
      log.warn(`[seed] Could not download 311 data (${err.message}) and no saved copy exists. Using the bundled sample reports.`)
      return { reports: sampleReports, source: 'sample', description: 'bundled sample reports (311 data unavailable)' }
    }
  }
}
