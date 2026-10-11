// Real 311 import, against a local stand-in for a Socrata open-data portal (no internet).
import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { createServer } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, describe, test } from 'node:test'

process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'citycare-311-'))
process.env.CITYCARE_MODE = 'mock'
process.env.MOCK_DELAY_MS = '0'
process.env.PHOTON_URL = 'off'

const { detectColumns, fetchRealReports, loadSeedReports, mapType, seedSettings } = await import('../src/lib/realReports.js')
const { seedHistory } = await import('../src/pipeline.js')
const store = await import('../src/lib/store.js')

const daysAgo = (d) => new Date(Date.now() - d * 86400000).toISOString().slice(0, 19)

// Two portal layouts seen in the wild: a point column, and separate latitude/longitude text columns.
const DATASETS = {
  'abcd-1111': {
    name: '311 Call Center Service Requests',
    columns: [
      ['case_id', 'text'], ['creation_date', 'calendar_date'], ['status', 'text'], ['department', 'text'], ['request_type', 'text'],
      ['category', 'text'], ['type', 'text'], ['detail', 'text'], ['street_address', 'text'], ['neighborhood', 'text'], ['location', 'point'],
    ],
    rows: [
      { case_id: '2026001', creation_date: daysAgo(5), status: 'OPEN', department: 'Public Works', request_type: 'Streets - Pothole', category: 'Streets', type: 'Pothole', street_address: '3900 TROOST AVE', location: { type: 'Point', coordinates: [-94.5716, 39.0576] } },
      { case_id: '2026002', creation_date: daysAgo(4), status: 'OPEN', department: 'Public Works', request_type: 'Streets - Pothole', category: 'Streets', type: 'Pothole', street_address: '3902 TROOST AVE', location: { type: 'Point', coordinates: [-94.57162, 39.05765] } },
      { case_id: '2026003', creation_date: daysAgo(3), status: 'ASSIGNED', department: 'Water Services', request_type: 'Water Main Break', street_address: '4700 BROADWAY BLVD', location: { type: 'Point', coordinates: [-94.5916, 39.0418] } },
      { case_id: '2026004', creation_date: daysAgo(2.5), status: 'OPEN', department: 'Solid Waste', request_type: 'Trash - Missed Pickup', street_address: '1200 E 18TH ST', location: { type: 'Point', coordinates: [-94.563, 39.0915] } },
      { case_id: '2026005', creation_date: daysAgo(2), status: 'OPEN', department: 'Solid Waste', request_type: 'Dead Animal', street_address: '600 MAIN ST', location: { type: 'Point', coordinates: [-94.5835, 39.105] } },
      { case_id: '2026006', creation_date: daysAgo(1), status: 'CLOSED', department: 'Public Works', request_type: 'Street Light Out', street_address: '3900 MAIN ST', location: { type: 'Point', coordinates: [-94.5857, 39.0574] } },
      { case_id: '2026007', creation_date: daysAgo(1), status: 'OPEN', department: 'Finance', request_type: 'Tax Question', street_address: '414 E 12TH ST', location: { type: 'Point', coordinates: [-94.5786, 39.1003] } },
      { case_id: '2026008', creation_date: daysAgo(1), status: 'OPEN', department: 'Public Works', request_type: 'Pothole', street_address: 'NO LOCATION' },
      { case_id: '2026009', creation_date: daysAgo(1), status: 'OPEN', department: 'Public Works', request_type: 'Pothole', street_address: '100 MAIN ST, ST LOUIS', location: { type: 'Point', coordinates: [-90.19, 38.63] } },
    ],
  },
  'efgh-2222': {
    name: 'Service Requests 311 (2015-2020)',
    columns: [['request_id', 'text'], ['open_date', 'calendar_date'], ['issue_type', 'text'], ['latitude', 'text'], ['longitude', 'text']],
    rows: [{ request_id: 'X1', open_date: daysAgo(10), issue_type: 'Graffiti', latitude: '39.04', longitude: '-94.59' }],
  },
}

let server
let base
const hits = []
before(async () => {
  server = createServer((req, res) => {
    const url = new URL(req.url, 'http://x')
    hits.push(url.pathname + url.search)
    const send = (code, body) => res.writeHead(code, { 'Content-Type': 'application/json' }).end(JSON.stringify(body))
    if (url.pathname === '/api/catalog/v1') {
      return send(200, {
        results: [
          { resource: { id: 'zzzz-0000', name: '311 Requests by Month (summary)', data_updated_at: '2026-10-01T00:00:00Z', columns_datatype: ['text'], columns_field_name: ['month'] } },
          { resource: { id: 'efgh-2222', name: DATASETS['efgh-2222'].name, data_updated_at: '2021-01-01T00:00:00Z', columns_datatype: ['text'], columns_field_name: ['latitude', 'longitude'] } },
          { resource: { id: 'abcd-1111', name: DATASETS['abcd-1111'].name, data_updated_at: '2026-10-10T00:00:00Z', columns_datatype: ['text', 'point'], columns_field_name: ['case_id', 'location'] } },
        ],
      })
    }
    const view = /^\/api\/views\/([\w-]+)\.json$/.exec(url.pathname)
    if (view && DATASETS[view[1]]) {
      return send(200, { name: DATASETS[view[1]].name, columns: DATASETS[view[1]].columns.map(([fieldName, dataTypeName]) => ({ fieldName, dataTypeName })) })
    }
    const rows = /^\/resource\/([\w-]+)\.json$/.exec(url.pathname)
    if (rows && DATASETS[rows[1]]) return send(200, DATASETS[rows[1]].rows)
    send(404, { error: 'not found' })
  })
  await new Promise((r) => server.listen(0, '127.0.0.1', r))
  base = `http://127.0.0.1:${server.address().port}`
})
after(() => server.close())

