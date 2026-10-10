# CityOps — Autonomous City Issue Manager

> Residents report potholes, broken streetlights, trash, and similar problems. A team of AI agents built with AWS Strands sorts each report into a category, merges duplicates, ranks issues by urgency, and recommends which city department and crew should handle it. A city staff member approves the recommendations.

---

## 1. The pitch (30 seconds)

**Problem:** City 311 systems get thousands of messy, repeated reports. One pothole might come in 15 times as "big hole on Main," "my tire popped near 5th & Main," and a photo with no text. Staff sort these by hand, duplicates waste crew time, and dangerous issues can wait behind minor ones.

**Solution:** CityOps puts a pipeline of agents between residents and city staff:

1. **Understands** free-form reports (text, photo, location).
2. **Merges** duplicates into one issue, so 15 reports become 1 issue with 15 reporters.
3. **Ranks** issues by safety risk, impact, and age.
4. **Recommends** a department and crew, with a written reason.
5. **Keeps a human in the loop.** A dispatcher approves, edits, or rejects each recommendation.

**Why agents and not one prompt:** each step needs different tools (map lookups, a search of past issues, crew schedules) and its own reasoning. Splitting the work also lets us show judges the trace of agents handing work to each other.

**Local angle (HackMidwest is in Kansas City):** Kansas City, MO publishes its real 311 data. If we demo on real KC streets and real KC report categories, the pitch lands harder.

---

## 2. Demo script (target 3 minutes)

Build backwards from this. If something doesn't serve the demo, it's a stretch goal.

1. **Resident view (phone-sized web page):** submit "Huge pothole on Troost near 39th, almost wrecked my car" plus a photo. The pin drops on a map.
2. **Live agent trace:** a side panel streams each agent's work:
   - Intake: "Category: Street / Pothole. Hazard words detected: 'almost wrecked'."
   - Dedup: "Matches existing issue #1042 (3 prior reports within 40 m in the last 6 days). Merging."
   - Priority: "Score 87/100: arterial road, 4 reports, vehicle damage risk, 6 days open."
   - Router: "Recommend Public Works, Street Maintenance Crew B (12 open jobs, nearest)."
3. **Dispatcher dashboard:** a map of clustered issues and a priority-ranked queue. The issue jumps to the top. The dispatcher clicks **Approve**.
4. **Wow moment:** paste in a batch of 50 seeded reports. In about 30 seconds the queue settles into around 12 real issues, each with a department assignment. Show the numbers: "50 reports → 12 issues, 76% duplicate reduction."
5. **Optional closer:** the dispatcher asks in plain English, "What are the most dangerous open issues in Midtown?" and the supervisor agent answers.

---

## 3. Agent architecture

### Recommended Strands pattern

- **Main pipeline = Graph.** The pipeline is deterministic (Intake → Dedup → Priority → Router), so it's easy to debug and easy to show as a diagram.
- **Dispatcher chat = Agents-as-tools.** A "City Supervisor" agent can call the specialist agents and data tools to answer questions.
- **Skip Swarm** unless there's spare time. Agents handing off to each other on their own looks cool but is harder to make reliable in 24 hours.

```
Resident report ──► [Intake Agent] ──► [Dedup Agent] ──┬─ duplicate ─► merge into existing issue ─► [Priority Agent] (re-score)
                                                       └─ new ───────► create issue ─────────────► [Priority Agent]
                                                                                                         │
                                                                                                         ▼
                                                                                                  [Router Agent]
                                                                                                         │
                                                                                                         ▼
                                                                                    Dispatcher dashboard (human approves)

Dispatcher question ──► [Supervisor Agent] ──tools──► query_issues, the other agents, stats
```

### Agents, their jobs, and their tools

| Agent | Model tier | Input → Output | Tools |
|---|---|---|---|
| **Intake / Classifier** | Small, fast model (Haiku-class) | Raw text, photo, and location → structured report: category, subcategory, cleaned description, hazard flags, confidence | `geocode_address`, `reverse_geocode`, `analyze_photo` (vision model), `list_categories` |
| **Dedup** | Mid-tier model (Sonnet-class) | Structured report → `{duplicate_of: issue_id \| null, confidence, reason}` | `find_nearby_issues(lat, lng, radius_m, days, category)`, `semantic_search_issues(text)`, `get_issue(id)` |
| **Priority** | Mid-tier model | Issue plus context → score 0–100, priority tier (P1–P4), list of contributing factors | `get_road_type`, `nearby_sensitive_sites` (schools, hospitals), `get_issue_history`, `get_weather` (stretch) |
| **Router / Dispatch** | Mid-tier model | Prioritized issue → department, crew, suggested SLA, reason | `list_departments`, `get_crew_workload`, `get_crew_locations` |
| **Supervisor** (dispatcher chat) | Mid-tier model | Natural-language question → answer | `query_issues`, `get_stats`, the agents above wrapped as tools |

