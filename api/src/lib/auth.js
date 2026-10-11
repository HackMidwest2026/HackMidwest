// Dispatcher accounts: sign up, log in, log out, and a guard for dispatcher-only routes.
//
// Passwords are hashed with scrypt (node:crypto). A login sets an HTTP-only cookie holding a
// signed token ({ user id, name, email, expiry } + HMAC-SHA256), so any API instance sharing
// the database can check it without a lookup. The signing secret is AUTH_SECRET, or one
// generated on first start and stored in the database.
//
// Sign-up (signupMode):
//   - "code":  DISPATCHER_SIGNUP_CODE is set, and new accounts must enter it.
//   - "open":  DISPATCHER_OPEN_SIGNUP=true, and anyone can sign up (demos only).
//   - "first": neither is set and there are no accounts yet: the first person may sign up,
//              so a fresh deployment can be set up.
//   - "closed": neither is set and an account exists: no more sign-ups until a code is set.
import { createHmac, randomBytes, randomUUID, scrypt as scryptCb, timingSafeEqual } from 'node:crypto'
import { promisify } from 'node:util'
import * as store from './store.js'

const scrypt = promisify(scryptCb)
const COOKIE = 'cc_session'
const SESSION_DAYS = 7
const KEY_LEN = 64

export const authSettings = (env = process.env) => ({
  signupCode: (env.DISPATCHER_SIGNUP_CODE || '').trim(),
  openSignup: (env.DISPATCHER_OPEN_SIGNUP || '').trim().toLowerCase() === 'true',
  secret: (env.AUTH_SECRET || '').trim(),
})

// ---------- passwords ----------

export async function hashPassword(password) {
  const salt = randomBytes(16)
  const key = await scrypt(password, salt, KEY_LEN)
  return `scrypt$${salt.toString('base64url')}$${key.toString('base64url')}`
}

export async function verifyPassword(password, stored) {
  const [scheme, salt, hash] = String(stored || '').split('$')
  if (scheme !== 'scrypt' || !salt || !hash) return false
  const expected = Buffer.from(hash, 'base64url')
  const key = await scrypt(password, Buffer.from(salt, 'base64url'), expected.length)
  return timingSafeEqual(key, expected)
}

// ---------- session tokens ----------

let secretPromise = null
const getSecret = () => (secretPromise ||= authSettings().secret ? Promise.resolve(authSettings().secret) : store.authSecret(randomBytes(32).toString('base64url')))

const sign = (payload, secret) => createHmac('sha256', secret).update(payload).digest('base64url')

export async function makeToken(user, { days = SESSION_DAYS } = {}) {
  const payload = Buffer.from(JSON.stringify({ uid: user.user_id, name: user.name, email: user.email, role: user.role, exp: Date.now() + days * 86400000 })).toString('base64url')
  return `${payload}.${sign(payload, await getSecret())}`
}

export async function readToken(token) {
  const [payload, sig] = String(token || '').split('.')
  if (!payload || !sig) return null
  const expected = Buffer.from(sign(payload, await getSecret()))
  const given = Buffer.from(sig)
  if (expected.length !== given.length || !timingSafeEqual(expected, given)) return null
  try {
    const data = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'))
    return data.exp > Date.now() ? data : null
  } catch {
    return null
  }
}

function cookieValue(req) {
  for (const part of (req.headers.cookie || '').split(';')) {
    const [k, ...v] = part.trim().split('=')
    if (k !== COOKIE) continue
    try {
      return decodeURIComponent(v.join('='))
    } catch {
      return null // malformed cookie: treat as signed out
    }
  }
  return null
}

function setSessionCookie(req, res, token, maxAgeS) {
  const secure = req.secure || req.headers['x-forwarded-proto'] === 'https'
  res.setHeader('Set-Cookie', `${COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAgeS}${secure ? '; Secure' : ''}`)
}

/** The signed-in dispatcher for a request, or null. */
export async function currentUser(req) {
  if (req.dispatcher !== undefined) return req.dispatcher
  const data = await readToken(cookieValue(req))
  req.dispatcher = data && { user_id: data.uid, name: data.name, email: data.email, role: data.role || 'dispatcher' }
  return req.dispatcher
}

