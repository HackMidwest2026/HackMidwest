// "Import new 311 requests" on the AI Triage Pipeline screen, against a local stand-in for the
// city's Socrata open-data portal.
import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { createServer } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, describe, test } from 'node:test'

process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'citycare-import-'))
process.env.CITYCARE_MODE = 'mock'
process.env.MOCK_DELAY_MS = '0'
process.env.MOCK_BATCH_DELAY_MS = '0'
process.env.PHOTON_URL = 'off'
process.env.SEED_SOURCE = 'sample' // start from the bundled history; switched to the portal below
process.env.IMPORT_LIMIT = '3'
delete process.env.DATABASE_URL

const { app } = await import('../src/server.js')
const store = await import('../src/lib/store.js')
const { seedReports } = await import('../src/lib/data.js')
const { seedHistory } = await import('../src/pipeline.js')

const ago = (d) => new Date(Date.now() - d * 86400000).toISOString().slice(0, 19)
const point = (lat, lng) => ({ type: 'Point', coordinates: [lng, lat] })
let rows = [
  { case_id: 'KC-1', creation_date: ago(4), status: 'OPEN', request_type: 'Streets - Pothole', street_address: '3900 TROOST AVE', location: point(39.0576, -94.5716) },
  { case_id: 'KC-2', creation_date: ago(3), status: 'OPEN', request_type: 'Water Main Break', street_address: '4700 BROADWAY BLVD', location: point(39.0418, -94.5916) },
  { case_id: 'KC-3', creation_date: ago(2), status: 'OPEN', request_type: 'Dead Animal', street_address: '600 MAIN ST', location: point(39.105, -94.5835) },
  { case_id: 'KC-4', creation_date: ago(1), status: 'OPEN', request_type: 'Graffiti', street_address: '1200 E 18TH ST', location: point(39.0915, -94.563) },
]

let portal
let api
before(async () => {
  portal = createServer((req, res) => {
    const url = new URL(req.url, 'http://x')
    const send = (body) => res.writeHead(200, { 'Content-Type': 'application/json' }).end(JSON.stringify(body))
    if (url.pathname === '/api/catalog/v1') return send({ results: [{ resource: { id: 'abcd-1111', name: '311 Call Center Service Requests', data_updated_at: '2026-10-10T00:00:00Z', columns_datatype: ['point'], columns_field_name: ['location'] } }] })
    if (url.pathname === '/api/views/abcd-1111.json')
      return send({ name: '311 Call Center Service Requests', columns: [['case_id', 'text'], ['creation_date', 'calendar_date'], ['status', 'text'], ['request_type', 'text'], ['street_address', 'text'], ['location', 'point']].map(([fieldName, dataTypeName]) => ({ fieldName, dataTypeName })) })
    if (url.pathname === '/resource/abcd-1111.json') return send(rows)
    res.writeHead(404).end()
  })
  await new Promise((r) => portal.listen(0, '127.0.0.1', r))
  await store.initStore()
  await store.resetState()
  await seedHistory(seedReports)
  const server = app.listen(0)
  await new Promise((r) => server.once('listening', r))
  api = { server, base: `http://127.0.0.1:${server.address().port}` }
})
after(() => {
  portal.close()
  api.server.close()
})

let cookie = ''
async function call(method, path, body) {
  const res = await fetch(api.base + path, { method, headers: { 'Content-Type': 'application/json', ...(cookie && { Cookie: cookie }) }, body: body && JSON.stringify(body) })
  const set = res.headers.get('set-cookie')
  if (set) cookie = set.split(';')[0]
  return { status: res.status, body: await res.json() }
}

describe('311 import', () => {
  test('needs a dispatcher login', async () => {
    assert.equal((await call('POST', '/api/import/311', {})).status, 401)
    assert.equal((await call('POST', '/api/auth/signup', { name: 'Jordan Rivera', email: 'jordan@city.gov', password: 'dispatch-2026' })).status, 201)
  })

  test('is refused while 311 data is turned off', async () => {
    const r = await call('POST', '/api/import/311', {})
    assert.equal(r.status, 400)
    assert.match(r.body.error, /turned off/)
    process.env.SEED_SOURCE = 'socrata'
    process.env.SEED_DOMAIN = `http://127.0.0.1:${portal.address().port}`
  })

  test('imports the newest requests, up to IMPORT_LIMIT, and keeps their case numbers', async () => {
    const r = await call('POST', '/api/import/311', {})
    assert.equal(r.status, 200)
    assert.equal(r.body.reports, 3)
    assert.equal(r.body.fetched, 4)
    assert.equal(r.body.already_imported, 0)
    assert.equal(r.body.waiting, 1)
    assert.equal(r.body.dataset, '311 Call Center Service Requests')
    const imported = store.listReports().filter((x) => x.source === 'open_data_311')
    assert.deepEqual(imported.map((x) => x.external_id).sort(), ['KC-2', 'KC-3', 'KC-4']) // the newest three
    // The case number and status show in the incident's reports.
    const kc = imported.find((x) => x.external_id === 'KC-2')
    const detail = await call('GET', `/api/issues/${kc.issue_id}`)
    assert.ok(detail.body.reports.some((x) => x.external_id === 'KC-2' && x.external_status === 'OPEN'))
    assert.equal(store.getLastBatch().reports, 3)
  })

  test('a second import only takes what is new', async () => {
    const again = await call('POST', '/api/import/311', {})
    assert.equal(again.body.reports, 1) // KC-1, left waiting last time
    assert.equal(again.body.already_imported, 3)
    const none = await call('POST', '/api/import/311', {})
    assert.equal(none.body.reports, 0)
    assert.match(none.body.message, /No new 311 requests/)
    rows = [...rows, { case_id: 'KC-5', creation_date: ago(0.1), status: 'OPEN', request_type: 'Street Light Out', street_address: '3900 MAIN ST', location: point(39.0574, -94.5857) }]
    const fresh = await call('POST', '/api/import/311', {})
    assert.equal(fresh.body.reports, 1)
    assert.ok(store.listReports().some((x) => x.external_id === 'KC-5'))
  })

  test('a portal outage is reported, not hidden behind sample data', async () => {
    process.env.SEED_DOMAIN = 'http://127.0.0.1:9'
    const r = await call('POST', '/api/import/311', {})
    assert.equal(r.status, 502)
    assert.match(r.body.error, /Could not get 311 data/)
  })
})
