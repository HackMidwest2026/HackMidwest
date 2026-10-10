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

On first start the API seeds 13 historical reports, which become 8 open issues. In the console, open **AI Triage Pipeline** and click **Run demo batch** to run 50 messy reports through the agents. **Reset demo** restores the seeded history.

## The UI

- **Citizen Portal:** a full-screen map with a floating "Report an Issue" card. Residents pick a category (or leave it on Auto for the Intake agent), drop or drag a pin, or type a location and pick from the suggestions dropdown, attach a photo, and describe the problem. Before they submit, the card shows open incidents within 120 m. After they submit, it streams the agents' work live and shows the result (for example, "merged into #1042, P1").
- **Dispatch Command:** a console with five views.
  - **Command Center:** a ranked live triage stream, a tactical map with P1/P2 heatmap, crew telemetry and neighborhood layers, and an incident drawer showing the priority factors, the routing recommendation, merged reports, the agent audit trail, and Approve / Change crew / Reject.
  - **GIS Spatial Grid:** a density breakdown by neighborhood.
  - **AI Triage Pipeline:** the four agents, batch metrics, the live agent trace and the dedup event log.
  - **Routing Matrix:** the SLA table.
  - **Field Crews:** crew workload and assignments.
- **Supervisor Channel:** plain-English questions answered by the Supervisor agent.

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
```

## Engines: mock vs Bedrock

| `CITYCARE_MODE` | What runs | Needs |
|---|---|---|
| `mock` (default) | Rule-based agents: keyword classifier, distance and text dedup, rubric priority, workload router. Deterministic and instant. | Nothing |
| `bedrock` | Strands agents on Claude via Amazon Bedrock. Haiku-class for intake; Sonnet-class for dedup, priority, router and supervisor. | AWS credentials with Bedrock access, model access enabled |

In Bedrock mode, any failed LLM call (quota, bad model ID, network) falls back to the rule engine for that step. The trace marks the step as `fallback`, so a live demo never dead-ends. Model IDs are set with `INTAKE_MODEL_ID` and `REASONING_MODEL_ID` (see `.env.example`). The defaults are the profiles verified on the team's account: `us.anthropic.claude-haiku-4-5-20251001-v1:0` for intake and `us.anthropic.claude-sonnet-4-6` for the rest, in `us-east-2`.

**Check which engine is running:** the API logs a line at startup, e.g. `Engine: Bedrock (from CITYCARE_MODE) region=us-east-2 …`, and the navbar badge shows **BEDROCK** or **MOCK**. The old variable name `CITYOPS_MODE` is still accepted. After editing `.env`, restart with `docker compose up -d` so the container picks up the change; no rebuild is needed.

The design rule from the plan holds in both modes: code does what code is good at, and the LLM makes the judgment calls.
- **Dedup:** code finds candidates by distance (radius per subcategory, e.g. 40 m for potholes, 150 m for main breaks), time window and category. The agent decides whether a candidate is the same physical problem. Low confidence becomes "possible duplicate", not a merge.
- **Priority:** code computes the rubric base score (safety +40, arterial +15, reports, sensitive sites, age). The agent may adjust it by ±15 and must explain why.
- Every agent returns **Zod-validated structured output**. The server re-checks LLM answers, e.g. a merge target must be one of the candidates and the SLA must match the tier.

## Demo numbers (mock engine, synthetic data)

`POST /api/demo/batch`: **50 reports → 12 issues (76% duplicate reduction)**, category accuracy 100%, dedup precision/recall 100/100. This includes two potholes 85 m apart that correctly stay separate.

These numbers come from synthetic reports whose keywords the rule engine was tuned on, so they overstate real-world accuracy. Re-run the batch in Bedrock mode to get honest LLM numbers for the slides.

## Running it for another city

Nothing in the code names a city. Everything city-specific lives in the data folder (`DATA_DIR`, default `data/`):

| File | What it holds | Required |
|---|---|---|
| `city.json` → `profile` | Display name and region, address suffix, default zoom, example report, address and supervisor questions shown in the UI | `center` only; the rest is optional |
| `city.json` → `streets`, `neighborhoods`, `sensitive_sites` | Local street classes for the priority rubric, area names, schools and hospitals | Optional. Without them, area names come from OpenStreetMap, road class counts as unknown, and no sensitive-site points are added. |
| `categories.json`, `departments.json` | Issue categories and the departments and crews that handle them | Yes |
| `seed_reports.json`, `demo_reports.json` | Demo history and the 50-report batch | For the demo only |

A minimal `city.json` is just `{ "center": { "lat": 41.8781, "lng": -87.6298 } }`. With that, the UI says "City Services" and "City Operations", offers generic example questions, and reports anywhere are located through OpenStreetMap. The agents' instructions name the configured city when one is set.

## Project layout

```
api/                     Node service (Express 5) + agents          → owners A (agents), B (tools), C (API)
  src/agents/            intake, dedup, priority, router, supervisor (Strands) + rules.js (mock engine)
  src/tools/cityTools.js tool functions shared by both engines
  src/lib/               store (JSON-persisted), geo (KC gazetteer), events (trace bus), data loader
  src/pipeline.js        orchestration: single-report and batch paths
  src/server.js          REST + SSE
  test/                  node:test suite
