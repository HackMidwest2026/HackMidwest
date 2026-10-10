# CityOps: Autonomous City Issue Manager

Residents report potholes, broken streetlights, trash and similar problems. A pipeline of AI agents built with **AWS Strands Agents (JavaScript SDK)** sorts each report into a category, merges duplicates, ranks issues by urgency, and recommends which department and crew should handle it. A city dispatcher approves every recommendation.

Built for HackMidwest (Kansas City). The geography, categories and demo data use real KC streets.

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

- Resident view: http://localhost:8080
- Dispatcher dashboard: http://localhost:8080/#/dispatch

On first start the API seeds 13 historical reports, which become 8 open issues. Click **Run demo batch** on the dashboard to run 50 messy reports through the agents. **Reset demo** restores the seeded history.

Hot-reload development in Docker:

```bash
docker compose -f docker-compose.dev.yml up     # UI on http://localhost:5173, API on :8080
```

## Local development (no Docker)

Requires Node 22+.

```bash
cd api && npm install && npm run dev      # API on :8080 (mock mode)
cd web && npm install && npm run dev      # UI on :5173, proxies /api to :8080
cd api && npm test                        # rules, geo and end-to-end pipeline tests
```

## Engines: mock vs Bedrock

| `CITYOPS_MODE` | What runs | Needs |
|---|---|---|
| `mock` (default) | Rule-based agents: keyword classifier, distance and text dedup, rubric priority, workload router. Deterministic and instant. | Nothing |
| `bedrock` | Strands agents on Claude via Amazon Bedrock. Haiku-class for intake; Sonnet-class for dedup, priority, router and supervisor. | AWS credentials with Bedrock access, model access enabled |

In Bedrock mode, any failed LLM call (quota, bad model ID, network) falls back to the rule engine for that step. The trace marks the step as `fallback`, so a live demo never dead-ends. Model IDs are set with `INTAKE_MODEL_ID` and `REASONING_MODEL_ID` (see `.env.example`). Some accounts need a cross-region inference profile prefix such as `us.`.

The design rule from the plan holds in both modes: code does what code is good at, and the LLM makes the judgment calls.
- **Dedup:** code finds candidates by distance (radius per subcategory, e.g. 40 m for potholes, 150 m for main breaks), time window and category. The agent decides whether a candidate is the same physical problem. Low confidence becomes "possible duplicate", not a merge.
- **Priority:** code computes the rubric base score (safety +40, arterial +15, reports, sensitive sites, age). Critical hazards (signal out, open manhole, main break, tree blocking the road) are raised to a base of 80, so they reach P1 on the first report. The agent may adjust it by ±15 and must explain why.
- Every agent returns **Zod-validated structured output**. The server re-checks LLM answers, e.g. a merge target must be one of the candidates and the SLA must match the tier.

## Demo numbers (mock engine, synthetic data)

`POST /api/demo/batch`: **50 reports → 12 issues (76% duplicate reduction)**, category accuracy 100%, dedup precision/recall 100/100. This includes two potholes 85 m apart that correctly stay separate.

These numbers come from synthetic reports whose keywords the rule engine was tuned on, so they overstate real-world accuracy. Re-run the batch in Bedrock mode to get honest LLM numbers for the slides.

## Project layout

```
api/                     Node service (Express 5) + agents          → owners A (agents), B (tools), C (API)
  src/agents/            intake, dedup, priority, router, supervisor (Strands) + rules.js (mock engine)
  src/tools/cityTools.js tool functions shared by both engines
  src/lib/               store (JSON-persisted), geo (KC gazetteer), events (trace bus), data loader
  src/pipeline.js        Strands Graph for single reports; batch path
  src/server.js          REST + SSE
  test/                  node:test suite
web/                     React (Vite) + Leaflet                     → owner D
data/                    categories, departments/crews (simulated), KC geography, seed + demo reports
scripts/generate-demo-data.js   regenerates data/seed_reports.json and data/demo_reports.json
```

The single-report pipeline is a **Strands `Graph`** (`buildReportGraph` in `api/src/pipeline.js`): `intake → dedup → priority → router`, one node per agent. Nodes share the report and issue ids through the graph's app state. The `priority → router` edge is conditional: a report merged into an issue a dispatcher already approved re-scores it but does not re-route it. `GET /api/graph` returns the topology for the UI. The batch path reuses the same steps but schedules them in code, so it can run intake in parallel, keep dedup serialized and triage each touched issue once. The supervisor uses the agents-as-tools pattern.

## API contract

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/reports` | `{ text, lat?, lng?, address?, photo? (data URL), client_run_id? }` → runs the pipeline, returns `{ report, issue, merged, run_id }`. Without lat/lng it geocodes cross streets from the text. |
| `GET` | `/api/issues?status=open\|all\|<status>` | Ranked by priority |
| `GET` | `/api/issues/:id` | Includes `reports[]` and `agent_trace[]` (audit trail) |
| `POST` | `/api/issues/:id/approve` | `{ crew_id?, note? }`: approve as-is, or edit the crew first |
| `POST` | `/api/issues/:id/reject` | `{ reason }` |
| `PATCH` | `/api/issues/:id` | `{ status }`: `in_progress`, `resolved`, … |
| `GET` | `/api/stream` | SSE: `trace` events (every agent step and tool call) and `issue` updates |
| `POST` | `/api/chat` | `{ question }` → supervisor answer |
| `GET` | `/api/graph` | Strands Graph topology: nodes, edges, edge conditions |
| `GET` | `/api/stats`, `/api/meta` | Dashboard numbers; categories, departments, crews, neighborhoods |
| `POST` | `/api/demo/batch`, `/api/demo/reset` | Demo controls |

Trace event shape (see `api/src/lib/events.js`): `{ event_id, ts, run_id, report_id?, issue_id?, agent, status: started|tool|completed|error, message, data?, engine?, model?, duration_ms? }`.

## Before the demo / what still needs access

- **AWS:** credentials and Bedrock model access for Claude Haiku-class and Sonnet-class in one region. Then set `CITYOPS_MODE=bedrock` and the model IDs, and run one report end to end. The Bedrock path has not yet been run against a live account; it has been checked only up to the credential step.
- **KC 311 data:** confirm the dataset ID on data.kcmo.org, then import an extract to seed real history and check the category mapping in `data/categories.json`.
- **Geography:** `data/city.json` uses approximate straight-line street positions and hand-picked sites. Verify the sensitive sites, or swap in Amazon Location Service or Nominatim.
- **Not built yet (stretch):** photo analysis (photos are stored, and `analyze_photo` is a stub), Titan embeddings for semantic dedup (currently bag-of-words similarity), map clustering, resident notifications, equity adjustment, AgentCore deploy.