describe('real 311 data', () => {
  test('maps 311 request types to CityCare categories', () => {
    assert.deepEqual(mapType('Streets - Pothole'), { category: 'streets', subcategory: 'pothole' })
    assert.deepEqual(mapType('Street Light Out'), { category: 'traffic_lighting', subcategory: 'streetlight_out' })
    assert.deepEqual(mapType('Traffic Signal Malfunction'), { category: 'traffic_lighting', subcategory: 'traffic_signal' })
    assert.deepEqual(mapType('Water Main Break'), { category: 'water', subcategory: 'main_break' })
    assert.deepEqual(mapType('Dead Animal'), { category: 'animals', subcategory: 'dead_animal' })
    assert.deepEqual(mapType('Abandoned Vehicle'), { category: 'property', subcategory: 'abandoned_vehicle' })
    assert.equal(mapType('Tax Question'), null)
  })

  test('finds columns by name and type', () => {
    const cols = detectColumns(DATASETS['abcd-1111'].columns.map(([fieldName, dataTypeName]) => ({ fieldName, dataTypeName })))
    assert.equal(cols.id, 'case_id')
    assert.equal(cols.opened, 'creation_date')
    assert.equal(cols.status, 'status')
    assert.equal(cols.point, 'location')
    assert.deepEqual(cols.text, ['request_type', 'category', 'detail'])
    const other = detectColumns(DATASETS['efgh-2222'].columns.map(([fieldName, dataTypeName]) => ({ fieldName, dataTypeName })))
    assert.equal(other.lat, 'latitude')
    assert.equal(other.lng, 'longitude')
    assert.equal(other.opened, 'open_date')
  })

  test('downloads open requests from the newest 311 dataset and seeds issues from them', async () => {
    const { reports, meta } = await fetchRealReports({ ...seedSettings({}), domain: base, limit: 5 })
    assert.equal(meta.dataset, 'abcd-1111') // newest real 311 dataset, not the summary or the old one
    assert.ok(hits.some((h) => h.startsWith('/resource/abcd-1111.json') && h.includes('creation_date') && h.includes('%24where')))
    // Closed, non-field (tax), unlocated and out-of-town requests are left out.
    assert.deepEqual(reports.map((r) => r.external_id), ['2026001', '2026002', '2026003', '2026004', '2026005'])
    const pothole = reports[0]
    assert.equal(pothole.category_hint, 'streets')
    assert.equal(pothole.lat, 39.0576)
    assert.match(pothole.address, /^3900 TROOST AVE, Kansas City/)
    assert.ok(pothole.created_at < reports[4].created_at) // oldest first, with real dates

    store.resetState()
    const m = await seedHistory(reports)
    assert.equal(m.reports, 5)
    const issues = store.listIssues()
    // The two Troost pothole reports a few meters apart merge into one issue.
    const merged = issues.find((i) => i.subcategory === 'pothole')
    assert.equal(merged.report_count, 2)
    assert.equal(merged.first_reported_at.slice(0, 10), reports[0].created_at.slice(0, 10))
    assert.deepEqual(issues.map((i) => i.category).sort(), ['animals', 'streets', 'trash', 'water'])
    assert.equal(issues.find((i) => i.category === 'water').subcategory, 'main_break')
  })

  test('tops up with recently closed requests when few are still open', async () => {
    const { reports } = await fetchRealReports({ ...seedSettings({}), domain: base, limit: 50 })
    assert.equal(reports.length, 6)
    assert.equal(reports.find((r) => r.external_id === '2026006').external_status, 'CLOSED')
  })

  test('falls back to the saved copy, then to the sample data, when the portal is unreachable', async () => {
    const quiet = { warn: () => {} }
    const live = await loadSeedReports([], { refresh: true, settings: { ...seedSettings({}), domain: base }, log: quiet })
    assert.equal(live.source, 'live')
    const cached = await loadSeedReports([], { refresh: true, settings: { ...seedSettings({}), domain: 'http://127.0.0.1:9' }, log: quiet })
    assert.equal(cached.source, 'cache')
    assert.equal(cached.reports.length, live.reports.length)
    process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'citycare-311-empty-'))
    const { config } = await import('../src/config.js')
    config.stateDir = process.env.STATE_DIR
    const sample = await loadSeedReports([{ raw_text: 'sample' }], { refresh: true, settings: { ...seedSettings({}), domain: 'http://127.0.0.1:9' }, log: quiet })
    assert.equal(sample.source, 'sample')
    const forced = await loadSeedReports([{ raw_text: 'sample' }], { settings: seedSettings({ SEED_SOURCE: 'sample' }) })
    assert.equal(forced.source, 'sample')
  })
})