**Design rule:** let deterministic code do what code is good at, and let the LLM decide the judgment calls.
- **Dedup:** code finds candidate matches by distance, time window, and category. The LLM decides whether a candidate is the same physical problem. For example, "streetlight out" and "dark corner, light broken" both 30 m apart should merge. Two separate potholes 80 m apart on the same block should not.
- **Priority:** code computes a base score from a rubric. The LLM adjusts it by up to ±15 and must explain why. This keeps scores consistent from run to run while still allowing judgment.

Use **structured output** (Strands supports Pydantic-model outputs) for every agent so each one returns JSON that matches a schema. Don't parse free text.

---

## 4. Data model (draft)

**Report**: one resident submission
- `report_id`, `created_at`, `raw_text`, `photo_url`, `lat`, `lng`, `address`, `reporter_contact` (optional)
- `category`, `subcategory`, `hazard_flags[]`, `classifier_confidence`
- `issue_id`: the issue it was merged into

**Issue**: one real-world problem, grouping one or more reports
- `issue_id`, `category`, `subcategory`, `lat`, `lng` (centroid), `address`, `summary`
- `report_count`, `first_reported_at`, `last_reported_at`
- `priority_score`, `priority_tier` (P1–P4), `priority_factors[]`
- `recommended_department`, `recommended_crew`, `routing_reason`, `suggested_sla_hours`
- `status`: `new` → `triaged` → `approved` → `assigned` → `in_progress` → `resolved`
- `agent_trace[]`: what each agent decided and why (powers the demo panel and the audit trail)

**Department / Crew** (seed data)
- `department_id`, `name`, `categories_handled[]`
- `crew_id`, `department_id`, `home_lat/lng`, `open_jobs`, `capacity`

---

## 5. Categories and department mapping

Base these loosely on Kansas City's 311 categories (check against the real dataset before finalizing).

| Category | Subcategories | Department |
|---|---|---|
| Streets | Pothole, street damage, sidewalk, curb | Public Works: Street Maintenance |
| Traffic & Lighting | Streetlight out, traffic signal, sign damaged/missing | Public Works: Traffic / Street Lighting |
| Trash & Sanitation | Missed pickup, illegal dumping, overflowing bin, bulky item | Solid Waste |
| Water | Main break, leak, flooding, sewer backup, open manhole | Water Services |
| Property & Nuisance | Graffiti, overgrown lot, abandoned vehicle, dangerous building | Neighborhood Services |
| Parks & Trees | Fallen tree/limb, park damage | Parks & Recreation |
| Animals | Dead animal, stray | Animal Services |
| Other / Unclear | — | Human review queue |

**Priority rubric (base score, 0–100):**
- Safety hazard to life or vehicles (open manhole, signal out, downed limb on road, main break): +40
- Road type: arterial +15, collector +8, residential +0
- Report count: +3 per extra report, capped at +15
- Near a school, hospital, or senior center (within 200 m): +10
- Days open: +2 per day, capped at +10
- Equity (stretch): adjustment for areas that historically report less, so quieter neighborhoods aren't always deprioritized. Judges tend to ask about this, so have an answer ready.
- Tiers: **P1** ≥ 80 (respond within 24 h) · **P2** 60–79 (72 h) · **P3** 40–59 (1 week) · **P4** < 40 (scheduled)

---

## 6. Data sources

