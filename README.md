# CareerGraph AI

> **Know your gap. Build your path. Meet your mentor.**

A career intelligence platform for BTech / final-year students. It analyses skills from
multiple sources, computes skill gaps against target occupations, generates
prerequisite-ordered learning roadmaps, verifies skills with short assessments, turns public
GitHub repositories into evidence-backed skill suggestions, and ranks alumni mentors against
the gaps that remain.

---

## Current Status

This table describes **what is actually implemented and verified in this repository**,
not what is planned.

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Foundation — FastAPI, React, JWT auth, database, health checks |
| Phase 2 | ✅ Complete | User Profiles — student & alumni profiles, completion score, mentor directory |
| Phase 3 | ✅ Complete | Resume Intelligence — PDF/DOCX/TXT parsing, skill extraction with confidence & evidence, student review & confirmation |
| Phase 4 | ✅ Complete | Skill Gaps & Career Readiness — occupation catalog, deterministic readiness scoring |
| Phase 5 | ✅ Complete | Skill Graph & Learning Roadmap — dependency graph, prerequisite-ordered roadmaps, progress tracking |
| Phase 6 | ✅ Complete | GitHub + LinkedIn — live public GitHub verification with evidence-backed skill suggestions; LinkedIn stored as a self-declared (unverified) link |
| Phase 7 | ⛔ Not started | RAG knowledge base + LLM explanations (OpenRouter) |
| Phase 8 | ✅ Complete | Skill Assessments & Alumni Matching — curated question bank, deterministic grading, evidenced skills, ranked mentors, mentorship requests |

### Explicitly *not* implemented (do not assume otherwise)

* **LLM usage** — no LLM is called anywhere. All scores, explanations, roadmap ordering,
  assessment grading and mentor ranking are deterministic and computed in Python.
  `OPENROUTER_API_KEY` exists in config for a future phase but is unused.
* **Neo4j** — a Neo4j adapter exists and is code-complete, but it is **unverified against a
  live server** (no instance is available in the development environment). The default and
  tested graph backend is the built-in in-memory graph.
* **Learning resources / course links** — roadmaps do *not* include course URLs. No curated
  resource dataset exists, so no links are invented.
* **GitHub** — verification uses the **public, unauthenticated** GitHub REST API only: no OAuth,
  no personal access token, no private repositories, and no repository code is downloaded.
  Unauthenticated calls are limited to 60 requests/hour per IP; when the limit is hit the API
  returns `503` with an explicit message. Up to 100 of the account's most recently pushed public
  repositories are analysed, and **forks are excluded** from all evidence.
* **LinkedIn is not verified.** LinkedIn exposes no public API for reading a member's profile, so
  a LinkedIn URL is stored as a *self-declared* link and always returned with `verified: false`.
  The UI labels it "Unverified — self-declared".
* **RAG / LLM explanations** — not started.
* **spaCy / sentence-transformers** — not used. Skill extraction is regex matching against a
  curated in-repo taxonomy (see below).
* **Adaptive / AI-generated assessments** — the Phase 8 question bank is a small curated set
  authored in-repo (`backend/app/data/assessments.py`), not generated. Grading is exact
  answer matching; there is no NLP or semantic grading, and a pass is **not** a certification.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router, Axios |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | SQLite (local dev) / PostgreSQL (staging & production) |
| Migrations | Alembic |
| Graph | In-memory backend (default, tested); optional Neo4j backend (unverified) |
| Skill extraction | Regex matching + curated taxonomy (no ML models) |
| GitHub verification | Public GitHub REST API, unauthenticated (no OAuth/token) |
| Auth | JWT (HS256) + bcrypt |

---

## Quick Start

### Prerequisites
- Python 3.11+ (developed and verified against 3.14)
- Node.js 18+
- Git

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at <http://localhost:8000> · API docs at <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at <http://localhost:5173>

### Database migrations

Tables are also created automatically on startup in development, but migrations are the
authoritative schema history:

