// Dispatcher accounts over HTTP: sign up, log in, protected routes, log out.
import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, describe, test } from 'node:test'

process.env.STATE_DIR = mkdtempSync(join(tmpdir(), 'citycare-auth-'))
process.env.CITYCARE_MODE = 'mock'
process.env.MOCK_DELAY_MS = '0'
process.env.PHOTON_URL = 'off'
process.env.SEED_SOURCE = 'sample'
delete process.env.DATABASE_URL
delete process.env.DISPATCHER_SIGNUP_CODE

const { app } = await import('../src/server.js')
const store = await import('../src/lib/store.js')
const { hashPassword, verifyPassword, readToken, resetLoginAttempts } = await import('../src/lib/auth.js')
const { seedReports } = await import('../src/lib/data.js')
const { seedHistory } = await import('../src/pipeline.js')

let server
let base
before(async () => {
  await store.initStore()
  await store.resetState()
  await seedHistory(seedReports)
  server = app.listen(0)
  await new Promise((r) => server.once('listening', r))
  base = `http://127.0.0.1:${server.address().port}`
})
after(() => server.close())

/** fetch with a tiny cookie jar */
function client() {
  let cookie = ''
  return async (method, path, body) => {
    const res = await fetch(base + path, {
      method,
      headers: { ...(body && { 'Content-Type': 'application/json' }), ...(cookie && { Cookie: cookie }) },
      body: body && JSON.stringify(body),
    })
    const set = res.headers.get('set-cookie')
    if (set) cookie = set.split(';')[0].endsWith('=') ? '' : set.split(';')[0]
    return { status: res.status, body: await res.json().catch(() => null), setCookie: set }
  }
}

