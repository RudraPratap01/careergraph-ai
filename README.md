# CareerGraph AI

> **Know your gap. Build your path. Meet your mentor.**

A career intelligence platform for BTech / final-year students. It analyses skills from
multiple sources, computes skill gaps against target occupations, generates
prerequisite-ordered learning roadmaps, verifies skills with short assessments, turns public
GitHub repositories into evidence-backed skill suggestions, ranks alumni mentors against the
gaps that remain, and answers career-learning questions with cited, curated sources.

---

## Current Status

This table describes **what is actually implemented and verified in this repository**,
not what is planned.

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Foundation — FastAPI, React, JWT auth, database, health checks |
| Phase 2 | ✅ Complete | User Profiles — student & alumni profiles, completion score, mentor directory |
| Phase 3 | ✅ Complete | Resume Intelligence — PDF/DOCX/TXT parsing, deterministic taxonomy matching with confidence & evidence, student review & confirmation that preserves existing profile skills |
| Phase 4 | ✅ Complete | Skill Gaps & Career Readiness — occupation catalog, deterministic readiness scoring |
| Phase 5 | ✅ Complete | Skill Graph & Learning Roadmap — dependency graph, prerequisite-ordered roadmaps, progress tracking |
| Phase 6 | ✅ Complete | GitHub + LinkedIn — live public GitHub verification with evidence-backed skill suggestions; LinkedIn stored as a self-declared (unverified) link |
| Phase 7 | ✅ Complete (local mode) | Grounded Career Advisor — curated knowledge corpus, local BM25 retrieval, citation-attributed answers, optional OpenRouter explanation with validation and deterministic fallback |
| Phase 8 | ✅ Complete | Skill Assessments & Alumni Matching — curated question bank, deterministic grading, evidenced skills, ranked mentors, mentorship requests |

A separate UI/UX and reliability refinement pass modernises the React client: a token-based
design system, responsive navigation, accessible forms and landmarks, reduced-motion support,
lazy-loaded routes, a real 404 page, and regression tests.

Phase 7 is integrated in the UI as the **Advisor** page and in the dashboard, skill-gap and
roadmap flows. The retrieval, grounding, deterministic context and local answer mode always work;
the external LLM explanation is optional and is only reported as used when a validated model
answer was actually returned.

### Scope boundaries and unverified integrations

* **Deterministic core** — readiness scoring, roadmap ordering, assessment grading and mentor
  ranking remain deterministic Python. The Phase 7 LLM is optional and may only *explain*
  retrieved evidence; it cannot change a score or roadmap order.
* **Live LLM provider** — no OpenRouter key is configured in this development environment, so a
  real provider call has **not** been verified here. The frontend/backend behaviour, request
  construction, response validation and failure fallback are covered with an injected deterministic
  client; without a key the API makes no external AI request.
* **RAG / web search** — Phase 7 is lexical BM25 retrieval over a small, curated in-repo corpus
  (94 documents / 102 chunks). It is **not** semantic/embedding search, web search, or a general
  knowledge base. No external course catalogue or URL index is used.
* **Neo4j** — the adapter and live integration tests are implemented. The ordinary suite uses
  the in-memory backend and an unreachable-server fallback. A disposable Neo4j 5.24 service is
  configured in the GitHub Actions `integration` job; local Docker/Neo4j was unavailable. The
  release CI result is the live-verification record.
* **Learning resources / course links** — roadmaps and advisor answers do *not* include course
  URLs. The advisor shows only retrieved, internal curated source cards, so no course links are
  invented.
* **GitHub** — verification uses the **public, unauthenticated** GitHub REST API only: no OAuth,
  no personal access token, no private repositories, and no repository code is downloaded.
  Unauthenticated calls are limited to 60 requests/hour per IP; when the limit is hit the API
  returns `503` with an explicit message. Up to 100 of the account's most recently pushed public
  repositories are analysed, and **forks are excluded** from all evidence.
