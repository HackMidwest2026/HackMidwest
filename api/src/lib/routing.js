// Route arithmetic for the Route Planner agent: on-site time per job, drive-time estimates
// and stop order. Code does the math; the agent decides which jobs ride together.
// Durations and speeds are simulated, like the crews.
import { distanceM, neighborhoodFor } from './geo.js'
import { getCrew, listCrews, listIssues } from './store.js'

export const SHIFT_MINUTES = 480
const DRIVE_KMH = 30 // average city speed including lights
const DETOUR = 1.3 // street grid vs straight line
const SETUP_MINUTES = 5 // park, unload and cone off at each stop

const WORK_MINUTES = {
  pothole: 45,
  street_damage: 90,
  sidewalk: 60,
  curb: 60,
  streetlight_out: 40,
  traffic_signal: 60,
  sign_damaged: 30,
  missed_pickup: 20,
  illegal_dumping: 60,
  overflowing_bin: 20,
  bulky_item: 30,
  main_break: 180,
  leak: 90,
  flooding: 120,
  sewer_backup: 90,
  open_manhole: 30,
  graffiti: 45,
  overgrown_lot: 90,
  abandoned_vehicle: 30,
  dangerous_building: 60,
  fallen_tree: 120,
  park_damage: 60,
  dead_animal: 20,
  stray: 30,
}

export const workMinutes = (subcategory) => WORK_MINUTES[subcategory] ?? 45
export const driveMinutes = (a, b) => Math.round(((distanceM(a, b) / 1000) * DETOUR * 60) / DRIVE_KMH)

const ROUTABLE = new Set(['triaged', 'approved', 'assigned'])
const TIER_RANK = { P1: 0, P2: 1, P3: 2, P4: 3 }
const home = (crew) => ({ lat: crew.home_lat, lng: crew.home_lng })

/** Open jobs a crew is responsible for: assigned to it, or recommended to it and awaiting approval. */
export function crewJobs(crewId) {
  return listIssues()
    .filter((i) => ROUTABLE.has(i.status) && (i.assigned_crew === crewId || (!i.assigned_crew && i.recommended_crew === crewId)))
    .map((i) => ({
      issue_id: i.issue_id,
      subcategory: i.subcategory,
      priority_tier: i.priority_tier,
      priority_score: i.priority_score,
      address: i.address,
      neighborhood: i.neighborhood || neighborhoodFor(i),
      lat: i.lat,
      lng: i.lng,
      needs_approval: i.status === 'triaged',
      work_min: workMinutes(i.subcategory),
    }))
}

/** Crews that have at least one open job, with their jobs and each job's close neighbours. */
export function crewsWithJobs() {
  return listCrews()
    .map((c) => {
      const jobs = crewJobs(c.crew_id)
      return {
        crew_id: c.crew_id,
        name: c.name,
        department_id: c.department_id,
        home: home(c),
        jobs: jobs.map((j) => ({
          ...j,
          drive_from_yard_min: driveMinutes(home(c), j),
          near_jobs: jobs
            .filter((o) => o.issue_id !== j.issue_id && distanceM(j, o) <= 1500)
            .map((o) => ({ issue_id: o.issue_id, distance_m: Math.round(distanceM(j, o)) })),
        })),
      }
    })
    .filter((c) => c.jobs.length)
}

/**
 * Time a trip for one crew: yard -> stops -> yard. Urgent stops (P1/P2) come first, then
 * nearest-next. Returns errors for issue ids that are not this crew's open jobs.
 */
export function estimateRoute(crewId, issueIds) {
  const crew = getCrew(crewId)
  if (!crew) return { error: `Unknown crew ${crewId}` }
  const mine = new Map(crewJobs(crewId).map((j) => [j.issue_id, j]))
  const unknown = issueIds.filter((id) => !mine.has(id))
  const jobs = [...new Set(issueIds)].filter((id) => mine.has(id)).map((id) => mine.get(id))

  const ordered = []
  let at = home(crew)
  const left = [...jobs]
  while (left.length) {
    const urgent = left.filter((j) => (TIER_RANK[j.priority_tier] ?? 3) <= 1)
    const pool = urgent.length ? urgent : left
    const next = pool.reduce((a, b) => (distanceM(at, b) < distanceM(at, a) ? b : a))
    ordered.push(next)
    left.splice(left.indexOf(next), 1)
    at = next
  }

  let clock = 0
  let driveTotal = 0
  let km = 0
  at = home(crew)
  const stops = ordered.map((j) => {
    const drive = driveMinutes(at, j)
    km += distanceM(at, j) / 1000
    driveTotal += drive
    clock += drive
    const stop = { ...j, drive_min: drive, arrive_min: clock }
    clock += SETUP_MINUTES + j.work_min
    at = j
    return stop
  })
  const back = ordered.length ? driveMinutes(at, home(crew)) : 0
  if (ordered.length) km += distanceM(at, home(crew)) / 1000
  driveTotal += back
  const total = clock + back
  return {
    crew_id: crew.crew_id,
    crew_name: crew.name,
    department_id: crew.department_id,
    home: home(crew),
    stops,
    drive_min: driveTotal,
    work_min: stops.reduce((s, j) => s + SETUP_MINUTES + j.work_min, 0),
    total_min: total,
    distance_km: +km.toFixed(1),
    over_shift: total > SHIFT_MINUTES,
    ...(unknown.length && { errors: unknown.map((id) => `#${id} is not an open job for ${crew.name}`) }),
  }
}

/** "Street Maintenance Crew B: 4 jobs in Midtown, about 2 h total" */
export function tripHeadline(route) {
  const hoods = [...new Set(route.stops.map((s) => s.neighborhood))]
  const where = hoods.length <= 2 ? hoods.join(' & ') : `${hoods[0]} +${hoods.length - 1} areas`
  const hours = Math.max(0.5, Math.round((route.total_min / 60) * 2) / 2)
  const n = route.stops.length
  return `${route.crew_name}: ${n} job${n === 1 ? '' : 's'} in ${where}, about ${hours} h total`
}
