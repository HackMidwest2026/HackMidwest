import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { before, describe, test } from 'node:test'

// Isolated state, rule-based engine, no artificial delay. Must be set before importing the app.
process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'cityops-test-'))
process.env.CITYOPS_MODE = 'mock'
process.env.MOCK_DELAY_MS = '0'
process.env.MOCK_BATCH_DELAY_MS = '0'

const { classifyText, detectHazards, baseScore, tierFor } = await import('../src/agents/rules.js')
const { geocodeAddress, roadType } = await import('../src/lib/geo.js')
const { demoReports, seedReports } = await import('../src/lib/data.js')
const store = await import('../src/lib/store.js')
const { processBatch, processReport, seedHistory } = await import('../src/pipeline.js')

describe('rules', () => {
  test('classifies messy text', () => {
    assert.equal(classifyText('main & 31st pot hole is HUGE').subcategory, 'pothole')
    assert.equal(classifyText('its pitch black at troost and linwood, light is out').subcategory, 'streetlight_out')
    assert.equal(classifyText('stoplight dead at 47th & prospect!!').subcategory, 'traffic_signal')
    assert.equal(classifyText('asdf qwerty').category, 'other')
  })

  test('detects hazard phrases without reporting overlapping fragments', () => {
    const hz = detectHazards('Huge pothole, almost wrecked my car', 'pothole', 'streets')
    assert.deepEqual(hz.phrases, ['almost wrecked'])
    assert.ok(hz.flags.includes('vehicle_damage_risk'))
  })

  test('priority rubric and tiers', () => {
    const issue = { hazard_flags: ['vehicle_damage_risk'], report_count: 4 }
    const ctx = { road: { road_type: 'arterial', street: 'Troost Ave' }, sites: [], days_open: 6.2 }
    const { base_score } = baseScore(issue, ctx)
    assert.equal(base_score, 40 + 15 + 9 + 10)
    assert.equal(tierFor(80), 'P1')
    assert.equal(tierFor(79), 'P2')
    assert.equal(tierFor(39), 'P4')
  })

  test('critical hazards reach the P1 floor on their first report', () => {
    const ctx = { road: { road_type: 'arterial', street: 'Main St' }, sites: [], days_open: 0 }
    const signal = baseScore({ subcategory: 'traffic_signal', hazard_flags: ['inherent_safety_hazard'], report_count: 1 }, ctx)
    assert.equal(signal.base_score, 80)
    assert.ok(signal.factors.some((f) => f.factor === 'critical_hazard' && f.points === 25))
    const tree = (flags) => baseScore({ subcategory: 'fallen_tree', hazard_flags: flags, report_count: 1 }, ctx).base_score
    assert.equal(tree(['inherent_safety_hazard', 'road_blocked']), 80)
    assert.equal(tree(['inherent_safety_hazard']), 55)
    const pothole = baseScore({ subcategory: 'pothole', hazard_flags: ['vehicle_damage_risk'], report_count: 1 }, ctx)
    assert.equal(pothole.base_score, 55)
  })
})

describe('geo', () => {
  test('geocodes an intersection from free text', () => {
    const g = geocodeAddress('Huge pothole on Troost near 39th')
    assert.equal(g.found, true)
    assert.match(g.address, /Troost Ave & 39th St/)
  })

  test('road type picks the highest class nearby', () => {
    assert.equal(roadType({ lat: 39.0574, lng: -94.5715 }).road_type, 'arterial')
  })
})

describe('pipeline', () => {
  before(async () => {
    store.resetState()
    await seedHistory(seedReports)
  })

  test('demo report merges into the seeded Troost & 39th pothole', async () => {
    const r = await processReport({ raw_text: 'Huge pothole on Troost near 39th, almost wrecked my car', lat: 39.0576, lng: -94.5716 })
    assert.equal(r.merged, true)
    assert.equal(r.issue.issue_id, 1042)
    assert.equal(r.issue.report_count, 4)
    assert.equal(r.issue.priority_tier, 'P1')
    assert.equal(r.issue.recommended_department, 'pw_streets')
    const agents = new Set(r.issue.agent_trace.map((e) => e.agent))
    for (const a of ['intake', 'dedup', 'priority', 'router']) assert.ok(agents.has(a), `trace has ${a}`)
  })

  test('report on an approved issue re-scores it but skips the router edge', async () => {
    store.updateIssue(1042, { status: 'approved', recommended_crew: 'streets_c' })
    const r = await processReport({ raw_text: 'Still a big pothole at Troost and 39th', lat: 39.0576, lng: -94.5716 })
    assert.equal(r.issue.issue_id, 1042)
    assert.equal(r.issue.status, 'approved')
    assert.equal(r.issue.recommended_crew, 'streets_c')
    const run = r.issue.agent_trace.filter((e) => e.run_id === r.run_id).map((e) => e.agent)
    assert.ok(run.includes('priority'))
    assert.ok(!run.includes('router'))
    store.updateIssue(1042, { status: 'triaged' })
  })

  test('demo batch collapses 50 reports into the true issues', async () => {
    const m = await processBatch(demoReports)
    assert.equal(m.reports, 50)
    assert.equal(m.issues, m.ground_truth.true_issues)
    assert.ok(m.ground_truth.dedup_precision >= 0.95)
    assert.ok(m.ground_truth.dedup_recall >= 0.95)
    assert.ok(m.ground_truth.category_accuracy >= 0.95)
  })

  test('two potholes 85 m apart stay separate issues', () => {
    const ids = new Set(
      store
        .listReports()
        .filter((r) => r.truth?.cluster?.startsWith('gillham_armour_pothole'))
        .map((r) => `${r.truth.cluster}:${r.issue_id}`),
    )
    assert.equal(ids.size, 2)
  })
})