* **LinkedIn is not verified.** LinkedIn exposes no public API for reading a member's profile, so
  a LinkedIn URL is stored as a *self-declared* link and always returned with `verified: false`.
  The UI labels it "Unverified — self-declared".
* **spaCy / sentence-transformers** — not used. Skill extraction is regex matching against a
  curated in-repo taxonomy (see below), and advisor retrieval is lexical BM25 rather than an
  embedding model.
* **Adaptive / AI-generated assessments** — the Phase 8 question bank is a small curated set
  authored in-repo (`backend/app/data/assessments.py`), not generated. Grading is exact
  answer matching; there is no NLP or semantic grading, and a pass is **not** a certification.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, React Router, Axios; custom CSS design system with Tailwind CSS v4 preflight |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | SQLite (local dev) / PostgreSQL (staging & production) |
| Migrations | Alembic |
| Graph | In-memory backend (default); optional Neo4j 5 adapter with live CI integration tests |
| Skill extraction | Regex matching + curated taxonomy (no ML models) |
| Advisor retrieval | Local lexical BM25 over a curated in-repo corpus (no embeddings/web search) |
| Advisor explanation | Optional OpenRouter chat model, backend-only key, citation/link validation, deterministic fallback |
| GitHub verification | Public GitHub REST API, unauthenticated (no OAuth/token) |
| Auth | JWT (HS256) + bcrypt |

---

## Quick Start

### Prerequisites
- Python 3.11+ (developed and verified against 3.14)
- Node.js 22+ (Vite 8; CI uses Node 22)
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

> **Local development caution:** a SQLite file created before Alembic was introduced may not
> have an `alembic_version` table. Back it up before attempting migrations, and never point a
> migration at a database containing data you have not backed up.

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

# Phase 7: retrieval is always local. The LLM explanation is optional.
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
LLM_TIMEOUT_SECONDS=20
LLM_MAX_TOKENS=600
LLM_TEMPERATURE=0.2
RAG_TOP_K=6
RAG_MIN_SCORE=1.0
```

With `OPENROUTER_API_KEY` empty (**the default**), the advisor returns a deterministic
source-attributed answer and reports `llm_configured=false`, `mode="grounded_extractive"`. With a
key configured, only the question, target occupation, canonical skill names, gap summary, roadmap
step names and retrieved excerpts are sent to OpenRouter. Resume files, resume text, email, names,
account IDs and tokens are never included. The API key stays on the backend and is never returned
by `/intelligence/status`.

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
| POST | `/resume/confirm-skills` | Confirm the reviewed skill list (accepts `source: resume|self`; never downgrades verified evidence) | Student |

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

### Grounded Career Intelligence (Phase 7)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/intelligence/ask` | Ask a career-learning question; returns the answer, mode, cited sources, deterministic context, privacy note and limitations | Student/Admin |
| GET | `/intelligence/status` | Retrieval, LLM-configuration and corpus status; never returns the API key | Yes |

`occupation` is optional and defaults to the student's saved target role. An explicitly requested
unknown occupation is rejected with `404`; a stale unknown role saved on the profile is treated as
“no target role” so a general question can still be answered. The route never accepts a user ID,
resume payload or arbitrary prompt context, so it cannot read another account's profile.

---

## How Resume Review Works (Phase 3)

Resume text extraction runs entirely in the student's CareerGraph backend. Skills are matched
against the curated in-repo taxonomy with an evidence snippet and a deterministic confidence
score; no external AI/NLP service receives the file.

**Review and data preservation.** The review pane starts with the extracted matches and also
carries forward existing profile skills that are not already evidenced by a passed assessment or
GitHub. Those skills are labelled **Kept from profile** so they are visible rather than silently
deleted.

* Confirming sends the complete reviewed list. Removing an item from the pane removes it from the
  saved profile; existing skills are included by default so a resume review cannot erase them
  unnoticed.
* Each saved item records `source="resume"` for a resume match or `source="self"` for a skill
  kept from the profile. The request schema rejects `assessment` and `github` values, so a resume
  confirmation cannot inflate evidence.