```bash
cd backend
python -m alembic upgrade head        # apply migrations
python -m alembic current             # show current revision
python -m alembic check               # verify models match the schema
```

Revisions: `0001_baseline` (users, profiles, resumes), `0002_roadmaps` (Phase 5 tables),
`0003_assessments_mentorship` (Phase 8 tables) and `0004_github_verifications` (Phase 6 table).
All are additive; nothing is dropped or reset.

---

## Environment Configuration

Copy `.env.example` to `backend/.env` and fill in values.

```ini
DATABASE_URL=sqlite:///./careergraph_dev.db

# Skill graph: "memory" (default, always available) or "neo4j"
GRAPH_BACKEND=memory
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

For PostgreSQL (when Docker is available):

```bash
docker compose up -d
# Then update backend/.env:
DATABASE_URL=postgresql+psycopg2://careergraph:careergraph_pass@localhost:5432/careergraph_db
```

If `GRAPH_BACKEND=neo4j` but the server is unreachable or the driver is missing, the app logs
a warning and transparently falls back to the in-memory graph instead of failing.

---

## API Endpoints

### Authentication & System (Phase 1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Server + DB health check | No |
| POST | `/auth/register` | Create account | No |
| POST | `/auth/login` | Login, get JWT token | No |
| GET | `/auth/me` | Get current user | Yes |

### User Profiles & Mentors (Phase 2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/profile/me` | Current user's profile + completion score | Yes |
| PUT | `/profile/student` | Update student education, target role & skills | Student |
| PUT | `/profile/alumni` | Update alumni role, expertise & availability | Alumni |
| GET | `/profile/{user_id}` | Public profile for any user | Yes |
| GET | `/alumni` | List available alumni mentors (with `expertise` filter) | No |

### Resume Intelligence (Phase 3)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/resume/upload` | Upload & parse a resume (PDF, DOCX, TXT ≤ 10 MB) | Student |
| GET | `/resume/latest` | Most recent parsed resume for the current user | Student |
| POST | `/resume/confirm-skills` | Confirm/replace the student's skills (syncs to the profile) | Student |

### Skill Gaps & Career Readiness (Phase 4)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/career/occupations` | List the curated occupation catalog | Yes |
| GET | `/career/occupations/{key}` | One occupation with its required & optional skills | Yes |
| GET | `/career/gap-analysis` | Deterministic readiness analysis (`?occupation=` optional) | Student |

### Skill Dependency Graph (Phase 5A)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/graph/stats` | Active backend, node/edge counts, acyclicity | Yes |
| GET | `/graph/skills/{skill}` | Transitive prerequisites + direct dependents | Yes |

### Learning Roadmap (Phase 5B)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/roadmap/generate` | Generate a prerequisite-ordered roadmap | Student |
| GET | `/roadmap` | Current active roadmap | Student |
| GET | `/roadmap/{roadmap_id}` | One roadmap you own | Student |
| GET | `/roadmap/{roadmap_id}/explanations` | Per-step explanations | Student |
| POST | `/roadmap/{roadmap_id}/steps` | Update one step's progress | Student |
| POST | `/roadmap/refresh` | Regenerate from current skills & target role | Student |

All roadmap endpoints are ownership-scoped: requesting another user's roadmap returns `404`.

### Skill Assessments (Phase 8)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/assessments` | List the curated assessment catalogue | Student |
| GET | `/assessments/attempts` | Your attempt history (newest first) | Student |
| GET | `/assessments/{key}` | One assessment's questions — **answers are never included** | Student |
| POST | `/assessments/{key}/start` | Open a new attempt and return its questions | Student |
| POST | `/assessments/attempts/{id}/submit` | Grade an attempt deterministically | Student |
| POST | `/assessments/attempts/{id}/confirm-skills` | Add skills *passed in this attempt* to your profile | Student |

