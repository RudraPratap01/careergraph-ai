<div align="center">
  <img src="docs/assets/readme-banner.svg" alt="CareerGraph AI - Know your gap. Build your path. Meet your mentor." width="100%">
  <h1>CareerGraph AI</h1>
  <p><strong>Know your gap. Build your path. Meet your mentor.</strong></p>
  <p>A full-stack career intelligence platform for students who want an explainable next step, not another generic career quiz.</p>
  <p>
    <a href="https://github.com/RudraPratap01/careergraph-ai/actions/workflows/ci.yml"><img src="https://github.com/RudraPratap01/careergraph-ai/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI status"></a>
    <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111827" alt="React 19">
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  </p>
  <p>
    <a href="#quick-start">Quick start</a> ·
    <a href="docs/ARCHITECTURE.md">Architecture</a> ·
    <a href="docs/API.md">API</a> ·
    <a href="docs/TESTING.md">Testing</a> ·
    <a href="docs/DEPLOYMENT.md">Deployment</a>
  </p>
</div>

---

## What this project solves

Students often know the role they want but not **which skill to work on next**, **whether their
evidence is credible**, or **who can help them close the remaining gap**. CareerGraph AI connects
those questions into one workflow:

- turn a profile and resume into an evidence-aware skill inventory;
- compare it with a curated target occupation using a deterministic readiness metric;
- order missing skills by prerequisites rather than by guesswork;
- let the student verify skills with assessments and public GitHub evidence;
- match remaining gaps with alumni mentors;
- explain learning decisions with cited, curated sources.

The deterministic career logic remains authoritative. The optional language model can explain
retrieved evidence, but it cannot change stored skills, a readiness score or a roadmap order. Its
answer is validated for citations and links, not for factual truth.