* Assessment- and GitHub-evidenced skills are always preserved separately. A resume review never
  downgrades their source.

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

## How the Grounded Career Advisor Works (Phase 7)

**No score is generated by an LLM.** The advisor receives the already-computed deterministic
readiness context and planned roadmap steps, retrieves supporting curated excerpts, and explains
them. Readiness and roadmap order remain authoritative and unchanged.

**Corpus and retrieval.**

* The corpus lives in `backend/app/data/career_knowledge.py`: **94 curated documents / 102
  chunks** covering readiness, learning strategy, prerequisite order, portfolio evidence,
  assessments, GitHub/resume evidence, mentorship preparation and the curated occupations/skills.
* Retrieval is local **BM25 lexical search** (`k1=1.5`, `b=0.75`, default top-k 6) with a small
  curated query-expansion map and taxonomy aliases. It is not an embedding model, semantic
  search, web search, or a general-purpose knowledge base.
* The **question alone** is the retrieval query. Profile context is added separately to the
  prompt so an off-topic question does not become “relevant” merely because the student has a
  target role.
* If the best score is below the configured threshold, the response contains no citations and
  says the curated corpus does not support the question; it does not invent an answer.

**Optional LLM explanation.** When `OPENROUTER_API_KEY` is non-empty and retrieval found
supporting sources, the backend sends a prompt containing only:

* the question,
* the target occupation and canonical skill names,
* the deterministic gap summary and roadmap step names,
* the retrieved curated excerpts with `[S1]`-style IDs.

Resume files/text, email, names, account IDs, tokens and raw profile records are **not** included.
The key is backend-only. The model is instructed not to invent courses, URLs, employers, salaries,
credentials, statistics or personal facts.

**Validation before an LLM answer is accepted.** The response must contain at least one valid
`[S#]` citation, may only cite IDs in the retrieved set, must not contain an external URL, and
must be 20–3000 characters. If it fails validation, the provider errors, times out, rate-limits,
or no key is configured, the API returns the deterministic extractive answer and records the
honest mode/notice. `llm_used` is exactly `mode == "llm"`; it is never set optimistically.

**Source cards, not course links.** Every accepted answer carries retrieved source metadata
(title, internal source label, kind, score and excerpt). No external course URL is generated or
returned. A citation is traceable to the displayed source card, but the system does not claim to
have verified the source as an official certification or syllabus.

