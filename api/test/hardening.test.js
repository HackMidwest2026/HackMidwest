// Findings from the production stress test: privacy, validation, crew bookkeeping, burst
// latency and many live-update streams, exercised over HTTP against a fresh API.
import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, describe, test } from 'node:test'

process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'citycare-hardening-'))
process.env.CITYCARE_MODE = 'mock'
process.env.MOCK_DELAY_MS = '200' // keep the pacing delay on: the burst test checks it isn't serialized
process.env.PHOTON_URL = 'off'
delete process.env.SEED_SOURCE
delete process.env.DATABASE_URL
delete process.env.DISPATCHER_SIGNUP_CODE
delete process.env.DISPATCHER_OPEN_SIGNUP

const { app } = await import('../src/server.js')
const store = await import('../src/lib/store.js')

const warnings = []
process.on('warning', (w) => warnings.push(w.name))

let server
let base
let cookie = ''
before(async () => {
  await store.initStore()
  await store.resetState()
  server = app.listen(0)
  await new Promise((r) => server.once('listening', r))
  base = `http://127.0.0.1:${server.address().port}`
})
after(() => server.close())

async function call(method, path, body, { auth = false } = {}) {
  const res = await fetch(base + path, { method, headers: { 'Content-Type': 'application/json', ...(auth && cookie && { Cookie: cookie }) }, body: body && JSON.stringify(body) })
  const set = res.headers.get('set-cookie')
  if (set && auth) cookie = set.split(';')[0]
  return { status: res.status, body: await res.json().catch(() => null) }
}

describe('hardening', () => {
  test('the first dispatcher can sign up on a new site; after that sign-up is closed', async () => {
    assert.equal((await call('GET', '/api/auth/config')).body.signup, 'first')
    assert.equal((await call('POST', '/api/auth/signup', { name: 'Ops Lead', email: 'lead@city.gov', password: 'dispatch-2026' }, { auth: true })).status, 201)
    assert.equal((await call('GET', '/api/auth/config')).body.signup, 'closed')
    assert.equal((await call('POST', '/api/auth/signup', { name: 'Stranger', email: 'x@example.com', password: 'whatever-123' })).status, 403)
  })

  test("a duplicate report's response doesn't reveal another resident's contact", async () => {
    await call('POST', '/api/reports', { text: 'Huge pothole on Troost near 39th', lat: 39.0576, lng: -94.5716, reporter_contact: 'alice@example.com' })
    const dup = await call('POST', '/api/reports', { text: 'big pothole troost and 39th', lat: 39.05762, lng: -94.57161 })
    assert.equal(dup.status, 201)
    assert.equal(dup.body.merged, true)
    assert.equal(dup.body.issue.reports.length, 2)
    assert.ok(!JSON.stringify(dup.body).includes('alice@example.com'))
    // Public issue details leave it out too; a signed-in dispatcher sees it.
    assert.ok(!JSON.stringify((await call('GET', `/api/issues/${dup.body.issue.issue_id}`)).body).includes('alice@example.com'))
    assert.ok(JSON.stringify((await call('GET', `/api/issues/${dup.body.issue.issue_id}`, null, { auth: true })).body).includes('alice@example.com'))
  })

  test('coordinates must be numbers on Earth', async () => {
    for (const [lat, lng] of [[91, 181], [-91, 0], [0, -181], ['abc', -94.5], [39.1, null]]) {
      const r = await call('POST', '/api/reports', { text: 'pothole', lat, lng })
      assert.equal(r.status, 400, `lat=${lat} lng=${lng}`)
    }
    assert.equal((await call('GET', '/api/nearby?lat=95&lng=0')).status, 400)
    assert.equal((await call('GET', '/api/reverse-geocode?lat=abc&lng=0')).status, 400)
    // Edge values are fine.
    assert.equal((await call('POST', '/api/reports', { text: 'pothole at the date line', lat: -90, lng: 180 })).status, 201)
  })

  test("resolving twice doesn't change a crew's workload again; reopening restores it", async () => {
    const issue = (await call('POST', '/api/reports', { text: 'Streetlight out at Main and 39th', lat: 39.0574, lng: -94.5857 })).body.issue
    await call('POST', `/api/issues/${issue.issue_id}/approve`, {}, { auth: true })
    const crewId = (await call('GET', `/api/issues/${issue.issue_id}`, null, { auth: true })).body.assigned_crew
    const jobs = async () => (await call('GET', '/api/crews')).body.find((c) => c.crew_id === crewId).open_jobs
    const counts = [await jobs()]
    for (const status of ['resolved', 'resolved', 'in_progress', 'rejected']) {
      await call('PATCH', `/api/issues/${issue.issue_id}`, { status }, { auth: true })
      counts.push(await jobs())
    }
    const n = counts[0]
    assert.deepEqual(counts, [n, n - 1, n - 1, n, n - 1])
    // Approving a closed issue reopens it and counts the job once.
    await call('POST', `/api/issues/${issue.issue_id}/approve`, {}, { auth: true })
    assert.equal(await jobs(), n)
  })

  test('a burst of reports is not slowed by one pacing delay per report', async () => {
    const t0 = Date.now()
    const results = await Promise.all(Array.from({ length: 30 }, (_, i) => call('POST', '/api/reports', { text: `Graffiti on wall number ${i}`, lat: 39.0 + i * 0.004, lng: -94.45 })))
    const elapsed = Date.now() - t0
    assert.ok(results.every((r) => r.status === 201))
    // Serialized delays would take 30 x 200 ms = 6 s for dedup alone.
    assert.ok(elapsed < 4000, `30 concurrent reports took ${elapsed} ms`)
  })

  test('simultaneous duplicate reports still merge into one incident', async () => {
    const results = await Promise.all(Array.from({ length: 20 }, () => call('POST', '/api/reports', { text: 'Water main break flooding the street on Prospect', lat: 39.0802, lng: -94.5532 })))
    const ids = new Set(results.map((r) => r.body.issue.issue_id))
    assert.equal(ids.size, 1)
    assert.equal(store.getIssue([...ids][0]).report_count, 20)
  })

  test('150 open live-update streams work without listener warnings', async () => {
    const ctrls = Array.from({ length: 150 }, () => new AbortController())
    const responses = await Promise.all(ctrls.map((c) => fetch(base + '/api/stream', { signal: c.signal })))
    assert.ok(responses.every((r) => r.status === 200))
    // An event reaches a stream.
    const reader = responses[149].body.getReader()
    await call('POST', '/api/reports', { text: 'Dead deer in the road', lat: 39.02, lng: -94.6 })
    let text = ''
    while (!text.includes('event: issue')) text += new TextDecoder().decode((await reader.read()).value)
    ctrls.forEach((c) => c.abort())
    await new Promise((r) => setTimeout(r, 100))
    assert.ok(!warnings.includes('MaxListenersExceededWarning'), warnings.join(', '))
  })
})
