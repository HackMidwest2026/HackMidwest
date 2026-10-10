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

const { classifyText, classifyWithHint, detectHazards, baseScore, tierFor } = await import('../src/agents/rules.js')
const { geocodeAddress, roadType } = await import('../src/lib/geo.js')
const { demoReports, seedReports } = await import('../src/lib/data.js')
const store = await import('../src/lib/store.js')
const { analyzePhotoWithVision } = await import('../src/agents/photo.js')
const { createLimiter } = await import('../src/lib/limiter.js')
const { planRoutes } = await import('../src/agents/routes.js')
const { crewJobs, estimateRoute, SHIFT_MINUTES } = await import('../src/lib/routing.js')
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

describe('limiter', () => {
  const tick = () => new Promise((r) => setImmediate(r))

  test('caps concurrency and hands out slots in arrival order', async () => {
    const lim = createLimiter({ maxConcurrent: 2 })
    const order = []
    const releases = []
    for (const n of [1, 2, 3, 4]) lim.acquire().then((rel) => order.push(n) && releases.push(rel))
    await tick()
    assert.deepEqual(order, [1, 2])
    assert.equal(lim.stats().waiting, 2)
    assert.ok(lim.isBusy())
    releases[0]()
    releases[0]() // a second release of the same slot is ignored
    await tick()
    assert.deepEqual(order, [1, 2, 3])
    releases[1]()
    await tick()
    assert.deepEqual(order, [1, 2, 3, 4])
  })

  test('caps calls per minute even when slots are free', async () => {
    const lim = createLimiter({ maxConcurrent: 10, perMinute: 2 })
    let got = 0
    for (let i = 0; i < 3; i++) lim.acquire().then((rel) => (got++, rel()))
    await tick()
    assert.equal(got, 2)
    assert.equal(lim.stats().waiting, 1)
    assert.equal(lim.stats().last_minute, 2)
  })

  test('pause holds new callers until it ends', async () => {
    const lim = createLimiter({ maxConcurrent: 5 })
    lim.pause(80)
    let got = false
    lim.acquire().then((rel) => ((got = true), rel()))
    await tick()
    assert.equal(got, false)
    assert.ok(lim.isBusy())
    await new Promise((r) => setTimeout(r, 120))
    assert.equal(got, true)
  })
})

describe('photo', () => {
  test('vision agent only reads images the server saved under /uploads', async () => {
    for (const photo_url of ['/etc/passwd', '../.env', '/uploads/notes.txt', 'https://example.com/x.jpg']) {
      const r = await analyzePhotoWithVision({ photo_url })
      assert.equal(r.analyzed, false, photo_url)
    }
  })

  test('a photo-only report still runs through the pipeline', async () => {
    const r = await processReport({ raw_text: '(photo only, no description)', photo_url: '/uploads/missing.jpg', lat: 39.0912, lng: -94.5555 })
    assert.equal(r.report.photo_analysis.analyzed, false)
    assert.ok(r.issue.issue_id)
  })
})

describe('geo', () => {
  test('geocodes an intersection from free text', () => {
    const g = geocodeAddress('Huge pothole on Troost near 39th')
    assert.equal(g.found, true)
    assert.match(g.address, /Troost Ave & 39th St/)
  })

  test('geocodes 18th & Vine and named landmarks', () => {
    assert.match(geocodeAddress('Graffiti all over the wall at 18th and Vine').address, /^Vine St & 18th St/)
    assert.match(geocodeAddress('graffiti at 18th & vine').address, /^Vine St & 18th St/)
    const station = geocodeAddress('Pothole right outside Union Station')
    assert.equal(station.precision, 'landmark')
    assert.match(station.address, /^Union Station/)
    assert.equal(geocodeAddress('Streetlight out by the Plaza').found, true)
  })

  test('"water main" and similar phrases do not pick the wrong street', () => {
    assert.match(geocodeAddress('Water main break gushing at Broadway and Westport Rd').address, /^Broadway Blvd & Westport Rd/)
    assert.match(geocodeAddress('Big oak tree down across Troost at 39th').address, /^Troost Ave & 39th St/)
    assert.match(geocodeAddress('Traffic signal dark at Main and 31st').address, /^Main St & 31st St/)
    assert.equal(geocodeAddress('water main break somewhere').found, false)
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

  test('route plan covers every open crew job exactly once', async () => {
    const plan = await planRoutes()
    const crewIds = [...new Set(store.listCrews().map((c) => c.crew_id))]
    const expected = crewIds.flatMap((id) => crewJobs(id).map((j) => j.issue_id)).sort()
    const planned = [...plan.trips.flatMap((t) => t.stops.map((s) => s.issue_id)), ...plan.deferred.map((d) => d.issue_id)].sort()
    assert.ok(expected.length > 5)
    assert.deepEqual(planned, expected)
    for (const t of plan.trips) {
      assert.ok(t.total_min <= SHIFT_MINUTES || t.stops.length === 1, t.headline)
      assert.match(t.headline, /: \d+ jobs? in .+, about [\d.]+ h total$/)
      const tiers = t.stops.map((s) => s.priority_tier)
      const firstLow = tiers.findIndex((x) => x === 'P3' || x === 'P4')
      if (firstLow >= 0) assert.ok(!tiers.slice(firstLow).some((x) => x === 'P1' || x === 'P2'), 'urgent stops come first')
    }
    assert.ok(plan.totals.drive_saved_min >= 0)
  })

  test("estimate_route refuses jobs that are not the crew's", () => {
    const [job] = crewJobs('streets_b')
    const r = estimateRoute('water_emergency', [job.issue_id])
    assert.equal(r.stops.length, 0)
    assert.equal(r.errors.length, 1)
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
