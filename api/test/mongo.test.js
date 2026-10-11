// MongoDB (Prisma) persistence, end to end against a real database. Skipped unless
// TEST_DATABASE_URL points at a disposable MongoDB replica set, e.g.
//   TEST_DATABASE_URL="mongodb://localhost:27017/citycare_test?replicaSet=rs0&directConnection=true" npm test
// The database's CityCare collections are wiped by this test.
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, test } from 'node:test'

const url = process.env.TEST_DATABASE_URL
const env = { ...process.env, DATABASE_URL: url, CITYCARE_MODE: 'mock', MOCK_DELAY_MS: '0', MOCK_BATCH_DELAY_MS: '0', PHOTON_URL: 'off', STATE_DIR: mkdtempSync(join(tmpdir(), 'citycare-mongo-')) }

/** Run a snippet in a fresh Node process (fresh in-memory state) and return its JSON output. */
function run(code) {
  const out = execFileSync(process.execPath, ['--input-type=module', '-e', code], { cwd: join(import.meta.dirname, '..'), env, encoding: 'utf8' })
  return JSON.parse(out.trim().split('\n').pop())
}

describe('MongoDB persistence', { skip: !url && 'set TEST_DATABASE_URL to run' }, () => {
  test('data written by one API process is loaded by the next', () => {
    const PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    const first = run(`
      const store = await import('./src/lib/store.js')
      const { seedReports } = await import('./src/lib/data.js')
      const { seedHistory, processReport } = await import('./src/pipeline.js')
      await store.initStore(); await store.resetState()
      await seedHistory(seedReports)
      const photo_url = await store.savePhoto(${JSON.stringify(PNG)})
      const r = await processReport({ raw_text: 'Huge pothole on Troost near 39th, almost wrecked my car', lat: 39.0576, lng: -94.5716, photo_url, category_hint: 'streets' })
      store.updateIssue(r.issue.issue_id, { status: 'assigned', assigned_crew: 'streets_b' })
      store.updateCrew('streets_b', (c) => ({ open_jobs: c.open_jobs + 1 }))
      store.setLastBatch({ reports: 50, issues: 12 })
      await store.closeStore()
      console.log(JSON.stringify({ issues: store.listIssues().length, reports: store.listReports().length, issue: store.getIssue(r.issue.issue_id), report: store.getReport(r.report.report_id), crew: store.getCrew('streets_b'), photo_url }))
    `)
    assert.ok(first.issues >= 8 && first.reports >= 14)

    const second = run(`
      const store = await import('./src/lib/store.js')
      const loaded = await store.initStore()
      const photo = await store.readPhoto(${JSON.stringify(first.photo_url)}.split('/').pop())
      const issues = store.listIssues().length
      const next = await store.createIssue({ summary: 'counter check' })
      console.log(JSON.stringify({ loaded, issues, reports: store.listReports().length,
        issue: store.getIssue(${first.issue.issue_id}), report: store.getReport(${JSON.stringify(first.report.report_id)}),
        crew: store.getCrew('streets_b'), lastBatch: store.getLastBatch(), photoBytes: photo?.bytes.length, photoMime: photo?.mime,
        nextIssueId: next.issue_id, info: store.storeInfo() }))
      await store.closeStore()
    `)
    assert.equal(second.loaded, true)
    assert.equal(second.info.backend, 'mongodb')
    assert.equal(second.issues, first.issues)
    assert.equal(second.reports, first.reports)
    // Full records round-trip, including nested JSON, arrays, dates and fields kept in `extra`.
    assert.deepEqual(second.issue, first.issue)
    assert.deepEqual(second.report, first.report)
    assert.equal(second.issue.status, 'assigned')
    assert.ok(second.issue.agent_trace.length > 3)
    assert.equal(second.report.category_hint, 'streets')
    assert.deepEqual(second.crew, first.crew)
    assert.deepEqual(second.lastBatch, { reports: 50, issues: 12 })
    assert.equal(second.photoMime, 'image/jpeg') // every photo is stored as JPEG (lib/images.js)
    assert.ok(second.photoBytes > 50)
    // ID counters persist, so new issues never reuse an old number.
    assert.ok(second.nextIssueId > first.issue.issue_id)
  })

  test('instances sharing the database never reuse a number and see each other\'s issues', () => {
    const r = run(`
      const a = await import('./src/lib/store.js?a')
      const b = await import('./src/lib/store.js?b')
      await a.initStore(); await a.resetState(); await a.flush()
      await b.initStore()
      // Both instances create issues at the same time.
      const made = await Promise.all(Array.from({ length: 20 }, (_, i) => (i % 2 ? a : b).createIssue({ summary: 'n' + i, lat: 39, lng: -94.5 })))
      await a.flush(); await b.flush()
      const seen = []
      b.onRemoteChange((e) => e.type === 'issue' && seen.push(e.issue.issue_id))
      await b.syncOnce()
      const aOnly = made.filter((_, i) => i % 2).map((x) => x.issue_id)
      const bSees = b.listIssues().map((x) => x.issue_id)
      // A reset on one instance makes the other reload.
      let reloaded = false
      b.onRemoteChange((e) => e.type === 'reload' && (reloaded = true))
      await a.resetState()
      await b.syncOnce()
      console.log(JSON.stringify({ ids: made.map((x) => x.issue_id), aOnly, bSees, seen, reloaded, afterReset: b.listIssues().length }))
      await a.closeStore(); await b.closeStore()
    `)
    assert.equal(new Set(r.ids).size, 20)
    assert.ok(r.aOnly.every((id) => r.bSees.includes(id)))
    assert.deepEqual([...r.seen].sort(), [...r.aOnly].sort())
    assert.equal(r.reloaded, true)
    assert.equal(r.afterReset, 0)
  })

  test('demo reset wipes the database', () => {
    const r = run(`
      const store = await import('./src/lib/store.js')
      await store.initStore(); await store.resetState(); await store.closeStore()
      const again = await import('./src/lib/store.js?again')
      await again.initStore()
      console.log(JSON.stringify({ issues: again.listIssues().length, reports: again.listReports().length, crews: again.listCrews().length }))
      await again.closeStore()
    `)
    // Issues and reports are gone; the seed crews are written back.
    assert.equal(r.issues, 0)
    assert.equal(r.reports, 0)
    assert.ok(r.crews > 0)
  })
})