### Alumni Matching & Mentorship (Phase 8)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/mentorship/matches` | Rank alumni mentors for the current student | Student |
| GET | `/mentorship/requests` | Requests you sent (student) or received (alumni) | Yes |
| POST | `/mentorship/requests` | Request mentorship from a mentor | Student |
| POST | `/mentorship/requests/{id}/accept` | Accept a request (targeted mentor only, capacity enforced) | Alumni |
| POST | `/mentorship/requests/{id}/decline` | Decline a request (targeted mentor only) | Alumni |
| POST | `/mentorship/requests/{id}/cancel` | Cancel your own pending request | Student |

Request actions are party-scoped. A user who is not the student or the targeted mentor gets
`404` (not `403`) so the endpoint never confirms that someone else's request exists; a party who
lacks the required role gets `403`.

### GitHub Verification & LinkedIn (Phase 6)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/verification/github` | Fetch a public GitHub account + repositories, store the analysis | Student |
| GET | `/verification/github` | The stored verification (`404` if none) | Student |
| DELETE | `/verification/github` | Unlink the account; GitHub-sourced skills become self-reported | Student |
| POST | `/verification/github/confirm-skills` | Add selected *detected* skills to the profile | Student |
| POST | `/verification/linkedin` | Save a LinkedIn profile URL as **self-declared, unverified** | Student |
| GET | `/verification/linkedin` | The stored LinkedIn link (`404` if none) | Student |
| GET | `/verification/status` | Combined GitHub + LinkedIn status | Student |

One GitHub login can be linked to only one CareerGraph account (`409` on a second claim, checked
case-insensitively). GitHub failures are mapped honestly: unknown account → `404`, exhausted rate
limit → `503`, network timeout/DNS failure → `503`, any other upstream error → `502`. A
verification is never reported as successful unless GitHub actually returned the data.

---

## How the Readiness Score Works (Phase 4)

The score is **deterministic, explainable and reproducible**. No LLM is involved and it is
**not** a probability of employment.

```
readiness = round( 100 × Σ weight(matched required skills)
                        / Σ weight(all required skills) )
```

* Each required skill in the occupation catalog carries an importance weight (1–5).
* **Presence** of a skill counts; the self-reported level is shown but does not change the score.
* Only `required_skills` affect the score. `optional_skills` are reported as bonuses and never
  lower the score.
* Skill names are normalised through the taxonomy (e.g. `postgres` → `PostgreSQL`); duplicates
  collapse to the highest stated level.
* Skills outside the taxonomy are returned in `unknown_skills` and neither help nor hurt.

The API returns a per-skill contribution breakdown (`contributions`), a human-readable
`explanation`, and a `disclaimer` stating the metric is not a hiring probability.

---

## How the Skill Graph & Roadmap Work (Phase 5)

**Data.** The graph is built from a curated, in-repo prerequisite dataset
(`backend/app/data/skill_prerequisites.py`) in which every edge is tagged
`source="curated"` and carries a rationale. Every skill referenced is a canonical name from
`backend/app/data/skills_taxonomy.py`. No ESCO/O*NET records or identifiers are claimed or
invented.

**Backends.** `BaseSkillGraph` implements the algorithms (bounded traversal, missing-prerequisite
discovery, deterministic topological ordering, cycle detection). `InMemorySkillGraph` is the
default and the one the test suite exercises. `Neo4jSkillGraph` persists edges in Neo4j and
reloads them via Cypher, then reuses the same algorithms.

**Roadmap generation.**

1. Required skills for the target occupation are read from the Phase 4 catalog.
2. Required skills the student already has become `possessed_skills` and are **never scheduled**.
3. Missing prerequisites of the outstanding skills are discovered via the graph.
4. Steps are topologically ordered — **a prerequisite never appears after the skill that
   depends on it** (verified by tests). Ordering is deterministic (lexicographic tie-breaks).
5. Steps are snapshotted on the roadmap; progress lives in `roadmap_step_progress` so a single
   step can be updated without rewriting the snapshot.
6. If dependency data is incomplete (empty graph, unknown skills, or a cycle), the roadmap is
   flagged `is_partial` with a `notes` explanation instead of guessing.