web/                     React (Vite) + Tailwind + Leaflet: Citizen Portal and Dispatch console → owner D
data/                    sample city data (Kansas City): profile, geography, categories, departments/crews (simulated), seed + demo reports
scripts/generate-demo-data.js   regenerates data/seed_reports.json and data/demo_reports.json
```

The pipeline is orchestrated in code instead of a Strands `Graph`. The flow is fixed (Intake → Dedup → Priority → Router), and the merge-or-create branch and the database writes between steps are plain code. Code orchestration also lets the batch path run intake and triage in parallel while keeping dedup serialized. Each step is still its own Strands `Agent` with its own tools, model tier and schema. The supervisor uses the agents-as-tools pattern.

## API contract

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/reports` | `{ text, lat?, lng?, address?, photo? (data URL), category_hint?, client_run_id? }` → runs the pipeline, returns `{ report, issue, merged, run_id }`. Without lat/lng it geocodes cross streets from the text. |
| `GET` | `/api/issues?status=open\|all\|<status>` | Ranked by priority |
| `GET` | `/api/issues/:id` | Includes `reports[]` and `agent_trace[]` (audit trail) |
| `POST` | `/api/issues/:id/approve` | `{ crew_id?, note? }`: approve as-is, or edit the crew first |
| `POST` | `/api/issues/:id/reject` | `{ reason }` |
| `PATCH` | `/api/issues/:id` | `{ status }`: `in_progress`, `resolved`, … |
| `GET` | `/api/stream` | SSE: `trace` events (every agent step and tool call) and `issue` updates |
| `POST` | `/api/chat` | `{ question }` → supervisor answer |
| `GET` | `/api/address-suggest?q=` | Autocomplete: `[{ label, sublabel, address, lat, lng, kind, source }]` |
| `GET` | `/api/nearby?lat&lng` | Open issues near a point (pre-submit duplicate hint) |
| `GET` | `/api/crews` | Crews with workload and active assignments |
| `GET` | `/api/stats`, `/api/meta` | Dashboard numbers; categories, departments, crews, neighborhoods |
| `POST` | `/api/demo/batch`, `/api/demo/reset` | Demo controls |

Trace event shape (see `api/src/lib/events.js`): `{ event_id, ts, run_id, report_id?, issue_id?, agent, status: started|tool|completed|error, message, data?, engine?, model?, duration_ms? }`.

## Before the demo / what still needs access

- **AWS:** credentials and Bedrock model access for Claude Haiku-class and Sonnet-class in one region. Then set `CITYCARE_MODE=bedrock` and the model IDs, and run one report end to end. The Bedrock path has not yet been run against a live account; it has been checked only up to the credential step.
- **KC 311 data:** confirm the dataset ID on data.kcmo.org, then import an extract to seed real history and check the category mapping in `data/categories.json`.
- **Geography:** `data/city.json` uses approximate straight-line street positions and hand-picked sites. Verify the sensitive sites, or swap in Amazon Location Service or Nominatim.
- **Not built yet (stretch):** photo analysis (photos are stored, and `analyze_photo` is a stub), Titan embeddings for semantic dedup (currently bag-of-words similarity), map clustering, resident notifications, equity adjustment, AgentCore deploy.