**Limitations.** Citation checking reduces obvious fabrication but is not a truth oracle. The
corpus is small, lexical retrieval misses paraphrases, and a model can still make an unsupported
statement while citing a real source — which is why the excerpts and limitations remain visible.
A live OpenRouter call has not been verified without a configured key. There is no per-user LLM
spend quota in the application; deploy behind a gateway with rate limiting if an external model
is enabled.

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
Phase 3 resume review preserves assessment- and GitHub-evidenced skills and carries existing
self-reported skills into the review rather than silently deleting them.

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
        │     ├── github_service       Phase 6 GitHub API, evidence & LinkedIn
        │     └── career_intelligence_service  Phase 7 BM25 retrieval & optional LLM
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
│       ├── components/     Navbar, Icon, Logo, PageHeader, EmptyState,
│       │                   DashboardCard, HeroGraph, PasswordInput, AuthAside,
│       │                   dashboard/DashboardCards
│       ├── content/        landing.js — data-driven landing copy
│       ├── context/        AuthContext.js, AuthProvider.jsx
│       ├── hooks/          useAuth.js
│       ├── pages/          Landing, Login, Register, Dashboard, Profile,
│       │                   Resume, CareerGap (Phase 4), Roadmap (Phase 5),
│       │                   Verification (Phase 6), Assessments & Mentors (Phase 8),
│       │                   Advisor (Phase 7), NotFound
│       ├── services/       api.js — single HTTP layer
│       ├── index.css       design tokens, layout, components, responsive rules
│       └── setupTests.js   Vitest + Testing Library setup
├── backend/
│   ├── alembic/            Migration environment + revisions
│   └── app/
│       ├── config.py       All settings from .env
│       ├── data/           Curated taxonomy, occupations, prerequisites, assessments,
│       │                   and Phase 7 career-knowledge corpus
│       ├── database/       SQLAlchemy engine & session
│       ├── models/         DB models (user, profile, resume, roadmap,
│       │                   assessment, mentorship, github_verification)
│       ├── schemas/        Pydantic request/response models
│       ├── routes/         API endpoints
│       ├── services/       Business logic
│       └── utils/          JWT, password hashing
├── .github/workflows/ci.yml  Backend, frontend and live-service integration jobs
├── docker-compose.yml      PostgreSQL + Neo4j
└── .env.example            Config template
```

---

## Frontend, Design System & Accessibility

The client is a Vite/React SPA with role-aware routes and a custom design system defined in
`frontend/src/index.css`. Existing class names (`card`, `btn`, `badge`, `page-container`, …) are
preserved while the token layer is expanded.

* **Design tokens** — colour, surfaces, typography, spacing, radii, elevation and motion are
  centralised as CSS custom properties. Shared primitives include buttons, forms, badges, alerts,
  progress bars, empty/loading states and the navigation shell.
* **Reusable components** — `Navbar`, `Icon`, `Logo`, `PageHeader`, `EmptyState`, `DashboardCard`,
  `PasswordInput`, `AuthAside`, dashboard cards and data-driven landing content. Visuals are
  CSS/SVG, not remote stock imagery.
* **Responsive behaviour** — primary navigation collapses at 1080px; the auth aside hides below
  980px; grids use auto-fit tracks; representative authenticated pages are tested at 390, 768,
  1024 and 1440px with no horizontal overflow.
* **Advisor states** — the Phase 7 page has explicit loading, error, empty, retrieved-source and
  success states. It distinguishes local grounded mode from a validated LLM explanation, shows the
  deterministic readiness context separately, and never presents a source card as a course link.
* **Accessibility** — skip link as the first focus target, a `<main id="main-content">` landmark,
  exactly one `h1` per page, labelled form controls, named icon buttons, `aria-current`,
  `aria-expanded`/`aria-controls`, `aria-pressed` filters, progressbar metadata, visible focus
  rings, Escape-to-close with focus return on the mobile menu, `aria-live` status for advisor
  loading, and a `prefers-reduced-motion` fallback.
* **Routing and performance** — every page, including the advisor, is lazy-loaded behind
  Suspense, guarded by role-aware routes, with a catch-all 404 page.
* **Honest UI copy** — the resume flow says deterministic taxonomy matching rather than AI/NLP;
  LinkedIn is always labelled “Unverified — self-declared”; readiness and mentor scores are
  described as deterministic metrics/heuristics, never hiring probabilities; partial roadmaps,
  advisor local-vs-LLM mode, and optional graph-backend state are labelled accurately.

---

## Testing

### Backend

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q
```

**334 tests pass, 7 skipped** in the full local suite (Phases 1–8). The 7 skips are the opt-in
live PostgreSQL (2) and Neo4j (5) tests; they skip cleanly when no test services are configured.
The suite was also run successfully from a clean Python 3.14 virtualenv after installing the pinned
`requirements.txt`, verifying the CI-compatible versions rather than only the pre-existing local
environment.