describe('dispatcher accounts', () => {
  test('passwords are hashed with a salt and verified', async () => {
    const a = await hashPassword('correct horse battery')
    const b = await hashPassword('correct horse battery')
    assert.notEqual(a, b)
    assert.ok(!a.includes('correct'))
    assert.equal(await verifyPassword('correct horse battery', a), true)
    assert.equal(await verifyPassword('wrong password', a), false)
    assert.equal(await verifyPassword('anything', 'garbage'), false)
  })

  test('sign up, use dispatcher routes, log out, log back in', async () => {
    const call = client()
    const issueId = store.listIssues()[0].issue_id

    // Signed out: dispatcher actions are refused, public views still work.
    assert.equal((await call('GET', '/api/auth/me')).body.user, null)
    const denied = await call('POST', `/api/issues/${issueId}/reject`, { reason: 'x' })
    assert.equal(denied.status, 401)
    assert.equal(denied.body.auth_required, true)
    for (const [m, p] of [['GET', '/api/reports'], ['POST', '/api/chat'], ['POST', '/api/reset'], ['GET', '/api/routes'], ['PATCH', `/api/issues/${issueId}`]]) {
      assert.equal((await call(m, p, m === 'GET' ? undefined : {})).status, 401, `${m} ${p} should need a login`)
    }
    assert.equal((await call('GET', '/api/issues')).status, 200)
    assert.equal((await call('GET', '/api/meta')).status, 200)

    // Bad sign-ups.
    assert.equal((await call('POST', '/api/auth/signup', { name: 'A', email: 'not-an-email', password: 'longenough' })).status, 400)
    assert.equal((await call('POST', '/api/auth/signup', { name: 'A', email: 'a@city.gov', password: 'short' })).status, 400)

    const up = await call('POST', '/api/auth/signup', { name: 'Jordan Rivera', email: 'Jordan@City.gov', password: 'dispatch-2026' })
    assert.equal(up.status, 201)
    assert.deepEqual({ ...up.body.user, user_id: undefined }, { user_id: undefined, name: 'Jordan Rivera', email: 'jordan@city.gov', role: 'dispatcher' })
    assert.match(up.setCookie, /cc_session=[^;]+; Path=\/; HttpOnly; SameSite=Lax/)
    assert.equal(up.body.user.password_hash, undefined)

    // Signed in: actions work and record who did them.
    assert.equal((await call('GET', '/api/auth/me')).body.user.name, 'Jordan Rivera')
    const ok = await call('POST', `/api/issues/${issueId}/reject`, { reason: 'Not actionable' })
    assert.equal(ok.status, 200)
    assert.equal(ok.body.status_history.at(-1).by, 'Jordan Rivera')
    assert.equal((await call('GET', '/api/reports')).status, 200)

    // Same email again is refused.
    assert.equal((await call('POST', '/api/auth/signup', { name: 'Other', email: 'jordan@city.gov', password: 'another-pass' })).status, 409)

    // Log out clears the session.
    const out = await call('POST', '/api/auth/logout', {})
    assert.match(out.setCookie, /Max-Age=0/)
    assert.equal((await call('GET', '/api/auth/me')).body.user, null)

    // Wrong password and unknown email get the same answer.
    const wrong = await call('POST', '/api/auth/login', { email: 'jordan@city.gov', password: 'nope-nope' })
    const unknown = await call('POST', '/api/auth/login', { email: 'nobody@city.gov', password: 'nope-nope' })
    assert.equal(wrong.status, 401)
    assert.deepEqual(wrong.body, unknown.body)

    const back = await call('POST', '/api/auth/login', { email: 'JORDAN@city.gov', password: 'dispatch-2026' })
    assert.equal(back.status, 200)
    assert.equal((await call('GET', '/api/auth/me')).body.user.email, 'jordan@city.gov')
  })

  test('repeated attempts from one address are slowed down', async () => {
    resetLoginAttempts()
    const call = client()
    const codes = []
    for (let i = 0; i < 12; i++) codes.push((await call('POST', '/api/auth/login', { email: 'x@city.gov', password: 'wrong-pass' })).status)
    assert.deepEqual(codes.slice(0, 10), Array(10).fill(401))
    assert.deepEqual(codes.slice(10), [429, 429])
    resetLoginAttempts()
  })

  test('a tampered or forged session cookie is rejected', async () => {
    const call = client()
    await call('POST', '/api/auth/signup', { name: 'Sam Lee', email: 'sam@city.gov', password: 'dispatch-2026' })
    const good = (await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: 'sam@city.gov', password: 'dispatch-2026' }) })).headers
      .get('set-cookie')
      .split(';')[0]
      .split('=')[1]
    assert.ok(await readToken(good))
    const [payload, sig] = good.split('.')
    const forged = Buffer.from(JSON.stringify({ uid: 'x', name: 'Mallory', email: 'm@x', exp: Date.now() + 1e9 })).toString('base64url')
    for (const token of [`${forged}.${sig}`, `${payload}.AAAA`, 'garbage', '']) {
      const res = await fetch(base + '/api/reports', { headers: { Cookie: `cc_session=${token}` } })
      assert.equal(res.status, 401, `token ${token.slice(0, 12)} should be rejected`)
    }
  })

  test('public issue details hide residents’ contact info', async () => {
    const issue = store.listIssues()[0]
    const report = store.reportsForIssue(issue.issue_id)[0]
    store.updateReport(report.report_id, { reporter_contact: 'resident@example.com' })
    const pub = await (await fetch(`${base}/api/issues/${issue.issue_id}`)).json()
    assert.ok(pub.reports.every((r) => !('reporter_contact' in r)))
  })

  test('DISPATCHER_SIGNUP_CODE gates sign-up', async () => {
    process.env.DISPATCHER_SIGNUP_CODE = 'kc-ops-2026'
    resetLoginAttempts()
    try {
      const call = client()
      assert.equal((await call('GET', '/api/auth/config')).body.signup_code_required, true)
      const body = { name: 'Pat Kim', email: 'pat@city.gov', password: 'dispatch-2026' }
      assert.equal((await call('POST', '/api/auth/signup', body)).status, 403)
      assert.equal((await call('POST', '/api/auth/signup', { ...body, code: 'wrong' })).status, 403)
      assert.equal((await call('POST', '/api/auth/signup', { ...body, code: 'kc-ops-2026' })).status, 201)
    } finally {
      delete process.env.DISPATCHER_SIGNUP_CODE
    }
  })

  test('accounts survive a data reset', async () => {
    await store.resetState()
    assert.ok(await store.findUser({ email: 'jordan@city.gov' }))
  })
})
