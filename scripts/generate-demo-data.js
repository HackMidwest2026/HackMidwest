#!/usr/bin/env node
// Generates data/seed_reports.json (prior history) and data/demo_reports.json (the 50-report
// "wow moment" batch) from hand-written clusters pinned to KC intersections.
// Output is deterministic (seeded RNG), so ground truth stays stable between runs.
//
//   node scripts/generate-demo-data.js

import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const city = JSON.parse(readFileSync(join(root, 'data/city.json'), 'utf8'))

function mulberry32(seed) {
  return () => {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rand = mulberry32(311)

function street(name) {
  const s = city.streets.find((x) => x.name === name)
  if (!s) throw new Error(`unknown street ${name}`)
  return s
}

// Place a point at an intersection, shifted by (eastM, northM) meters plus up to ±jitterM of noise.
function at(ns, ew, { eastM = 0, northM = 0, jitterM = 12 } = {}) {
  const a = street(ns)
  const b = street(ew)
  const lat0 = b.lat
  const lng0 = a.lng
  const mPerDegLat = 111320
  const mPerDegLng = 111320 * Math.cos((lat0 * Math.PI) / 180)
  const jx = (rand() * 2 - 1) * jitterM
  const jy = (rand() * 2 - 1) * jitterM
  return {
    lat: +(lat0 + (northM + jy) / mPerDegLat).toFixed(6),
    lng: +(lng0 + (eastM + jx) / mPerDegLng).toFixed(6),
    address: `${a.name} & ${b.name}, Kansas City, MO`,
  }
}

// ---- Prior history: these become the existing open issues on reset. ----
// Order matters: the Troost & 39th pothole is third so it becomes issue #1042, as in the demo script.
const seedClusters = [
  {
    key: 'seed_main_39th_light', where: ['Main St', '39th St'], category: 'traffic_lighting', subcategory: 'streetlight_out',
    texts: [
      ['Streetlight out at Main and 39th', 3],
      ['light pole on main by 39th is dark', 2],
    ],
  },
  {
    key: 'seed_prospect_31st_dumping', where: ['Prospect Ave', '31st St'], category: 'trash', subcategory: 'illegal_dumping',
    texts: [
      ['Someone dumped a bunch of tires behind the store at Prospect & 31st', 4],
      ['tires dumped prospect and 31st again', 1],
    ],
  },
  {
    key: 'seed_troost_39th_pothole', where: ['Troost Ave', '39th St'], category: 'streets', subcategory: 'pothole',
    texts: [
      ['Pothole on Troost just north of 39th, northbound lane', 6],
      ['big pothole troost & 39th', 5],
      ['There is a deep hole in the road on Troost by 39th st, cars swerving around it', 4],
    ],
  },
  { key: 'seed_woodland_18th_lot', where: ['Woodland Ave', '18th St'], category: 'property', subcategory: 'overgrown_lot',
    texts: [['Vacant lot on Woodland near 18th is overgrown, weeds taller than me', 8]] },
  { key: 'seed_benton_12th_stray', where: ['Benton Blvd', '12th St'], category: 'animals', subcategory: 'stray',
    texts: [['Two loose dogs running around Benton & 12th, one looks aggressive', 1]] },
  { key: 'seed_broadway_47th_sidewalk', where: ['Broadway Blvd', '47th St'], category: 'streets', subcategory: 'sidewalk',
    texts: [['Sidewalk slab heaved up on Broadway at 47th, I tripped on it', 9]] },
  {
    key: 'seed_paseo_63rd_sewer', where: ['Paseo Blvd', '63rd St'], category: 'water', subcategory: 'sewer_backup',
    texts: [
      ['Storm drain clogged at Paseo & 63rd, water pooling', 3],
      ['smells like sewage at the paseo and 63rd', 2],
    ],
  },
  { key: 'seed_troost_75th_car', where: ['Troost Ave', '75th St'], category: 'property', subcategory: 'abandoned_vehicle',
    texts: [['Abandoned car with no plates parked on Troost near 75th for 3 weeks', 7]] },
]

// ---- Demo batch: 50 messy reports in 12 real problems. ----
const demoClusters = [
  {
    key: 'main_31st_pothole', where: ['Main St', '31st St'], category: 'streets', subcategory: 'pothole',
    texts: [
      'Massive pothole on Main at 31st, popped my tire this morning',
      'main & 31st pot hole is HUGE',
      'theres a crater in the southbound lane of main st near 31st',
      'Hole in the road at 31st and Main, someone is going to get hurt',
      'pothole main/31st pls fix',
      'Just blew a tire on a pothole at Main and 31st. Third one this month.',
    ],
  },
  {
    key: 'troost_linwood_light', where: ['Troost Ave', 'Linwood Blvd'], category: 'traffic_lighting', subcategory: 'streetlight_out',
    texts: [
      'Streetlight out on Troost at Linwood',
      'its pitch black at troost and linwood, light is out',
      'dark corner troost/linwood, light broken, feels unsafe walking',
      'street light not working near Linwood Blvd & Troost bus stop',
      'light out',
    ],
  },
  {
    key: 'prospect_47th_signal', where: ['Prospect Ave', '47th St'], category: 'traffic_lighting', subcategory: 'traffic_signal',
    texts: [
      'Traffic signal at Prospect and 47th is completely out, cars almost hit each other',
      'stoplight dead at 47th & prospect!!',
      'signal stuck blinking red at prospect/47th, near miss just now',
      'The traffic lights at 47th St and Prospect Ave are not working',
    ],
  },
  {
    key: 'paseo_18th_dumping', where: ['Paseo Blvd', '18th St'], category: 'trash', subcategory: 'illegal_dumping',
    texts: [
      'Someone dumped a mattress and a couch in the alley off Paseo by 18th',
      'illegal dumping paseo & 18th, big pile of trash',
      'construction debris dumped near 18th and the paseo',
      'mattress + tires dumped behind the lot at Paseo/18th',
      'pile of trash someone left on paseo near 18th st',
    ],
  },
  {
    key: 'broadway_westport_main_break', where: ['Broadway Blvd', 'Westport Rd'], category: 'water', subcategory: 'main_break',
    texts: [
      'Water main break at Broadway and Westport Rd, water gushing into the street',
      'geyser of water shooting up at westport & broadway',
      'busted pipe? water everywhere at Broadway/Westport road',
      'water main break westport rd and broadway, lane is flooded',
      'HUGE water main break in Westport by Broadway, its like a river',
      'water gushing out of the street near Broadway & Westport Rd',
    ],
  },
  {
    key: 'wornall_63rd_tree', where: ['Wornall Rd', '63rd St'], category: 'parks_trees', subcategory: 'fallen_tree',
    texts: [
      'Big tree limb down across the road at Wornall and 63rd',
      'tree fell on wornall near 63rd, blocking a lane',
      'branch across wornall rd by 63rd st in Brookside',
      'Fallen tree blocking traffic Wornall & 63rd',
    ],
  },
  {
    key: 'grand_truman_graffiti', where: ['Grand Blvd', 'Truman Rd'], category: 'property', subcategory: 'graffiti',
    texts: [
      'Graffiti all over the underpass wall at Grand and Truman',
      'someone tagged the building at truman & grand',
      'spray paint graffiti on the wall near Grand Blvd/Truman Rd',
    ],
  },
  {
    key: 'gillham_armour_pothole_a', where: ['Gillham Rd', 'Armour Blvd'], category: 'streets', subcategory: 'pothole',
    texts: [
      'Pothole at Gillham and Armour, right in the crosswalk',
      'gillham & armour big pothole by the light',
      'pot hole at armour/gillham intersection',
      'Bent my rim on a pothole at Gillham Rd & Armour',
    ],
  },
  {
    // A *different* pothole about 85 m east of the one above. Should NOT be merged with it.
    key: 'gillham_armour_pothole_b', where: ['Gillham Rd', 'Armour Blvd'], offset: { eastM: 85 }, category: 'streets', subcategory: 'pothole',
    texts: [
      'Second pothole on Armour east of Gillham, in front of the apartments',
      'pothole on armour blvd halfway between gillham and oak',
      'another hole in the road on Armour just past Gillham heading east',
    ],
  },
  {
    key: 'independence_benton_manhole', where: ['Benton Blvd', 'Independence Ave'], category: 'water', subcategory: 'open_manhole',
    texts: [
      'Open manhole with no cover on Independence Ave at Benton!! dangerous',
      'manhole cover missing independence & benton',
      'missing cover on a man hole at Benton/Independence, kids walk by here',
      'Open manhole near Independence and Benton, someone put a cone in it',
    ],
  },
  {
    key: 'wornall_75th_deer', where: ['Wornall Rd', '75th St'], category: 'animals', subcategory: 'dead_animal',
    texts: [
      'Dead deer on Wornall at 75th',
      'roadkill (deer) wornall & 75th in waldo',
      'dead animal in the road near 75th and Wornall',
    ],
  },
  {
    key: 'holmes_55th_pickup', where: ['Holmes St', '55th St'], category: 'trash', subcategory: 'missed_pickup',
    texts: [
      'Trash was not picked up on Holmes near 55th this week',
      'missed pickup on our block, holmes & 55th',
      "they didn't pick up recycling or trash at Holmes/55th",
    ],
  },
]

const seedReports = []
for (const c of seedClusters) {
  for (const [text, daysAgo] of c.texts) {
    const loc = at(c.where[0], c.where[1], c.offset)
    seedReports.push({
      raw_text: text,
      ...loc,
      days_ago: daysAgo,
      truth: { cluster: c.key, category: c.category, subcategory: c.subcategory },
    })
  }
}

let demoReports = []
for (const c of demoClusters) {
  for (const text of c.texts) {
    const loc = at(c.where[0], c.where[1], c.offset)
    demoReports.push({ raw_text: text, ...loc, truth: { cluster: c.key, category: c.category, subcategory: c.subcategory } })
  }
}
// Shuffle so duplicates arrive interleaved, like real 311 traffic.
for (let i = demoReports.length - 1; i > 0; i--) {
  const j = Math.floor(rand() * (i + 1))
  ;[demoReports[i], demoReports[j]] = [demoReports[j], demoReports[i]]
}
demoReports = demoReports.map((r, i) => ({ demo_id: `demo-${String(i + 1).padStart(3, '0')}`, ...r }))

const note = 'SYNTHETIC reports for the CityCare demo. Generated by scripts/generate-demo-data.js; do not edit by hand.'
writeFileSync(join(root, 'data/seed_reports.json'), JSON.stringify({ _note: note, reports: seedReports }, null, 2) + '\n')
writeFileSync(
  join(root, 'data/demo_reports.json'),
  JSON.stringify({ _note: note, clusters: demoClusters.length, reports: demoReports }, null, 2) + '\n',
)
console.log(`wrote ${seedReports.length} seed reports and ${demoReports.length} demo reports (${demoClusters.length} true issues)`)