Refreshing preserves progress for steps that still exist. Only one roadmap is active per user;
regenerating archives the previous one.

---

## How GitHub Verification Works (Phase 6)

**What is verified.** The account itself: login, display name, bio, avatar, public repository
count, followers and account age, plus the metadata of up to 100 recently pushed public
repositories. This data is fetched live from `https://api.github.com` at request time.

**What is *not* verified.** The inferred skills are a **deterministic heuristic over repository
metadata**, not a statement about the quality of the code:

* A repository's GitHub `primary language` is mapped to a canonical taxonomy skill through a
  small curated table (`Python → Python`, `Shell → Shell / Bash`, `Dockerfile → Docker`, …).
  Unmappable languages (`Jupyter Notebook`, `HCL`, `Objective-C`, …) are skipped, never guessed.
* Repository **topics** are normalised through the same taxonomy alias index
  (`machine-learning → Machine Learning`, `nextjs → Next.js`, `ci-cd → CI/CD`).
* **Forks are excluded** from every piece of evidence.
* A skill used by both the language and a topic in the same repository counts that repository once.

**Confidence and level are deterministic.**

```
repositories using the skill:  1 → 0.60   2 → 0.70   3–4 → 0.80   5+ → 0.90
+ 0.05 if total stars ≥ 5, capped at 0.95

proficiency: 4+ repos or ≥10 stars → advanced
             2+ repos or ≥ 1 star   → intermediate
             otherwise              → beginner
```

The API returns, per skill, the confidence, repository count, repository names (up to 10), star
count, sources (`language` / `topic`) and a human-readable evidence string. Skills are sorted by
`(−confidence, −repo_count, name)`, so the same repositories always produce the same output.

**Evidence requires explicit confirmation.** Verification only *suggests* skills. The server
re-checks that every requested skill was detected by the stored verification (`400` otherwise)
before writing it with `source="github"`. Confirming keeps any existing stated level, never
downgrades assessment evidence, and does not touch remote/detected state. A later resume review
preserves GitHub-evidenced skills. Unlinking the account keeps the skills but downgrades them to
`source="self"`, because the evidence behind them is gone.

**LinkedIn.** There is no public API for a member's profile, so nothing is inferred from a
LinkedIn URL. It is validated (`linkedin.com/in/<slug>`), canonicalised, stored on the profile,
and always reported as `verified: false`.

---

## How the Assessments Work (Phase 8)

**Question bank.** A small, curated bank lives in `backend/app/data/assessments.py`
(10 assessments, 38 questions, 19 canonical skills, 2 questions per skill). Every assessment is
tagged `source="curated"`; no official certification or external item bank is claimed.
`validate_assessment_bank()` is asserted by the test suite, so a malformed or duplicated
question fails the build rather than reaching a student.

**Grading is deterministic.**

```
score_percent = round(100 × correct answers / total questions)
skill passed  = round(100 × correct answers for that skill / that skill's questions) ≥ 70
```

* Answers are compared by index — no fuzzy or semantic matching.
* A question left unanswered counts as **incorrect**.
* Each skill is graded on its own questions, so a skill can be evidenced even if the overall
  score is below 70.
* Duplicate answers and out-of-range indices are rejected with `400`; re-submitting a graded
  attempt is `409`.

**Answers never leak.** The public question schema deliberately has no answer field. Correct
answers and explanations are only returned *after* submission, in the review section.

**Evidence requires explicit confirmation.** A pass only *suggests* skills. The student chooses
which ones to add, and the server re-checks that each requested skill was actually passed in
that attempt (`400` otherwise) before writing it to the profile with `source="assessment"`.
Confirming preserves an existing stated level and never discards it. Conversely, re-running the
Phase 3 resume review preserves assessment-evidenced skills rather than overwriting them.

Verified evidence feeds straight back into the Phase 4 readiness score.

---

## How Mentor Matching Works (Phase 8)

The match score is a **deterministic weighted heuristic used to order a list** — it is *not* a
probability, a prediction, or a promise of a good mentor. The API returns the full breakdown
(`factors`) and a disclaimer, and `match_score == Σ factor.earned`.