| Need | Source | Notes |
|---|---|---|
| Real 311 history | **KCMO Open Data (data.kcmo.org)**, "311 Call Center Service Requests" via the Socrata API | Hundreds of thousands of records. Use it to seed existing issues, real categories, and real locations. **Before the hack: confirm the dataset ID and download a CSV extract (e.g., the last 90 days).** |
| Standard format | Open311 GeoReport v2 spec | Mention in the pitch: "CityOps can plug into any city that speaks Open311." |
| Demo reports | **Synthetic messy reports we generate**, about 50–100 short texts that deliberately include duplicates, typos, and slang, all pinned to real KC intersections | This is the key to the demo. We control the ground truth, so we can show dedup accuracy. |
| Photos | A handful of stock or self-taken photos of potholes, lights, and dumping | For the vision step in Intake. |
| Map / geocoding | Amazon Location Service, or Nominatim/OpenStreetMap (free) | Leaflet + OSM tiles for the map UI. |
| Schools / hospitals | OSM points of interest, or a KC open-data facilities list | For the priority "sensitive sites" factor. A small static JSON file is fine. |
| Crews | Made-up seed data (around 8 crews across departments) | Label it clearly as simulated. |

---

## 7. Tech stack (proposal)

- **Agents:** Strands Agents SDK (Python). Use the Graph pattern for the pipeline and agents-as-tools for the supervisor.
- **Models:** Amazon Bedrock, Anthropic Claude. Use a Haiku-class model for intake and classification and a Sonnet-class model for dedup, priority, routing, and the supervisor. **Check which model IDs are enabled in our account and region before the hack.**
- **Embeddings for semantic dedup:** Amazon Titan Text Embeddings on Bedrock. Store vectors next to issues and use cosine similarity in memory. That's fine at hackathon scale, so we don't need a vector database.
- **Backend:** FastAPI, with a streaming endpoint (SSE or WebSocket) that pushes agent trace events to the UI.
- **Storage:** SQLite or plain JSON for speed. DynamoDB if we want the "AWS-native" checkbox. Photos go in S3, or local files if S3 slows us down.
- **Frontend:** React (Vite) + Leaflet. Two views: Resident Report and Dispatcher Dashboard (map, queue, agent trace, approve button).
- **Deploy (stretch):** Bedrock AgentCore Runtime for the agents, plus Amplify or S3 static hosting for the UI. **Fallback: run it all on a laptop. Don't let deployment eat the last 3 hours.**
- **Observability:** Strands has OpenTelemetry tracing built in. The trace panel in our UI is the user-facing version.

---

## 8. Team split (4 people)

| Person | Owns | First deliverable |
|---|---|---|
| **A — Agents lead** | Strands Graph, all agent prompts and structured-output schemas, Bedrock setup | Intake agent classifying a hard-coded report end to end |
| **B — Data & tools** | KC 311 import, synthetic report generator, seed departments/crews/POIs, tool functions (`find_nearby_issues`, geocoding, embeddings) | Database loaded with seeded issues, plus `find_nearby_issues` working |
| **C — Backend/API** | FastAPI routes, issue/report persistence, merge logic, streaming trace events, approve/reject endpoints | `POST /reports` → runs the pipeline → returns the issue and streams the trace |
| **D — Frontend & pitch** | Resident form, dispatcher map and queue, trace panel, slides, demo video backup | Map showing seeded issues from a mock JSON file (no backend needed at first) |

**Agree on the integration contract in the first hour:** the JSON shapes for Report, Issue, and trace events (section 4). Then everyone builds against mocks in parallel.

---

## 9. Timeline (assumes about 24 hours of hacking; adjust to the real schedule)