**Project status:** functional local-development release; backend, frontend and live PostgreSQL +
Neo4j integration checks are wired in CI. There is no hosted demo or production deployment in this
repository. See the [honest limitations](#limitations-and-security).

## Screenshots

These are real screenshots of the running application, captured with a disposable SQLite database
and synthetic demo records. No real user data, cookies or credentials are shown.

<p align="center">
  <a href="docs/assets/screenshots/dashboard.png"><img src="docs/assets/screenshots/dashboard.png" alt="CareerGraph AI dashboard with profile, target career, readiness and learning roadmap cards" width="100%"></a>
</p>

<table>
  <tr>
    <td width="50%"><a href="docs/assets/screenshots/resume.png"><img src="docs/assets/screenshots/resume.png" alt="Resume analysis with extracted skills awaiting review" width="100%"></a></td>
    <td width="50%"><a href="docs/assets/screenshots/career-gap.png"><img src="docs/assets/screenshots/career-gap.png" alt="Career gap analysis showing deterministic readiness and missing skills" width="100%"></a></td>
  </tr>
  <tr>
    <td width="50%"><a href="docs/assets/screenshots/roadmap.png"><img src="docs/assets/screenshots/roadmap.png" alt="Prerequisite-ordered learning roadmap with progress" width="100%"></a></td>
    <td width="50%"><a href="docs/assets/screenshots/advisor.png"><img src="docs/assets/screenshots/advisor.png" alt="Grounded advisor answer with visible source citations" width="100%"></a></td>
  </tr>
</table>

<p align="center">
  <a href="docs/assets/screenshots/advisor-mobile.png"><img src="docs/assets/screenshots/advisor-mobile.png" alt="CareerGraph AI advisor on a mobile-width viewport" width="300"></a>
  <br>
  <em>Responsive advisor layout at 390px.</em>
</p>

Screenshot provenance and the synthetic-data note are documented in
[`docs/assets/README.md`](docs/assets/README.md).

## Feature overview

| Capability | Status | What is implemented |
| --- | --- | --- |
| Authentication and roles | Implemented | JWT login, bcrypt passwords, student/alumni/admin roles, protected routes |
| Student and alumni profiles | Implemented | Education, target role, skills, expertise, availability, completion score |
| Resume intelligence | Implemented | PDF/DOCX/TXT extraction, curated taxonomy matching, confidence and evidence, student-controlled review |
| Skill-gap analysis | Implemented | Occupations with weighted required/optional skills and per-skill contributions |
| Career readiness | Implemented | Deterministic weighted coverage, band, explanation and disclaimers |
| Skill graph | Implemented | Curated prerequisites, bounded traversal, cycle checks, in-memory and optional Neo4j adapters |
| Learning roadmap | Implemented | Prerequisite-ordered steps, persisted progress, refresh and partial-roadmap warnings |
| Assessments | Implemented | Curated question bank, exact grading, per-skill review, evidence-only confirmation |
| GitHub evidence | Implemented | Public unauthenticated GitHub REST API, fork exclusion, deterministic detected-skill suggestions |
| LinkedIn | Self-declared only | URL is stored and never shown as verified |
| Alumni matching and mentorship | Implemented | Itemized deterministic ranking, requests, capacity-enforced acceptance |
| Grounded Career Advisor | Implemented | Local BM25 retrieval, cited sources, deterministic extractive answer and explicit refusal when unsupported |
| Optional LLM explanations | Optional | OpenRouter path with citation/link validation and fallback; no live provider key was available during release verification |
| PostgreSQL and Neo4j | Verified in CI | Live disposable service-container checks pass in GitHub Actions; local Docker Compose was not executed |
| Hosted demo | Not included | No production URL, uptime claim or deployment is represented by this repository |

### What the advisor will not do

- It will not calculate or change readiness.
- It will not change stored profile skills or reorder a roadmap.
- It will not send stored resume text, profile names/emails, account IDs or tokens to a provider.
  The typed question itself is sent, so do not enter sensitive personal data in it.
- It rejects external links and requires valid citations, but citation validation is not a truth
  guarantee.
- If retrieval finds no supporting evidence, it will refuse to answer from unsupported sources.

## How it works

```text
Profile + resume evidence
        -> curated skill normalization
        -> weighted readiness against a target occupation
        -> missing skills + prerequisite graph
        -> deterministic learning roadmap
        -> assessments / GitHub evidence / mentor matching
        -> question + deterministic context + retrieved excerpts
        -> local BM25 answer or optional validated LLM explanation
```

The readiness metric is:

```text
readiness = round(100 * sum(importance weights of matched required skills)
                       / sum(importance weights of all required skills))
```

Presence counts; the self-reported level is shown but does not change the score. Optional skills
are informational and unknown skills neither help nor hurt. Readiness is **not** a probability of
employment, and the API returns that disclaimer with the result.

## Architecture

<p align="center">
  <img src="docs/assets/architecture.svg" alt="CareerGraph AI architecture: React frontend, FastAPI API, deterministic services, PostgreSQL/SQLite, optional Neo4j, curated corpus, and the grounded advisor with optional OpenRouter and citation validation" width="100%">
</p>

- **React 19 + Vite SPA** provides authenticated route guards, dashboard, resume review, gap
  analysis, roadmaps, assessments, verification, mentors and the advisor.
- **FastAPI** owns HTTP validation, JWT authentication and ownership/role boundaries.
- **Deterministic services** implement extraction, scoring, graph traversal, grading, ranking and
  roadmap ordering.
- **PostgreSQL or SQLite** stores application records; Alembic owns the schema history.
- **The skill graph** uses an in-memory backend by default and an optional Neo4j 5 adapter with the
  same algorithms. An unreachable Neo4j configuration falls back to memory.
- **The advisor** retrieves local curated excerpts with BM25. The optional OpenRouter explanation is
  accepted only after citation and link validation; otherwise the deterministic answer is returned.
- **GitHub Actions** runs backend, frontend and live-service integration checks.

The detailed component boundaries, request flows and fallback behavior are in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The editable diagram is
[`docs/assets/architecture.svg`](docs/assets/architecture.svg).

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, Vite 8, React Router 7, Axios, Tailwind CSS v4 with a custom CSS design system |
| Frontend quality | Vitest, Testing Library, jsdom, oxlint |
| Backend | Python 3.11+ (release verified on 3.14), FastAPI 0.115, Pydantic v2, SQLAlchemy 2 |
| Database | SQLite for local development; PostgreSQL 16 for shared deployments |
| Migrations | Alembic |
| Graph | In-memory backend by default; optional Neo4j 5.24 adapter |
| Authentication | JWT (HS256) and bcrypt |
| Retrieval | Local lexical BM25 over a curated in-repo corpus |
| Optional explanation | OpenRouter-compatible chat provider, backend-only key, validation and fallback |
| GitHub evidence | Public unauthenticated GitHub REST API |
| CI | GitHub Actions; Python 3.14, Node 22, PostgreSQL and Neo4j service containers |

Versions come from `backend/requirements.txt` and `frontend/package.json`. Tailwind CSS is
integrated alongside a substantial custom CSS design system; the UI styles live in
`frontend/src/index.css`.

## Quick start

### Prerequisites

- Python 3.11+ (the release uses 3.14)
- Node.js 22+ and npm
- Git
- Optional: Docker only for local PostgreSQL/Neo4j containers

The default setup needs no Docker: SQLite and the in-memory graph work out of the box.

### 1. Clone and install the backend

#### Windows PowerShell

```powershell
git clone https://github.com/RudraPratap01/careergraph-ai.git
cd careergraph-ai

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

Copy-Item .env.example backend\.env
# Edit backend\.env: set a real SECRET_KEY before sharing the app.
```

#### macOS / Linux

```bash
git clone https://github.com/RudraPratap01/careergraph-ai.git
cd careergraph-ai

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

cp .env.example backend/.env
# Edit backend/.env: set a real SECRET_KEY before sharing the app.
```

### 2. Apply migrations and start the API

```bash
cd backend
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The default `.env.example` uses SQLite at `backend/careergraph_dev.db` and the in-memory skill graph.
The API is at <http://localhost:8000>, docs at <http://localhost:8000/docs> and health at
<http://localhost:8000/health>.

> If you already have a SQLite file created before Alembic was introduced, back it up first. It
> may not have an `alembic_version` table; do not reset or stamp it blindly.

### 3. Start the frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to the backend at port 8000. There is no seed
script; create a student or alumni account through the UI.

### Optional PostgreSQL and Neo4j

The repository includes a development `docker-compose.yml`. It was not executed in the release
environment (Docker was unavailable); the live-service verification path is the CI integration job.
If you use it:

```bash
docker compose up -d
```

Then set a PostgreSQL URL in `backend/.env` and apply migrations:

```ini
DATABASE_URL=postgresql+psycopg2://careergraph:careergraph_pass@localhost:5432/careergraph_db
```

```bash
cd backend
python -m alembic upgrade head
python -m alembic check
```

Set `GRAPH_BACKEND=neo4j` and the `NEO4J_*` variables to use the graph adapter. Treat the Compose
passwords as development-only. See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for full setup details.

## Configuration reference

Copy `.env.example` to `backend/.env`. Never commit a real `.env`. The frontend has no secret
configuration.

| Variable | Required? | Purpose | Safe example |
| --- | --- | --- | --- |
| `APP_NAME` | Optional | API metadata name | `CareerGraph AI` |
| `APP_VERSION` | Optional | Version string | `0.1.0` |
| `DEBUG` | Optional | Debug mode; use `False` outside local development | `True` |
| `ENVIRONMENT` | Optional | Environment label | `development` |
| `DATABASE_URL` | Required for the target environment | SQLAlchemy database URL | `sqlite:///./careergraph_dev.db` |
| `SECRET_KEY` | **Required** | JWT signing secret; generate per environment | `<random 64+ character hex value>` |
| `ALGORITHM` | Optional | JWT algorithm; keep `HS256` unless justified | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Token lifetime in minutes | `1440` |
| `CORS_ORIGINS` | Required for browser deployments | JSON array of allowed origins | `["https://app.example.com"]` |
| `GRAPH_BACKEND` | Optional | `memory` or `neo4j` | `memory` |
| `NEO4J_URI` | If using Neo4j | Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` | If using Neo4j | Username | `neo4j` |
| `NEO4J_PASSWORD` | If using Neo4j | Password; keep it out of Git | `<test-only-password>` |
| `OPENROUTER_API_KEY` | Optional | Enables validated LLM explanations | `<provider key>` |
| `OPENROUTER_BASE_URL` | Optional | Provider-compatible base URL | `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | Optional | Model identifier | `openai/gpt-4o-mini` |
| `LLM_TIMEOUT_SECONDS` | Optional | Provider timeout | `20` |
| `LLM_MAX_TOKENS` | Optional | Maximum generated tokens | `600` |
| `LLM_TEMPERATURE` | Optional | Sampling temperature | `0.2` |
| `RAG_TOP_K` | Optional | Maximum retrieved chunks | `6` |
| `RAG_MIN_SCORE` | Optional | Minimum retrieval score | `1.0` |

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Security and deployment details are in [`docs/SECURITY.md`](docs/SECURITY.md) and
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Testing and quality

### Local commands

```bash
# Backend
cd backend
python -m pytest -q
python -m pip check

# Frontend
cd ../frontend
npm run lint
npm run test
npm run build
```

### Verified results

The last application-code verification (2026-10-27) recorded:

- **334 backend tests passed, 7 skipped.** The skips are the opt-in live PostgreSQL and Neo4j
  tests; those passed in the GitHub Actions integration job against disposable service containers.
- **60 frontend tests passed across 10 Vitest files**, lint clean and production build successful.
- `pip check` reported no broken requirements and `npm audit --audit-level=high` reported
  0 vulnerabilities at the time of the run.
- Live PostgreSQL 16 migration/round-trip tests and Neo4j 5.24 adapter tests passed in the
  `integration` job.

A Chrome-only release QA pass also recorded 115/115 student/alumni checks, 38/38 advisor checks,
68/68 responsive checks and 0 axe-core WCAG A/AA violations across 16 page states. This is not
Firefox/Safari coverage, a Lighthouse result, a screen-reader session or formal WCAG certification.

The documentation-only revision is verified by the same CI workflow. Inspect the latest run at
[Actions](https://github.com/RudraPratap01/careergraph-ai/actions/workflows/ci.yml). The complete
matrix, opt-in integration setup and known gaps are in [`docs/TESTING.md`](docs/TESTING.md).

## Project structure

```text
careergraph-ai/
├── backend/
│   ├── alembic/                 # Revisions and migration environment
│   ├── app/
│   │   ├── data/                # Curated taxonomy, occupations, prerequisites, corpus
│   │   ├── database/            # SQLAlchemy engine and sessions
│   │   ├── models/              # ORM models
│   │   ├── routes/              # FastAPI endpoints
│   │   ├── schemas/             # Pydantic contracts
│   │   ├── services/            # Deterministic career logic and advisor
│   │   └── utils/               # JWT/password helpers
│   └── tests/                   # Pytest suite and opt-in live checks
├── frontend/
│   └── src/
│       ├── components/          # Shared UI and dashboard cards
│       ├── context/ hooks/      # Auth state and hooks
│       ├── pages/               # Route screens
│       └── services/api.js      # Single HTTP layer
├── docs/                        # Architecture, API, testing, security, deployment, assets
├── .github/workflows/ci.yml
├── .env.example
├── docker-compose.yml
└── CONTRIBUTING.md
```

## Limitations and security

- **No hosted demo.** This repository does not claim a live URL, uptime or production deployment.
- **Optional paid LLM.** OpenRouter is disabled by default. A live provider call has not been
  verified without a key. If enabled, add gateway rate limiting, spend caps and monitoring; the
  application has no per-user LLM quota.
- **Lexical retrieval, not semantic search.** The advisor uses a small curated corpus and BM25. It
  is not web search, embedding search or a general-purpose knowledge base. Paraphrases outside the
  query-expansion map may be refused.
- **Citation checks are not a truth oracle.** They reduce obvious fabrication; the displayed
  excerpts and limitations remain visible.
- **Evidence is suggested, not silently trusted.** Resume extraction, assessments and GitHub
  detection require review and confirmation. Assessments are not certifications. LinkedIn is
  self-declared and always unverified.
- **Live service coverage.** PostgreSQL and Neo4j are verified via CI service containers. Local
  Docker Compose was not executed in the release environment.
- **Browser coverage.** QA was Chrome-only. Firefox, Safari, iOS, Lighthouse and screen-reader
  testing are not claimed.
- **Authentication limitations.** JWT is stored in `localStorage`; there is no MFA, password reset,
  refresh-token rotation or per-user LLM quota. The registration API accepts a client-supplied role,
  including `admin` (the web UI shows only student/alumni); restrict role assignment and add
  authentication throttling before exposing the app to untrusted users. Review
  [`docs/SECURITY.md`](docs/SECURITY.md) before a public deployment.

## License

**No license file is currently included.** Public visibility on GitHub does not itself grant
permission to reuse, modify or redistribute the code. The repository owner needs to choose a
license before the project can be described as open source. No license is invented here, and
contributors should not add one without the owner's decision.

## Contributing

Contribution guidance, branch/PR expectations, test requirements and secret-handling rules are in
[`CONTRIBUTING.md`](CONTRIBUTING.md). Bug reports and feature requests use the templates in
[`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Development setup](docs/DEVELOPMENT.md)
- [Testing and quality](docs/TESTING.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)
- [Documentation assets](docs/assets/README.md)

---

<div align="center">
  <p><strong>CareerGraph AI</strong> · Know your gap. Build your path. Meet your mentor.</p>
  <p><a href="https://github.com/RudraPratap01/careergraph-ai">GitHub</a> · <a href="https://github.com/RudraPratap01/careergraph-ai/issues">Issues</a> · <a href="docs/ARCHITECTURE.md">Docs</a></p>
  <p><em>Built to make career preparation explainable.</em></p>
</div>