| Factor | Weight | Awarded when |
|--------|--------|--------------|
| `gap_overlap` | 40 | proportional to how many of the student's *outstanding* skills the mentor covers |
| `same_college` | 20 | the mentor and student list the same college |
| `experience` | 15 | proportional to years of experience, capped at 10 years |
| `availability` | 15 | the mentor has `is_available_for_mentoring` set |
| `capacity` | 10 | proportional to free mentee slots (`max_mentees − accepted`) |
| **Total** | **100** | |

* Skill matching normalises through the taxonomy and falls back to word-boundary matching for
  free-text expertise, so `Java` does **not** match `javascript`.
* A student with no target role simply scores `gap_overlap = 0`; everything else still applies.
* Ties are broken deterministically (`−score`, `−overlap`, name, id), so the list is stable.
* Mentors who are at capacity or unavailable are **still listed** — they are scored lower rather
  than hidden, and the UI explains why.

**Mentorship lifecycle.** A request records the match score as a snapshot at creation time.
The target mentor can accept or decline; the student can cancel while it is pending. Accepting is
refused with `409` once the mentor's `max_mentees` is reached. Duplicate pending or accepted
requests for the same mentor are `409`, while a declined request may be re-sent.

---

## Architecture

```
Browser (React/Vite :5173)
        │
        │  HTTP + JWT
        ▼
FastAPI Backend (:8000)
        │
        ├── Pydantic validation        (schemas/)
        ├── Services — business logic  (services/)
        │     ├── skill_gap_service    Phase 4 readiness (deterministic)
        │     ├── graph_service        Phase 5 dependency graph
        │     ├── roadmap_service      Phase 5 roadmap planning
        │     ├── assessment_service   Phase 8 grading & evidenced skills
        │     ├── matching_service     Phase 8 mentor ranking (deterministic)
        │     ├── mentorship_service   Phase 8 request lifecycle & rules
        │     └── github_service       Phase 6 GitHub API, evidence & LinkedIn
        ├── JWT auth + bcrypt          (utils/)
        │
        ├──▶ SQLite (dev) / PostgreSQL (prod)
        └──▶ Curated in-repo data (app/data/)  ·  optional Neo4j
```

---

## Project Structure

```
careergraph-ai/
├── frontend/
│   └── src/
│       ├── components/     Navbar, shared UI
│       ├── pages/          Landing, Login, Register, Dashboard, Profile,
│       │                   Resume, CareerGap (Phase 4), Roadmap (Phase 5),
│       │                   Verification (Phase 6), Assessments & Mentors (Phase 8)
│       ├── services/       api.js — single HTTP layer
│       └── setupTests.js   Vitest + Testing Library setup
├── backend/
│   ├── alembic/            Migration environment + revisions
│   └── app/
│       ├── config.py       All settings from .env
│       ├── data/           Curated taxonomy, occupations, prerequisites, assessments
│       ├── database/       SQLAlchemy engine & session
│       ├── models/         DB models (user, profile, resume, roadmap,
│       │                   assessment, mentorship, github_verification)
│       ├── schemas/        Pydantic request/response models
│       ├── routes/         API endpoints
│       ├── services/       Business logic
│       └── utils/          JWT, password hashing
├── docker-compose.yml      PostgreSQL + Neo4j
└── .env.example            Config template
```

---

## Testing

