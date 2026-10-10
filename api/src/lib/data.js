// Read-only seed data loaded from the shared /data directory.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { config } from '../config.js'

function load(name) {
  return JSON.parse(readFileSync(join(config.dataDir, name), 'utf8'))
}

const categoriesFile = load('categories.json')
const departmentsFile = load('departments.json')

export const categories = categoriesFile.categories
export const hazardPhrases = categoriesFile.hazard_phrases
export const departments = departmentsFile.departments
export const crewSeed = departmentsFile.crews
// City data is optional apart from a center point. Without local streets, neighborhoods or
// sites the app still works anywhere: geocoding falls back to OpenStreetMap (Photon).
const rawCity = load('city.json')
export const city = {
  ...rawCity,
  center: rawCity.center || { lat: 0, lng: 0 },
  streets: rawCity.streets || [],
  neighborhoods: rawCity.neighborhoods || [],
  sensitive_sites: rawCity.sensitive_sites || [],
}
const profile = rawCity.profile || {}
export const cityProfile = {
  name: profile.name || '',
  region: profile.region || '',
  country_code: profile.country_code || '',
  address_suffix: profile.address_suffix ?? (profile.name ? `, ${[profile.name, profile.region].filter(Boolean).join(', ')}` : ''),
  default_zoom: profile.default_zoom || 12,
  address_grid: profile.address_grid || null,
  examples: profile.examples || {},
}
/** "Kansas City, MO", or a generic label when no city is configured. */
export const cityLabel = [cityProfile.name, cityProfile.region].filter(Boolean).join(', ') || 'your city'
export const seedReports = load('seed_reports.json').reports
export const demoReports = load('demo_reports.json').reports

export function findCategory(id) {
  return categories.find((c) => c.id === id)
}

export function findSubcategory(categoryId, subId) {
  return findCategory(categoryId)?.subcategories.find((s) => s.id === subId)
}

export function departmentForCategory(categoryId) {
  return departments.find((d) => d.categories_handled.includes(categoryId)) || departments.find((d) => d.department_id === 'human_review')
}

export function findDepartment(id) {
  return departments.find((d) => d.department_id === id)
}
