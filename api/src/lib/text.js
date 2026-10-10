// Lightweight bag-of-words similarity used for semantic dedup in mock mode
// (and as a pre-filter in Bedrock mode). Swap for Titan embeddings when available.

const STOP = new Set(
  'a an and are at by for from has have i in is it its it\'s just near of on or our out pls please so the there theres this to was we with my me someone our right'.split(' '),
)

const SYNONYMS = {
  pot: 'pothole', potholes: 'pothole', crater: 'pothole', hole: 'pothole',
  streetlight: 'light', lights: 'light', lamp: 'light', dark: 'light', black: 'light',
  stoplight: 'signal', signals: 'signal',
  dumped: 'dump', dumping: 'dump', mattress: 'dump', debris: 'dump',
  gushing: 'water', geyser: 'water', pipe: 'water', flooded: 'water', flood: 'water',
  tree: 'tree', limb: 'tree', branch: 'tree', fell: 'tree', fallen: 'tree',
  tagged: 'graffiti', spray: 'graffiti',
  manhole: 'manhole', cover: 'manhole',
  deer: 'animal', roadkill: 'animal', carcass: 'animal',
  trash: 'trash', recycling: 'trash', pickup: 'trash', garbage: 'trash',
}

export function tokens(text) {
  return (text || '')
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 1 && !STOP.has(w))
    .map((w) => SYNONYMS[w] || w)
}

export function similarity(a, b) {
  const va = new Map()
  const vb = new Map()
  for (const t of tokens(a)) va.set(t, (va.get(t) || 0) + 1)
  for (const t of tokens(b)) vb.set(t, (vb.get(t) || 0) + 1)
  let dot = 0
  for (const [k, v] of va) dot += v * (vb.get(k) || 0)
  const norm = (m) => Math.sqrt([...m.values()].reduce((s, v) => s + v * v, 0))
  const d = norm(va) * norm(vb)
  return d === 0 ? 0 : dot / d
}