### Backend

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q
```

**306 tests pass** (Phases 1–6 and 8), including:

| File | Focus |
|------|-------|
| `test_phase2_profiles.py` | Profiles, completion score, mentor listing |
| `test_phase3_resume.py` / `test_phase3_extended.py` | Resume parsing, extraction, confirmation |
| `test_swagger_auth.py` | Swagger bearer-token auth flow |
| `test_security_regressions.py` | Malformed/expired tokens → 401 (never 500), role enforcement |
| `test_phase4_skill_gap.py` | Taxonomy integrity, scoring exactness, API behaviour |
| `test_phase5_graph.py` | Duplicate/self-loop rejection, bounded traversal, ordering, cycles, Neo4j→memory fallback |
| `test_phase5_roadmap.py` | Roadmap ordering, persistence, progress, ownership isolation |
| `test_phase6_github.py` | Deterministic repository analysis, fork exclusion, transport error mapping, account-claim isolation, evidence-only confirmation, LinkedIn unverified semantics |
| `test_phase8_assessments.py` | Bank integrity, exact grading, answer-leak prevention, evidence confirmation rules |
| `test_phase8_matching.py` | Score == Σ factors, word-boundary expertise matching, ranking, request authorization & capacity |
| `test_journey_e2e.py` | The full 13-step Phase 1–5 journey **and** the Phase 8 assess → evidence → mentor → accept journey |

The full verification sequence used before committing was:

```bash
python -m pytest -q                     # 306 passed
python -m alembic upgrade head          # 0001 → 0002 → 0003 → 0004
python -m alembic check                 # "No new upgrade operations detected."
python -m alembic downgrade base        # clean rollback
python -m alembic upgrade head          # re-applies cleanly
```

### Frontend

```bash
cd frontend
npm run test        # vitest run
npm run lint        # oxlint
npm run build       # production build
```

**38 frontend tests pass**, covering the API error-normalisation layer and the UI for Phases 4, 5,
6 and 8 (readiness rendering, ordered roadmap steps, prerequisite relationships, progress updates,
partial-roadmap warnings, GitHub verification and evidence confirmation, LinkedIn unverified
labelling, assessment catalogue/runner/grading/confirmation, and mentor ranking, requesting,
accepting and declining).

---

## Viva Answers

**Why FastAPI?**
Python-native, fast, auto-generates API docs, and pairs naturally with the data/AI work in later phases.

**Why SQLAlchemy?**
One ORM works with both SQLite (dev) and PostgreSQL (prod) — switching databases is a config change.

**Why JWT?**
Stateless authentication — the server doesn't need a session store; the token carries identity.
Malformed or expired tokens are rejected with `401`, never `500`.

**Why bcrypt?**
Slow by design — makes brute-force attacks expensive. Plaintext passwords are never stored.

**Why separate the service layer?**
Routes handle HTTP, services handle business logic, `app/data/` holds curated reference data.
This keeps the deterministic scoring logic independently testable from the API surface.

**Why is the readiness score deterministic instead of LLM-generated?**
So it is reproducible, auditable and unit-testable. An LLM may later *explain* a score (Phase 7),
but it must never *invent* it — and the score is explicitly not a probability of employment.

**Why an in-memory graph by default?**
It makes the graph behaviour fully deterministic and testable with zero infrastructure, while the
Neo4j adapter provides a production path. The adapter is present but flagged unverified until a
live instance is available.

**Why can a passed assessment only *suggest* skills instead of writing them?**
Grading is automatic but the profile is the student's own record. The server re-checks that each
requested skill was genuinely passed in that attempt, then the student decides what to add —
so evidence cannot be forged by a crafted request, and nothing is silently rewritten.

**Why is the mentor match score not a percentage of success?**
It is a weighted ordering heuristic over observable facts (skill overlap, shared college,
experience, availability, free slots). Calling it a probability of a good match would be
unfounded, so the API returns the itemised factors, the score always equals their sum, and a
disclaimer travels with it.

**Why is GitHub "verified" but LinkedIn only "self-declared"?**
GitHub publishes a public REST API, so the account and its repository metadata can be fetched and
cross-checked at request time. LinkedIn exposes no public API for reading a member's profile, so
the only honest option is to store the URL the student supplies and label it clearly. Claiming
otherwise would be a fake integration.

**Why infer skills from repository metadata instead of reading the code?**
Reading code would be slow, expensive and still subjective. Primary languages and topics are
observable, deterministic metadata. Every suggestion carries the repositories and stars that
back it plus a confidence score, and the student must confirm it — so the system never silently
asserts competence it cannot demonstrate.
