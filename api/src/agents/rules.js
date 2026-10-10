// Deterministic logic. Two uses:
//  1. The "mock" engine: a full rule-based stand-in for each agent (no AWS needed).
//  2. The parts code is good at in Bedrock mode: candidate filtering and the base priority
//     score, which the LLM agents then judge or adjust.
import { categories, departmentForCategory, findCategory, findDepartment, findSubcategory, hazardPhrases } from '../lib/data.js'
import { config } from '../config.js'

// ---------------- Intake ----------------

export function classifyText(text, onlyCategory) {
  const t = ` ${(text || '').toLowerCase()} `
  const scored = []
  for (const c of categories.filter((x) => !onlyCategory || x.id === onlyCategory)) {
    for (const s of c.subcategories) {
      const hits = s.keywords.filter((k) => t.includes(k))
      if (hits.length) {
        const score = hits.reduce((sum, k) => sum + 1 + k.split(' ').length * 0.5, 0)
        scored.push({ category: c.id, subcategory: s.id, score, hits })
      }
    }
  }
  scored.sort((a, b) => b.score - a.score)
  const best = scored[0]
  if (!best) return { category: 'other', subcategory: 'unclear', confidence: 0.3, matched: [] }
  const runnerUp = scored.find((s) => s.category !== best.category)
  const margin = runnerUp ? best.score - runnerUp.score : best.score
  const confidence = Math.min(0.97, 0.6 + 0.08 * best.score + (margin > 1 ? 0.1 : 0))
  return { category: best.category, subcategory: best.subcategory, confidence: +confidence.toFixed(2), matched: best.hits }
}

/**
 * Combine the text classifier with the category the resident picked (if any).
 * The pick wins unless the text clearly describes something in another category.
 */
export function classifyWithHint(text, hint) {
  const general = classifyText(text)
  if (!hint || !findCategory(hint) || hint === 'other') return { ...general, hint_used: false }
  const within = classifyText(text, hint)
  if (within.category === hint) return { ...within, confidence: Math.max(within.confidence, 0.85), hint_used: true }
  if (general.category === 'other') {
    const sub = findCategory(hint).subcategories[0]
    return { category: hint, subcategory: sub.id, confidence: 0.55, matched: [], hint_used: true }
  }
  return { ...general, hint_used: false, hint_overridden: true }
}

export function detectHazards(text, subcategoryId, categoryId) {
  const t = (text || '').toLowerCase()
  const flags = new Set()
  const phrases = []
  for (const h of hazardPhrases) {
    if (t.includes(h.phrase)) {
      flags.add(h.flag)
      phrases.push(h.phrase)
    }
  }
  if (findSubcategory(categoryId, subcategoryId)?.hazard) flags.add('inherent_safety_hazard')
  // Report "almost wrecked", not also "wrecked".
  const unique = [...new Set(phrases)].filter((p, _i, all) => !all.some((q) => q !== p && q.includes(p)))
  return { flags: [...flags], phrases: unique }
}

export function cleanDescription(text) {
  const s = (text || '').replace(/\s+/g, ' ').replace(/!{2,}/g, '!').trim()
  return s ? s[0].toUpperCase() + s.slice(1) : s
}

export function subcategoryName(categoryId, subId) {
  return findSubcategory(categoryId, subId)?.name || 'Unclear report'
}

// ---------------- Dedup ----------------

// Point problems (a pothole) need a tight radius; spread-out ones (a main break flooding a block) a wider one.
const RADIUS_BY_SUBCATEGORY = {
  pothole: 40,
  sidewalk: 30,
  curb: 30,
  streetlight_out: 60,
  traffic_signal: 80,
  main_break: 150,
  flooding: 150,
  leak: 80,
  sewer_backup: 80,
  open_manhole: 50,
  fallen_tree: 80,
  dead_animal: 80,
  illegal_dumping: 70,
  missed_pickup: 120,
  graffiti: 60,
}

export function dedupRadius(subcategoryId) {
  return RADIUS_BY_SUBCATEGORY[subcategoryId] ?? config.dedup.radiusM
}

/** Score each candidate 0-1 for "same physical problem". */
export function scoreCandidates(report, candidates) {
  const radius = dedupRadius(report.subcategory)
  return candidates
    .map((c) => {
      const sameSub = c.subcategory === report.subcategory
      const proximity = Math.max(0, 1 - c.distance_m / radius)
      const confidence = (sameSub ? 0.55 : 0.2) + 0.3 * proximity + 0.15 * (c.text_similarity ?? 0)
      return { ...c, confidence: +Math.min(0.99, confidence).toFixed(2), same_subcategory: sameSub }
    })
    .sort((a, b) => b.confidence - a.confidence)
}

export function decideDuplicate(report, candidates) {
  const scored = scoreCandidates(report, candidates)
  const best = scored[0]
  if (!best) {
    return { duplicate_of: null, possible_duplicate_of: null, confidence: 0.9, reason: 'No open issue of this category nearby in the dedup window.' }
  }
  const why = `${best.distance_m} m away, ${best.same_subcategory ? 'same' : 'different'} subcategory, text similarity ${best.text_similarity ?? 0}`
  if (best.confidence >= config.dedup.mergeConfidence) {
    return {
      duplicate_of: best.issue_id,
      possible_duplicate_of: null,
      confidence: best.confidence,
      reason: `Matches issue #${best.issue_id} (${best.report_count} prior report${best.report_count === 1 ? '' : 's'}, ${why}).`,
    }
  }
  if (best.confidence >= 0.4) {
    return {
      duplicate_of: null,
      possible_duplicate_of: best.issue_id,
      confidence: best.confidence,
      reason: `Possible duplicate of #${best.issue_id} (${why}), below the merge threshold. Flagged for review.`,
    }
  }
  return { duplicate_of: null, possible_duplicate_of: null, confidence: +(1 - best.confidence).toFixed(2), reason: `Nearest candidate #${best.issue_id} looks like a different problem (${why}).` }
}