| File | Focus |
|------|-------|
| `test_phase2_profiles.py` | Profiles, completion score, mentor listing |
| `test_phase3_resume.py` / `test_phase3_extended.py` | Resume parsing, taxonomy extraction, confirmation semantics, source preservation, verified-evidence protection |
| `test_swagger_auth.py` | Swagger bearer-token auth flow |
| `test_security_regressions.py` | Malformed/expired tokens → 401 (never 500), role enforcement |
| `test_phase4_skill_gap.py` | Taxonomy integrity, scoring exactness, API behaviour |
| `test_phase5_graph.py` | Duplicate/self-loop rejection, bounded traversal, ordering, cycles, Neo4j→memory fallback |
| `test_phase5_roadmap.py` | Roadmap ordering, persistence, progress, ownership isolation |
| `test_phase6_github.py` | Deterministic repository analysis, fork exclusion, transport error mapping, account-claim isolation, evidence-only confirmation, LinkedIn unverified semantics |
| `test_phase7_career_intelligence.py` | Corpus integrity, BM25 retrieval/ranking, source attribution, citation/link validation, LLM fallback, prompt privacy, auth/role scoping, unknown occupation |
| `test_phase8_assessments.py` | Bank integrity, exact grading, answer-leak prevention, evidence confirmation rules |
| `test_phase8_matching.py` | Score == Σ factors, word-boundary expertise matching, ranking, request authorization & capacity |
| `test_journey_e2e.py` | The full 13-step Phase 1–5 journey **and** the Phase 8 assess → evidence → mentor → accept journey |
| `test_postgres_integration.py` | Opt-in live PostgreSQL schema and user/profile round-trip |
| `test_neo4j_integration.py` | Opt-in live Neo4j seeding, idempotency, traversal, roadmap ordering and driver lifecycle |

The Phase 7 tests use an injected deterministic LLM client for request/validation/fallback tests;
they do **not** claim a live OpenRouter call. No database model or Alembic revision changed in this
pass. The local development SQLite file predates Alembic and has no `alembic_version` table, so it
was left untouched; back it up before migrating.

### Frontend

```bash
cd frontend
npm run test        # vitest run
npm run lint        # oxlint
npm run build       # production build
```

**60 frontend tests pass across 10 Vitest files**, covering:

* API error-normalisation and auth pages.
* Navbar rendering, role-based links and mobile-menu behaviour.
* Resume review: confidence/evidence rendering, carrying existing profile skills into the review,
  preserving `self` provenance in the confirmation payload, and disabling sync if the existing
  profile could not be loaded.
* Readiness rendering and the career-gap occupation selector.
* Ordered roadmap steps, prerequisite relationships, progress updates and partial-roadmap warnings.
* GitHub verification, evidence confirmation and LinkedIn unverified labelling.
* Assessment catalogue, runner, grading and confirmation.
* Mentor ranking, request submission (including the immediate pending row), acceptance and decline.
* Advisor loading/success/error/empty states, deterministic context, source cards, local-vs-LLM
  labelling, validation feedback and the no-target general-question path.

### Real-browser QA

Temporary Playwright Core harnesses drove real **Google Chrome** against a throwaway SQLite
database and the Vite dev server. They are verification tools, not repository dependencies:

* **Existing student + alumni journey: 115/115 checks passed** — 0 JavaScript console errors,
  0 `5xx` responses and 0 unexpected `401` responses. Covered registration/login, profile save,
  resume upload/review/confirmation (including existing skill preservation), gap analysis with
  selector sync, roadmap generation and progress persistence, assessment submission, LinkedIn
  save, live GitHub verification (`octocat`), mentorship request → accept, dashboard, 404, mobile
  navigation, 390px overflow, and skip-link focus.
* **Phase 7 advisor: 38/38 checks passed** at 1440px and 390px — deterministic context, local
  grounded mode (no LLM key), source IDs, no fabricated external links, expandable privacy
  disclosure, a second grounded question, labelled controls, exactly one `h1`, no horizontal
  overflow, no unexpected `4xx`/`5xx`, and no JavaScript errors. It also checks the dashboard card
  and desktop/mobile navigation links.
* **Responsive audit: 68/68 checks passed** across dashboard, profile, career gap, roadmap, advisor,
  assessments, mentors and verification at 390, 768, 1024 and 1440px — exactly one `h1` per page,
  no horizontal overflow, and the 1080px navigation breakpoint behaves as expected.
* **Automated accessibility: 16 page states scanned with axe-core** using the WCAG 2 A/AA rule set,
  including the advisor answer at desktop and mobile: **0 violations**. This is automated coverage,
  not a formal WCAG certification or a screen-reader session.