| Phase | Goal |
|---|---|
| Hour 0–1 | Kickoff. Finalize data contracts, repo structure, AWS credentials working on all 4 laptops. |
| Hour 1–6 | Each person reaches their "first deliverable." The Intake agent runs alone. |
| Hour 6–10 | **Walking skeleton:** a report submitted in the UI flows through all 4 agents (even if they're dumb) and shows up on the dashboard. **This is the most important milestone.** |
| Hour 10–16 | Make the agents smart: dedup quality, priority rubric, routing reasons. Batch-import demo. |
| Hour 16–20 | Polish: trace panel animation, map clustering, approve flow, supervisor chat (stretch). |
| Hour 20–22 | **Feature freeze.** Rehearse the demo 3 or more times. Record a backup demo video. |
| Hour 22–24 | Slides, Devpost write-up, buffer. |

---

## 10. MVP vs. stretch

**MVP (must have for the demo):**
- [ ] Text report with location → category (Intake)
- [ ] Duplicate detection and merge (Dedup), with seeded data showing high reduction
- [ ] Priority score with factors (Priority)
- [ ] Department recommendation with reason (Router)
- [ ] Dispatcher dashboard: map, ranked queue, agent trace, approve button

**Stretch (in order):**
1. Photo understanding (vision tells pothole from streetlight and estimates severity)
2. Supervisor chat ("What's most urgent in Westport?")
3. Resident status notifications ("Your report was merged with 4 others and assigned to Public Works")
4. Crew route suggestions (group nearby P3/P4 jobs into one trip)
5. Equity-aware prioritization and a dashboard by neighborhood
6. Deploy on AgentCore with a public URL
7. SMS or voice intake (Amazon Connect / Pinpoint)

---

## 11. Before-we-start checklist (do this before the clock starts, if allowed)

- [ ] AWS account access for everyone. Pick **one region** where Bedrock has the Claude models (e.g., us-east-1 or us-west-2).
- [ ] **Bedrock model access enabled** for Claude Haiku-class, Claude Sonnet-class, and Titan Embeddings. Run one test call from each laptop.
- [ ] Python 3.10+ installed, Node 18+ installed.
- [ ] Skim the Strands docs: quickstart, `@tool`, structured output, multi-agent **Graph**, agents-as-tools. Note the current SDK version.
- [ ] Find the KC 311 dataset on data.kcmo.org, note its Socrata dataset ID, and download a CSV sample.
- [ ] List ~30 real KC intersections across neighborhoods (Midtown, Westport, Crossroads, Northeast, Waldo) for synthetic reports.
- [ ] Gather 5–10 issue photos.
- [ ] Create the GitHub repo, add teammates, and agree on the folder layout (`/agents`, `/api`, `/web`, `/data`).
- [ ] Check the hackathon rules: judging criteria, sponsor prize tracks (is there an AWS track?), and whether pre-made assets are allowed.
- [ ] Set a Bedrock budget alarm in AWS Budgets, so a runaway loop doesn't burn credits.

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Bedrock access or quota problems at the event | Enable access the night before. Keep a mock mode in which agents return canned results, so the UI demo still works. |
| Pipeline too slow for a live demo (4 sequential LLM calls) | Use the small model for intake. Run priority and nearby-site lookups in parallel. Stream the trace so the wait looks intentional. Pre-warm the system before the demo. |
| Dedup makes visible mistakes | Code-based candidate filtering first. LLM confirms only above a confidence threshold. Low confidence goes to "possible duplicate — needs review" rather than a forced merge. |
| Integration hell at hour 18 | Walking skeleton by hour 10. Shared JSON contracts. Mocks everywhere. |
| Scope creep | Section 10 is the contract. Stretch items only after the MVP boxes are checked. |
| Wi-Fi dies during the demo | Backup recorded video. Local SQLite and cached map tiles if possible. |

---

## 13. Judge Q&A prep

- **"Why multiple agents instead of one prompt?"** Each agent has its own tools, model size, and failure modes. We can swap a cheap model in for intake, test each step on its own, and show an audit trail per decision.
- **"Is the AI making decisions for the city?"** No. It recommends, and a human approves. Every recommendation records its reasoning (`agent_trace`).
- **"How do you measure accuracy?"** On the synthetic set we know the true duplicates and categories, so we report classification accuracy and dedup precision/recall. Put these numbers on a slide.
- **"How does this scale or plug into a real city?"** Open311 GeoReport v2 compatibility, AgentCore deployment, a swappable data layer.
- **"What about bias?"** Areas that report less get fewer fixes. We use a rubric with explicit factors and propose an equity adjustment, and every score is explainable.
- **"Cost?"** Rough number: Haiku-class intake plus Sonnet-class for the other three is a few cents per report or less. Compare that to staff triage time.

---

## Reference links

- Strands Agents 1.0 announcement (multi-agent primitives, A2A): https://strandsagents.com/blog/strands-agents-1-0/
- AWS deep dive on Strands architectures and observability: https://aws.amazon.com/blogs/machine-learning/amazon-strands-agents-sdk-a-technical-deep-dive-into-agent-architectures-and-observability
- Multi-agent pattern selection guide (Agents-as-Tools / Swarm / Graph / Workflow, June 2026): https://hidekazu-konishi.com/entry/strands_agents_multi_agent_patterns_guide.html
- Open311 GeoReport v2 spec: https://webarchive.library.unt.edu/web/20170118233000mp_/http://wiki.open311.org/GeoReport_v2
- KC 311 data (verify on data.kcmo.org): https://catalog.data.gov/dataset/311-service-and-information-requests/resource/0d33657b-ef5f-4d59-bbe3-8033e95c33c9
