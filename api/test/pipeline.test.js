import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { before, describe, test } from 'node:test'

// Isolated state, rule-based engine, no artificial delay. Must be set before importing the app.
process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'citycare-test-'))
process.env.CITYCARE_MODE = 'mock'
process.env.MOCK_DELAY_MS = '0'
process.env.MOCK_BATCH_DELAY_MS = '0'
process.env.PHOTON_URL = 'off' // no network in tests

const { classifyText, classifyWithHint, detectHazards, baseScore, tierFor } = await import('../src/agents/rules.js')
const { geocodeAddress, roadType, suggestAddresses } = await import('../src/lib/geo.js')
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

  test('category hint from the resident picker', () => {
    // Vague text: the pick decides.
    assert.equal(classifyWithHint('this is really bad, please fix', 'water').category, 'water')
    // Text matches inside the picked category: keep the specific subcategory.
    assert.equal(classifyWithHint('water gushing everywhere', 'water').subcategory, 'main_break')
    // Text clearly describes something else: the text wins.
    assert.equal(classifyWithHint('massive pothole on main', 'trash').category, 'streets')
    // No hint: plain classification.
    assert.equal(classifyWithHint('streetlight out').subcategory, 'streetlight_out')
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
})

describe('geo', () => {
  test('geocodes an intersection from free text', () => {
    const g = geocodeAddress('Huge pothole on Troost near 39th')
    assert.equal(g.found, true)
    assert.match(g.address, /Troost Ave & 39th St/)
  })

  test('address suggestions from partial input', () => {
    for (const q of ['troost & 39', '39th and tro', 'troost 39']) {
      assert.equal(suggestAddresses(q)[0]?.label, 'Troost Ave & 39th St', q)
    }
    const westport = suggestAddresses('westport').map((s) => s.label)
    assert.ok(westport.includes('Westport'), 'neighborhood offered')
    assert.equal(suggestAddresses("children's")[0].kind, 'place')
    assert.deepEqual(suggestAddresses('x'), [])
    // House numbers on the KC grid: 3900 Troost sits at 39th St.
    const est = suggestAddresses('3900 troost')[0]
    assert.equal(est.label, '3900 Troost Ave')
    assert.ok(Math.abs(est.lat - 39.0574) < 0.0005)
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

  test('demo batch collapses 50 reports into the true issues', async () => {
    const m = await processBatch(demoReports)
    assert.equal(m.reports, 50)
    assert.equal(m.issues, m.ground_truth.true_issues)
    assert.ok(m.ground_truth.dedup_precision >= 0.95)
    assert.ok(m.ground_truth.dedup_recall >= 0.95)
    assert.ok(m.ground_truth.category_accuracy >= 0.95)
  })

  test('reports outside the sample city still flow through the pipeline', async () => {
    // Chicago: no local street data, OpenStreetMap disabled in tests.
    const r = await processReport({ raw_text: 'Streetlight out on my block, totally dark', lat: 41.8781, lng: -87.6298 })
    assert.equal(r.merged, false)
    assert.equal(r.issue.subcategory, 'streetlight_out')
    assert.doesNotMatch(r.issue.address, /Kansas City/)
    assert.equal(r.issue.neighborhood, 'Unmapped area')
    assert.ok(r.issue.priority_factors.some((f) => /Road class unknown/.test(f.detail)))
    assert.equal(r.issue.recommended_department, 'pw_traffic')
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