* Where a page intentionally probes an empty-state endpoint, the resulting `404`/`400` response is
  recorded separately from script errors. The existing journey run recorded six such expected
  responses (`/resume/latest` `404`, `/career/gap-analysis` `400`, `/roadmap` `404`).
* Screenshots and the JSON reports live under `%TEMP%\opencode\cg_uiqa\` and are **not** committed.
* This is **Chrome-only** manual/automated QA. No Firefox/Safari run, Lighthouse audit, screen-reader
  session or WCAG conformance certification is claimed.

Live PostgreSQL and Neo4j checks are opt-in and are configured to run in the GitHub Actions
`integration` job using disposable service containers. Local Docker was unavailable, so the release
CI result will be the live-service verification record. The ordinary suite does not pretend to have
exercised them.

---

## Verification and Release Checklist

The following sequence was run for this release candidate:

```bash
# Backend (clean Python 3.14 venv with pinned requirements)
cd backend
python -m pytest -q                  # 334 passed, 7 skipped
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# GET /health -> 200, database connected; GET /docs -> 200

# Frontend
cd frontend
npm run lint                         # clean
npm run test -- --run                # 60 passed across 10 files
npm run build                        # production build succeeded
```

A live HTTP smoke test against a throwaway SQLite database created a student, saved a target role
and two skills, loaded `/intelligence/status` (`94` documents / `102` chunks,
`llm_configured=false`), and called `/intelligence/ask`. The result was HTTP `200`,
`mode="grounded_extractive"`, `llm_used=false`, six cited sources, and deterministic context
(`25%`, `Emerging`, `2/10` required skills). The answer included the `25%` score and cited
`S1`–`S6`; no external AI request was made.

**Release steps:**

1. Back up any production/staging database and confirm `alembic current`.
2. Set a strong `SECRET_KEY`, the real `DATABASE_URL`, CORS origins, and (optionally)
   `OPENROUTER_API_KEY` in the server environment. Never commit `.env`.
3. Run `alembic upgrade head` and `alembic check` in the target environment before serving.
4. Build the frontend (`npm ci && npm run build`) and serve `dist/` with the API URL configured
   by the deployment proxy.
5. Run the backend suite, frontend suite, lint and build. Re-run the Chrome journey, axe-core and
   responsive audits if UI changes after this release. In GitHub Actions, confirm all three jobs
   (`Backend`, `Frontend`, `Live PostgreSQL + Neo4j integration`) are green.
6. Keep the advisor key backend-only. If it is enabled, put rate limiting/spend controls at the
   API gateway; the application does not implement a per-user LLM quota.
7. Do not claim live Neo4j/PostgreSQL, live OpenRouter, Firefox/Safari, Lighthouse or WCAG results
   unless the corresponding run was actually performed and recorded.

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
So it is reproducible, auditable and unit-testable. In Phase 7 an LLM may *explain* a score using
retrieved citations, but it cannot *invent* or change it — and the score is explicitly not a
probability of employment.

**Why use lexical BM25 instead of embeddings?**
The Phase 7 corpus is small and curated; BM25 is deterministic, fast and requires no model
download or vector database. The trade-off is that paraphrases and synonyms outside the curated
query-expansion map are missed, so unsupported questions are refused rather than answered by
guesswork. Embedding retrieval is a possible later upgrade, not a current claim.

**Why is the advisor's LLM optional?**
The feature must still work and remain auditable without a paid external key. The local
grounded-extractive mode uses the same retrieval and deterministic context, and reports
`llm_configured=false`. When a model is configured, its output must pass citation and URL
validation or the system falls back; the mode and any fallback notice are returned honestly.

**Why an in-memory graph by default?**
It makes graph behaviour fully deterministic and testable with zero infrastructure, while the
Neo4j adapter provides a production path. The adapter is now exercised by an opt-in live Neo4j
integration test in CI; the ordinary suite still uses the in-memory backend and fallback guard.

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
