# CityCare: Autonomous City Issue Manager

Residents report potholes, broken streetlights, trash and similar problems. A pipeline of AI agents built with **AWS Strands Agents (JavaScript SDK)** sorts each report into a category, merges duplicates, ranks issues by urgency, and recommends which department and crew should handle it. A city dispatcher approves every recommendation.

CityCare is not tied to one city: reports can come from anywhere, and addresses, area names and map search use OpenStreetMap. The repo ships **sample data for Kansas City, MO** (streets, neighborhoods, simulated crews and demo reports) for testing and the HackMidwest demo. See [Running it for another city](#running-it-for-another-city).

```
Resident report ─► Intake ─► Dedup ─┬─ duplicate ─► merge into issue ─┬─► Priority ─► Router ─► Dispatcher approves
                                     └─ new ───────► create issue ─────┘
Dispatcher question ─► Supervisor ──tools──► query_issues, get_stats, Priority & Router agents
```

## Quick start (Docker)

```bash
cp .env.example .env          # optional; defaults to mock mode (no AWS needed)
docker compose up --build
```

- Citizen Portal: http://localhost:8080
- Dispatch Command console: http://localhost:8080/#/dispatch

Every incident comes from reports residents submit on the website: a new database starts empty, and each report runs through the agents as it arrives. The **AI Triage Pipeline** screen shows the agents' live trace, merges and totals for those reports. **Reset data** deletes all reports and incidents (dispatcher accounts are kept). For an offline demo with something on the map, set `SEED_SOURCE=sample` to load the bundled sample reports into an empty database.

## Dispatcher accounts

The **Dispatch Command** console needs a dispatcher login; the **Citizen Portal** stays open so residents can report without an account. Open Dispatch Command and choose **Sign up** to create an account (name, email, password of 8+ characters), or **Log in**. The avatar menu in the console shows who is signed in and has **Log out**.

- Accounts live in the database (`users` collection in MongoDB, or the local state file). Passwords are stored only as salted scrypt hashes.
- A login sets an HTTP-only, SameSite=Lax session cookie valid for 7 days, signed with `AUTH_SECRET` (or a secret generated once and stored in the database, so every copy of the app sharing it accepts the same logins).
- Set `DISPATCHER_SIGNUP_CODE` to require a code for new accounts. Without it, anyone who can reach the site can sign up as a dispatcher, which is fine for a demo but not for a real deployment.
- Dispatcher-only API calls (approve, reject, status changes, Supervisor chat, route plans, reset, the report list) return `401` without a login. Residents' contact details are left out of public issue details. Status changes record the dispatcher's name.
- Login and sign-up allow 10 attempts per minute per address.
- Accounts survive **Reset data**.

## Database

CityCare stores issues, reports, crews and report photos in **MongoDB** through **Prisma** (`api/prisma/schema.prisma`). Point every copy of the app at one database, such as a free MongoDB Atlas M0 cluster, and the whole team shares the same data.

1. In Atlas, open **Connect → Drivers** and copy the connection string. Add a database name after the host: `mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/citycare?retryWrites=true&w=majority`. URL-encode special characters in the password.
2. Under **Network Access**, allow the IP of every machine that runs the API (or `0.0.0.0/0` for a hackathon demo).
3. Put it in `.env` as `DATABASE_URL=...` and start the app. The API creates the collections and indexes on first start and starts empty (or with the sample reports if `SEED_SOURCE=sample`). `/api/health` shows `"database": { "backend": "mongodb" }`.

Without `DATABASE_URL`, data lives in a local JSON file (`STATE_DIR`), which is handy for offline demos and tests.

Notes:
- The API keeps a working copy in memory and writes each change to MongoDB within a fraction of a second, retrying if the database is briefly unreachable.
- **Several copies can share one database** (for example, each teammate running the app against the same Atlas cluster). Issue and report numbers come from atomic counters in the `counters` collection, so two copies never hand out the same number. Each copy checks the database for the others' changes every 3 seconds (`SYNC_INTERVAL_MS`) and pushes them to its browsers live, and a **Reset data** on one copy reloads all of them. If two copies change the same issue at the same moment, the later write wins.
- **Reset data** deletes all issues and reports in the database and restarts numbering at #1040 (photos are kept).
- Photos are stored in the `photos` collection. M0 has a 512 MB limit, so keep demo photos small.
- `cd api && npm run db:studio` opens Prisma Studio to browse the data. `npm run db:push` applies schema changes; after editing the schema, run `npx prisma generate`.
- Prisma 7 dropped MongoDB support, so the project pins Prisma 6.

## The UI

- **Citizen Portal:** a full-screen map with a floating "Report an Issue" card. Residents pick a category (or leave it on Auto for the Intake agent), drop or drag a pin, or type a location and pick from the suggestions dropdown, attach a photo, and describe the problem. Before they submit, the card shows open incidents within 120 m. After they submit, it streams the agents' work live and shows the result (for example, "merged into #1042, P1").
- **Dispatch Command:** a console with five views.
  - **Command Center:** a ranked live triage stream, a tactical map with P1/P2 heatmap, crew telemetry and neighborhood layers, and an incident drawer showing the priority factors, the routing recommendation, merged reports, the agent audit trail, and Approve / Change crew / Reject.
  - **GIS Spatial Grid:** a density breakdown by neighborhood.
  - **AI Triage Pipeline:** the four agents, batch metrics, the live agent trace and the dedup event log.
  - **Routing Matrix:** the SLA table.
  - **Field Crews:** crew workload and assignments.
- **Supervisor Channel:** plain-English questions answered by the Supervisor agent.

**Report photos** can be in any common format: JPEG, PNG, HEIC/HEIF (iPhone), WebP, AVIF, GIF, BMP or TIFF. The browser converts each photo to an upright JPEG of at most 2048 px before uploading (iPhone HEIC through a converter that loads only when needed), and the API converts again with [sharp](https://sharp.pixelplumbing.com), so every stored photo is a JPEG without metadata. That also removes the GPS coordinates phones embed, which often point at the resident's home. Uploads can be up to 25 MB; SVG and non-image files are refused with a clear message.

Address suggestions, address lookup for a dropped pin, and area names work for any location through [Photon](https://photon.komoot.io), a free OpenStreetMap geocoder with no API key, biased toward the current map view. If the city data includes streets and landmarks (the Kansas City sample does), those are suggested first and work offline. Set `PHOTON_URL=off` to disable Photon.

Built with React, Tailwind CSS 4, lucide icons and Leaflet with free OpenStreetMap tiles (no API key). The OSM tile servers are fine for a hackathon demo; for heavier use, follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/) or self-host tiles.

Hot-reload development in Docker:

```bash
docker compose -f docker-compose.dev.yml up     # UI on http://localhost:5173, API on :8080
```

## Local development (no Docker)

Requires Node 22+.

```bash
cd api && npm install && npm run dev      # API on :8080; reads ../.env if present
cd web && npm install && npm run dev      # UI on :5173, proxies /api to :8080
cd api && npm test                        # rules, geo and end-to-end pipeline tests
# Also test MongoDB persistence against a disposable replica set (its CityCare data is wiped):
TEST_DATABASE_URL="mongodb://localhost:27017/citycare_test?replicaSet=rs0&directConnection=true" npm test
```

## Engines: mock vs Bedrock

| `CITYCARE_MODE` | What runs | Needs |
|---|---|---|
| `mock` (default) | Rule-based agents: keyword classifier, distance and text dedup, rubric priority, workload router. Deterministic and instant. | Nothing |
| `bedrock` | Strands agents on Claude via Amazon Bedrock. Haiku-class for intake; Sonnet-class for dedup, priority, router and supervisor. | AWS credentials with Bedrock access, model access enabled |

**Rate limits and queueing (Bedrock mode).** Every model call passes through one limiter (`api/src/lib/limiter.js`): at most `BEDROCK_MAX_CONCURRENCY` calls in flight and `BEDROCK_RPM` per minute, so bursts wait instead of hitting the account quota. At most `REPORT_CONCURRENCY` reports run the pipeline at once; later ones wait in arrival order and their trace shows "Queued: N reports ahead". If Bedrock throttles anyway, all calls pause and the call retries (up to 3 times) before the step falls back to rules. `GET /api/health` shows live queue and call counts.

In Bedrock mode, any failed LLM call (quota, bad model ID, network) falls back to the rule engine for that step. The trace marks the step as `fallback`, so a live demo never dead-ends. Model IDs are set with `INTAKE_MODEL_ID` and `REASONING_MODEL_ID` (see `.env.example`). The defaults are the profiles verified on the team's account: `us.anthropic.claude-haiku-4-5-20251001-v1:0` for intake and `us.anthropic.claude-sonnet-4-6` for the rest, in `us-east-2`.

**Check which engine is running:** the API logs a line at startup, e.g. `Engine: Bedrock (from CITYCARE_MODE) region=us-east-2 …`, and the navbar badge shows **BEDROCK** or **MOCK**. The old variable name `CITYOPS_MODE` is still accepted. After editing `.env`, restart with `docker compose up -d` so the container picks up the change; no rebuild is needed.

**"Too many requests" / throttling:** all Bedrock calls go through one adaptive limiter (`BEDROCK_RPM`, default 24/min). When Bedrock throttles anyway, the limiter halves its pace for every caller, recovers gradually, and the call retries with backoff for about 2.5 minutes. The live trace shows "Bedrock rate limit reached. Waiting N s…" while it waits. Only if the quota stays exhausted does that step fall back to the rules. Common causes: several teammates running the app on one AWS account at once, which share one quota; a low tokens-per-minute quota, which is why `BEDROCK_MAX_TOKENS` is kept small; or a new account's default quota. `GET /api/health` shows the limiter's current pace and throttle count. Lower `BEDROCK_RPM`, or ask AWS for a quota increase, if fallbacks persist.

The design rule from the plan holds in both modes: code does what code is good at, and the LLM makes the judgment calls.
- **Dedup:** code finds candidates by distance (radius per subcategory, e.g. 40 m for potholes, 150 m for main breaks), time window and category. The agent decides whether a candidate is the same physical problem. Low confidence becomes "possible duplicate", not a merge.
- **Route planning:** the Route Planner agent (Sonnet, `api/src/agents/routes.js`) groups each crew's open jobs (assigned, or recommended and awaiting approval) into one trip for today's 8-hour shift: urgent jobs first, nearby P3/P4 jobs ride along, and what does not fit is deferred with a reason. Code orders the stops and does the time math (`api/src/lib/routing.js`, simulated drive speeds and on-site minutes); the agent can call `estimate_route` to check a trip before committing. The Supervisor chat can call it as a tool ("Plan today's routes: which crew has the longest day?"). Dashboard: **Route Plans**.
- **Photos:** when a report has a photo, a Vision agent (Haiku, image input, `api/src/agents/photo.js`) describes it first: what it shows, category, severity (low to critical) and visible hazards. Intake uses that to classify vague or photo-only reports, and Priority sees the severity. Mock mode stores photos without analyzing them.
- **Priority:** code computes the rubric base score (safety +40, arterial +15, reports, sensitive sites, age). Critical hazards (signal out, open manhole, main break, tree blocking the road) are raised to a base of 80, so they reach P1 on the first report. The agent may adjust it by ±15 and must explain why.
- Every agent returns **Zod-validated structured output**. The server re-checks LLM answers, e.g. a merge target must be one of the candidates and the SLA must match the tier.

## Accuracy test set (mock engine, synthetic data)

The test suite runs 50 synthetic reports with known answers (`data/demo_reports.json`): **50 reports → 12 issues (76% duplicate reduction)**, category accuracy 100%, dedup precision/recall 100/100, including two potholes 85 m apart that correctly stay separate. The rule engine was tuned on these keywords, so the numbers overstate real-world accuracy; they're a regression check, not a benchmark. The app itself no longer uses these reports.

## Running it for another city

Nothing in the code names a city. Everything city-specific lives in the data folder (`DATA_DIR`, default `data/`):

| File | What it holds | Required |
|---|---|---|
| `city.json` → `profile` | Display name and region, address suffix, default zoom, example report, address and supervisor questions shown in the UI | `center` only; the rest is optional |
| `city.json` → `streets`, `neighborhoods`, `sensitive_sites` | Local street classes for the priority rubric, area names, schools and hospitals | Optional. Without them, area names come from OpenStreetMap, road class counts as unknown, and no sensitive-site points are added. |
| `categories.json`, `departments.json` | Issue categories and the departments and crews that handle them | Yes |
| `seed_reports.json`, `demo_reports.json` | Sample history (only with `SEED_SOURCE=sample`) and the accuracy test set used by the tests | Synthetic |

A minimal `city.json` is just `{ "center": { "lat": 41.8781, "lng": -87.6298 } }`. With that, the UI says "City Services" and "City Operations", offers generic example questions, and reports anywhere are located through OpenStreetMap. The agents' instructions name the configured city when one is set.

## Project layout

```
api/                     Node service (Express 5) + agents          → owners A (agents), B (tools), C (API)
  prisma/schema.prisma   MongoDB schema: issues, reports, crews, photos, app_state
  src/agents/            intake, dedup, priority, router, supervisor (Strands) + rules.js (mock engine)
  src/tools/cityTools.js tool functions shared by both engines
  src/lib/               store (in-memory, saved to MongoDB or a JSON file), mongo (Prisma), geo (gazetteer), events (trace bus), data loader
  src/pipeline.js        Strands Graph for single reports; batch path
  src/server.js          REST + SSE
  test/                  node:test suite
web/                     React (Vite) + Tailwind + Leaflet: Citizen Portal and Dispatch console → owner D
data/                    sample city data (Kansas City): profile, geography, categories, departments/crews (simulated), seed + demo reports
scripts/generate-demo-data.js   regenerates data/seed_reports.json and data/demo_reports.json
```

The single-report pipeline is a **Strands `Graph`** (`buildReportGraph` in `api/src/pipeline.js`): `intake → dedup → priority → router`, one node per agent. Nodes share the report and issue ids through the graph's app state. The `priority → router` edge is conditional: a report merged into an issue a dispatcher already approved re-scores it but does not re-route it. `GET /api/graph` returns the topology for the UI. The batch path reuses the same steps but schedules them in code, so it can run intake in parallel, keep dedup serialized and triage each touched issue once. The supervisor uses the agents-as-tools pattern.

## API contract

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/reports` | `{ text, lat?, lng?, address?, photo? (data URL), category_hint?, client_run_id? }` → runs the pipeline, returns `{ report, issue, merged, run_id }`. Without lat/lng it geocodes cross streets from the text. |
| `GET` | `/api/issues?status=open\|all\|<status>` | Ranked by priority |
| `GET` | `/api/issues/:id` | Includes `reports[]` and `agent_trace[]` (audit trail) |
| `POST` | `/api/issues/:id/approve` | `{ crew_id?, note? }`: approve as-is, or edit the crew first |
| `POST` | `/api/issues/:id/reject` | `{ reason }` |
| `PATCH` | `/api/issues/:id` | `{ status }`: `in_progress`, `resolved`, … |
| `POST` | `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout` | Dispatcher accounts: `{ name, email, password, code? }` / `{ email, password }`; sets or clears the session cookie |
| `GET` | `/api/auth/me`, `/api/auth/config` | The signed-in dispatcher (or `null`); whether sign-up needs a code |
| `GET` | `/api/stream` | SSE: `trace` events (every agent step and tool call) and `issue` updates |
| `POST` | `/api/chat` | `{ question }` → supervisor answer |
| `GET` | `/api/address-suggest?q=` | Autocomplete: `[{ label, sublabel, address, lat, lng, kind, source }]` |
| `GET` | `/api/graph` | Strands Graph topology: nodes, edges, edge conditions |
| `POST` | `/api/routes/plan` | Route Planner agent: today's crew trips, deferred jobs, drive time saved |
| `GET` | `/api/routes` | Latest route plan |
| `GET` | `/api/nearby?lat&lng` | Open issues near a point (pre-submit duplicate hint) |
| `GET` | `/api/crews` | Crews with workload and active assignments |
| `GET` | `/api/stats`, `/api/meta` | Dashboard numbers; categories, departments, crews, neighborhoods |
| `POST` | `/api/reset` | Delete all incidents and reports (accounts are kept) |

Trace event shape (see `api/src/lib/events.js`): `{ event_id, ts, run_id, report_id?, issue_id?, agent, status: started|tool|completed|error, message, data?, engine?, model?, duration_ms? }`.

## Before the demo / what still needs access

- **AWS:** credentials and Bedrock model access for Claude Haiku-class and Sonnet-class in one region. Then set `CITYCARE_MODE=bedrock` and the model IDs, and run one report end to end. The Bedrock path has not yet been run against a live account; it has been checked only up to the credential step.
- **Geography:** `data/city.json` uses approximate straight-line street positions and hand-picked sites. Verify the sensitive sites, or swap in Amazon Location Service or Nominatim.
- **Not built yet (stretch):** Titan embeddings for semantic dedup (currently bag-of-words similarity), map clustering, resident notifications, equity adjustment, AgentCore deploy.