/** Express middleware: 401 unless a dispatcher is signed in. */
export function requireDispatcher(req, res, next) {
  currentUser(req).then(
    (user) => (user ? next() : res.status(401).json({ error: 'Sign in as a dispatcher to do this.', auth_required: true })),
    next,
  )
}

// ---------- brute-force guard: a few attempts per minute per address ----------

const attempts = new Map()
/** For tests. */
export const resetLoginAttempts = () => attempts.clear()

function tooManyAttempts(req, limit = 10) {
  const key = req.ip || req.socket?.remoteAddress || 'unknown'
  const now = Date.now()
  const recent = (attempts.get(key) || []).filter((t) => now - t < 60000)
  recent.push(now)
  attempts.set(key, recent)
  if (attempts.size > 5000) attempts.clear()
  return recent.length > limit
}

// ---------- routes ----------

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

async function signupMode() {
  const { signupCode, openSignup } = authSettings()
  if (signupCode) return 'code'
  if (openSignup) return 'open'
  return (await store.hasUsers()) ? 'closed' : 'first'
}
const publicUser = (u) => ({ user_id: u.user_id, name: u.name, email: u.email, role: u.role || 'dispatcher' })

export function authRoutes(app, wrap) {
  app.get(
    '/api/auth/config',
    wrap(async (_req, res) => {
      const mode = await signupMode()
      res.json({ signup: mode, signup_code_required: mode === 'code' })
    }),
  )

  app.get(
    '/api/auth/me',
    wrap(async (req, res) => {
      const user = await currentUser(req)
      res.json({ user: user || null })
    }),
  )

  app.post(
    '/api/auth/signup',
    wrap(async (req, res) => {
      if (tooManyAttempts(req)) return res.status(429).json({ error: 'Too many attempts. Wait a minute and try again.' })
      const name = String(req.body?.name || '').trim().slice(0, 80)
      const email = String(req.body?.email || '').trim().toLowerCase().slice(0, 200)
      const password = String(req.body?.password || '')
      const { signupCode } = authSettings()
      const mode = await signupMode()
      if (mode === 'closed') return res.status(403).json({ error: 'Sign-up is closed. Ask whoever runs this CityCare site for a dispatcher sign-up code.', signup: 'closed' })
      if (!name) return res.status(400).json({ error: 'Enter your name.' })
      if (!EMAIL.test(email)) return res.status(400).json({ error: 'Enter a valid email address.' })
      if (password.length < 8) return res.status(400).json({ error: 'Use a password of at least 8 characters.' })
      if (password.length > 200) return res.status(400).json({ error: 'That password is too long.' })
      if (signupCode) {
        const given = Buffer.from(String(req.body?.code || ''))
        const want = Buffer.from(signupCode)
        if (given.length !== want.length || !timingSafeEqual(given, want)) return res.status(403).json({ error: 'That dispatcher sign-up code is not right.' })
      }
      const user = { user_id: randomUUID(), email, name, password_hash: await hashPassword(password), role: 'dispatcher', created_at: new Date().toISOString() }
      if (!(await store.createUser(user))) return res.status(409).json({ error: 'An account with that email already exists. Log in instead.' })
      setSessionCookie(req, res, await makeToken(user), SESSION_DAYS * 86400)
      res.status(201).json({ user: publicUser(user) })
    }),
  )

  app.post(
    '/api/auth/login',
    wrap(async (req, res) => {
      if (tooManyAttempts(req)) return res.status(429).json({ error: 'Too many attempts. Wait a minute and try again.' })
      const email = String(req.body?.email || '').trim().toLowerCase()
      const password = String(req.body?.password || '')
      const user = email && (await store.findUser({ email }))
      // Same answer for an unknown email and a wrong password.
      if (!user || !(await verifyPassword(password, user.password_hash))) return res.status(401).json({ error: 'Email or password is incorrect.' })
      setSessionCookie(req, res, await makeToken(user), SESSION_DAYS * 86400)
      res.json({ user: publicUser(user) })
    }),
  )

  app.post('/api/auth/logout', (req, res) => {
    setSessionCookie(req, res, '', 0)
    res.json({ ok: true })
  })
}
