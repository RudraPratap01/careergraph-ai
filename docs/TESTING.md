# Testing

The project uses deterministic unit/API tests, opt-in live-service integration tests, and a
Chrome-only browser QA harness kept outside the repository. The repository does not claim a
coverage percentage, a formal accessibility certification or a live LLM-provider test.

## Test matrix

| Area | Tool | Where it runs | External services |
| --- | --- | --- | --- |
| Backend units, API behavior, security regressions, journey tests | Pytest | Local and CI | None |
| Frontend components, state, routing and accessibility-oriented assertions | Vitest + Testing Library | Local and CI | None |
| Frontend lint | oxlint | Local and CI | None |
| Frontend production build | Vite | Local and CI | None |
| Alembic migration/model consistency | Alembic | Local and CI | Database |
| Live PostgreSQL schema and round trip | Pytest opt-in | CI service container; local when configured | PostgreSQL 16 |
| Live Neo4j seeding/traversal/lifecycle | Pytest opt-in | CI service container; local when configured | Neo4j 5.24 |
| Real-browser workflow and responsive smoke checks | Playwright Core + Google Chrome | Release QA on the maintainer machine | Running app; synthetic data |
| Automated accessibility scan | axe-core in Chrome | Release QA | Running app |

## Backend tests

From `backend/`:

```bash
python -m pytest -q
```

The ordinary suite uses SQLite/in-memory services. The live PostgreSQL and Neo4j tests skip
cleanly unless their opt-in environment variables are configured. The last release validation of
the application code recorded **334 passed, 7 skipped**. The seven skips were the two PostgreSQL
and five Neo4j opt-in tests; those passed in the GitHub Actions `integration` job against
disposable service containers.

Useful focused runs:

```bash
python -m pytest -q tests/test_phase7_career_intelligence.py
python -m pytest -q tests/test_journey_e2e.py
python -m pytest -q tests/test_security_regressions.py
```

The advisor tests inject a deterministic fake LLM client to exercise request construction,
citation/link validation, fallback and prompt privacy. They do not establish that a live OpenRouter
model produced an answer.

### PostgreSQL opt-in

Apply the migrations to a **disposable** test database, then provide its URL:

```bash
# From backend/
export DATABASE_URL="postgresql+psycopg2://careergraph:password@localhost:5432/careergraph_test"
python -m alembic upgrade head
export POSTGRES_TEST_URL="$DATABASE_URL"
python -m pytest -q tests/test_postgres_integration.py
```

On Windows PowerShell, use `$env:DATABASE_URL = "..."` and
`$env:POSTGRES_TEST_URL = $env:DATABASE_URL`. Do not point these tests at a database containing
data you care about.

### Neo4j opt-in

The live Neo4j test deletes `:Skill` nodes in the target database as part of its clean-seeding
setup. The write opt-in is deliberate:

```bash
export NEO4J_TEST_URI="bolt://localhost:7687"
export NEO4J_TEST_USER="neo4j"
export NEO4J_TEST_PASSWORD="test-only-password"
export NEO4J_TEST_ALLOW_WRITE="true"
python -m pytest -q tests/test_neo4j_integration.py
```

On PowerShell, use `$env:NEO4J_TEST_URI = "..."` and so on. Never enable
`NEO4J_TEST_ALLOW_WRITE` against a graph containing real data.

## Frontend tests

From `frontend/`:

```bash
npm ci
npm run lint
npm run test
npm run build
```

The last release validation of the application code recorded **60 passing frontend tests across
10 Vitest files** and a successful production build. The documentation-only pass does not change
frontend behavior; the final CI run for the new revision is the authoritative check for this
commit. `pip check` and `npm audit --audit-level=high` were also clean at the time of the run.

Coverage includes authentication pages, navbar behavior, resume review and provenance
preservation, readiness and gap selection, roadmap ordering/progress, GitHub verification,
assessments, mentor matching and requests, and advisor loading/success/error/empty states.

## Migrations and dependency consistency

From `backend/`:

```bash
python -m alembic upgrade head
python -m alembic check
python -m pip check
```

The model/migration consistency check is part of both the local verification sequence and the CI
`backend` job. Use a disposable database when checking a schema you do not intend to alter.

Frontend dependency audit:

```bash
cd frontend
npm audit
```

Audit results depend on the current advisory database; do not treat a historical "clean" result as
a permanent guarantee.

## GitHub Actions

The workflow at [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) has three jobs:

1. **Backend** - installs pinned Python requirements on Python 3.14, runs the Pytest suite against
   SQLite, applies Alembic migrations to a disposable SQLite file and runs `alembic check`.
2. **Frontend** - installs with `npm ci` on Node 22, runs lint, Vitest and the production build.
3. **Live PostgreSQL + Neo4j integration** - starts disposable PostgreSQL 16 and Neo4j 5.24
   service containers, applies migrations to PostgreSQL, runs the PostgreSQL round-trip tests and
   runs the live Neo4j adapter tests with write access limited to the disposable graph.

The workflow uses read-only repository permissions. Inspect the latest run for `main` at
<https://github.com/RudraPratap01/careergraph-ai/actions/workflows/ci.yml>.

## Browser QA record

A Chrome-only release QA pass was performed against a throwaway SQLite database and the Vite dev
server using synthetic accounts:

- 115/115 checks in the student/alumni journey;
- 38/38 advisor checks at 1440px and 390px;
- 68/68 responsive checks at 390, 768, 1024 and 1440px;
- 16 page states scanned with axe-core using WCAG 2 A/AA rules, with 0 reported violations.

These were verification tools kept outside the repository, not a committed browser-test suite.
They do not constitute Firefox/Safari coverage, Lighthouse results, a screen-reader session or a
formal WCAG conformance certification. The README screenshots were captured from the running app
with synthetic demo records on 2026-10-27.

## Documentation checks

Documentation changes should be checked with:

- an internal link/asset existence check;
- XML validation for `docs/assets/*.svg`;
- Markdown fence/link review;
- `git diff --check` for whitespace errors;
- a staged-file review for secrets, databases, caches, build output and browser artifacts.

The repository does not currently include a Markdown lint or link-checker dependency. Do not add a
passing badge for either without wiring a real check.

## Known gaps

- No live OpenRouter generation has been verified because no provider key is available. The
  optional path is covered with an injected fake client, and the local fallback is verified.
- Docker Compose was not executed in the release environment. PostgreSQL and Neo4j were verified
  through GitHub Actions service containers.
- Browser QA is Chrome-only. No Firefox, Safari, iOS, Lighthouse or screen-reader run is claimed.
- There is no coverage service or coverage threshold configured.
- There is no hosted production deployment or uptime history.
- The test suite does not cover a production reverse proxy, TLS, database failover or backup
  restore. Those are deployment responsibilities.

## Related documentation

- [Development](DEVELOPMENT.md)
- [Architecture](ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Deployment](DEPLOYMENT.md)