// ---------------- Priority ----------------

const SAFETY_FLAGS = new Set(['inherent_safety_hazard', 'vehicle_damage_risk', 'collision_risk', 'injury_risk', 'electrical_hazard', 'road_blocked'])

/** Section 5 rubric. ctx = { road, sites, days_open } from the priority tools. */
export function baseScore(issue, ctx) {
  const factors = []
  const add = (factor, points, detail) => factors.push({ factor, points, detail })

  const safety = issue.hazard_flags.filter((f) => SAFETY_FLAGS.has(f))
  if (safety.length) add('safety_hazard', 40, `Safety hazard: ${safety.join(', ').replaceAll('_', ' ')}`)

  const roadPts = { arterial: 15, collector: 8, residential: 0 }[ctx.road.road_type] ?? 0
  add('road_type', roadPts, ctx.road.road_type === 'unknown' ? 'Road class unknown (no local street data)' : `${ctx.road.road_type} road${ctx.road.street ? ` (${ctx.road.street})` : ''}`)

  const extra = Math.max(0, issue.report_count - 1)
  if (extra) add('report_count', Math.min(15, extra * 3), `${issue.report_count} reports`)

  if (ctx.sites.length) add('sensitive_site', 10, `Within 200 m of ${ctx.sites[0].name} (${ctx.sites[0].type.replace('_', ' ')})`)

  const days = Math.floor(ctx.days_open)
  if (days > 0) add('days_open', Math.min(10, days * 2), `${days} day${days === 1 ? '' : 's'} open`)

  // An immediate danger to life is P1 even on its first report; the additive rubric alone
  // tops out around 70 for a single report (safety 40 + arterial 15 + agent 15).
  const subtotal = factors.reduce((s, f) => s + f.points, 0)
  if (isCriticalHazard(issue) && subtotal < CRITICAL_FLOOR) {
    add('critical_hazard', CRITICAL_FLOOR - subtotal, `Critical hazard (${issue.subcategory.replaceAll('_', ' ')}): raised to the P1 floor`)
  }

  const score = factors.reduce((s, f) => s + f.points, 0)
  return { base_score: Math.min(100, score), factors }
}

const CRITICAL_FLOOR = 80
const CRITICAL_SUBCATEGORIES = new Set(['traffic_signal', 'open_manhole', 'main_break'])

/** Signal out, open manhole, main break, or a fallen tree blocking the road. */
export function isCriticalHazard(issue) {
  if (CRITICAL_SUBCATEGORIES.has(issue.subcategory)) return true
  return issue.subcategory === 'fallen_tree' && issue.hazard_flags.includes('road_blocked')
}

/** Rule-based stand-in for the LLM's ±15 judgment adjustment. */
export function mockAdjustment(issue, ctx) {
  const flags = new Set(issue.hazard_flags)
  if (flags.has('children_present') && ctx.sites.some((s) => s.type === 'school')) {
    return { adjustment: 5, reason: 'Children reported nearby and a school is within 200 m.' }
  }
  if (['main_break', 'open_manhole', 'traffic_signal'].includes(issue.subcategory) && issue.report_count >= 3) {
    return { adjustment: 8, reason: 'Active hazard confirmed independently by several residents.' }
  }
  if (flags.size >= 3) return { adjustment: 5, reason: 'Multiple distinct hazards described.' }
  if (['graffiti', 'overgrown_lot', 'missed_pickup'].includes(issue.subcategory) && !issue.hazard_flags.length) {
    return { adjustment: -5, reason: 'Quality-of-life issue with no safety risk described.' }
  }
  return { adjustment: 0, reason: 'Rubric score reflects the situation; no adjustment.' }
}

export function tierFor(score) {
  if (score >= 80) return 'P1'
  if (score >= 60) return 'P2'
  if (score >= 40) return 'P3'
  return 'P4'
}

export const SLA_HOURS = { P1: 24, P2: 72, P3: 168, P4: 336 }

// ---------------- Router ----------------

export function pickCrew(issue, crews) {
  const dept = departmentForCategory(issue.category)
  const options = crews
    .filter((c) => c.department_id === dept.department_id)
    .map((c) => {
      const utilization = c.open_jobs / c.capacity
      const cost = c.distance_km / 4 + utilization + (c.open_jobs >= c.capacity ? 10 : 0)
      return { ...c, utilization: +utilization.toFixed(2), cost }
    })
    .sort((a, b) => a.cost - b.cost)
  const crew = options[0]
  const sla = SLA_HOURS[issue.priority_tier] ?? 168
  const alternatives = options.slice(1).map((c) => `${c.name} (${c.open_jobs}/${c.capacity}, ${c.distance_km} km)`)
  const reason = crew
    ? `${crew.name}: ${crew.open_jobs}/${crew.capacity} open jobs, ${crew.distance_km} km away.` +
      (alternatives.length ? ` Alternatives: ${alternatives.join('; ')}.` : '')
    : `${dept.name} handles this category; no crew on file.`
  return {
    department_id: dept.department_id,
    crew_id: crew?.crew_id ?? null,
    suggested_sla_hours: sla,
    reason,
  }
}

export function departmentName(id) {
  return findDepartment(id)?.name ?? id
}
