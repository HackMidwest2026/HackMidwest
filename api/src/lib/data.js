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
export const city = load('city.json')
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
