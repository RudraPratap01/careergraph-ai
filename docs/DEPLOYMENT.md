# Deployment

CareerGraph AI has no hosted production deployment at the time of this revision. The repository
contains a working local application, a CI-verified backend/frontend, and live-service integration
tests. This guide describes a supported deployment shape and the checks that must be completed by
the operator.

## Supported architecture

```text
Browser
  -> static HTTPS site (React dist/)
  -> /api/* reverse proxy
  -> FastAPI process
       -> PostgreSQL
       -> optional Neo4j
       -> optional OpenRouter
       -> local curated corpus (inside the image)
```

The frontend requests `/api/...`. In local development Vite rewrites `/api` to
`http://localhost:8000`; in a deployed environment the reverse proxy must forward `/api` to the API
and preserve the rest of the path. Do not expose the Vite development server.

## Environment

Set these values in the server environment or a managed secret store. See
[`.env.example`](../.env.example) and [DEVELOPMENT.md](DEVELOPMENT.md) for the full reference.

Required for a shared deployment:

- a strong `SECRET_KEY`;
- the production `DATABASE_URL`;
- exact `CORS_ORIGINS` for the frontend origin;
- `DEBUG=False` and `ENVIRONMENT=production`.

Optional:

- `GRAPH_BACKEND=neo4j` plus `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD`;
- `OPENROUTER_API_KEY` for explanations that use the validated optional LLM path;
- provider tuning variables such as `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `RAG_TOP_K` and
  `RAG_MIN_SCORE`.

Do not put any of these in frontend source or a public build-time environment file.

## Build and run

### Backend

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell
python -m pip install -r requirements.txt
python -m pip check

# Run this against a backed-up target database.
python -m alembic upgrade head
python -m alembic check

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use a process supervisor or container runtime in production. The repository does not include a
production WSGI/ASGI compose file, TLS terminator, secret manager or autoscaling configuration.

### Frontend

From `frontend/`:

```bash
npm ci
npm run build
```

Publish `frontend/dist/` from a static host or web server, with a single-page-app fallback to
`index.html`. Configure the same origin's `/api` proxy to the FastAPI service.

## Database migrations

- Alembic is the schema history; startup table creation is a development convenience, not a
  replacement for migrations.
- Take a backup and verify the target database before running `alembic upgrade head`.
- Run `alembic check` so a migration/model mismatch fails the release instead of reaching users.
- Migrations are additive in the verified history. Review any future downgrade plan carefully;
  do not treat downgrades as a routine rollback for data-bearing systems.
- SQLite is suitable for local development, not a shared production store.
- PostgreSQL 16 migrations and round-trip tests passed in the CI integration job against a
  disposable service container.

## Neo4j

- The default `GRAPH_BACKEND=memory` requires no graph server.
- For a shared graph, use Neo4j 5 and a dedicated account/password.
- Restrict network access to the Bolt port; do not expose the browser UI publicly.
- If the adapter cannot connect, the app falls back to the in-memory graph. That keeps the service
  available but means graph persistence is not active; monitor the backend logs and graph status.
- Live Neo4j tests are opt-in and use a disposable graph. Never run their write-enabled setup
  against production.

## Optional LLM provider

The advisor works without a key. If you enable OpenRouter:

- keep the key backend-only;
- add gateway rate limiting and spend controls, because there is no application-level per-user
  quota;
- monitor provider failures, timeouts and validation fallbacks;
- keep the deterministic fallback enabled;
- confirm that provider data handling is acceptable for the deployment's privacy policy.

A live OpenRouter call has not been verified in this repository because no provider key was
available. Unit tests exercise the request/validation/fallback behavior with a fake client.

## Health and monitoring

- `GET /health` is the application/database health endpoint.
- `GET /docs` is the interactive API documentation when exposed; protect it if necessary.
- Monitor:
  - HTTP 5xx rates and latency;
  - database connectivity and connection-pool saturation;
  - GitHub `503`/rate-limit responses;
  - Neo4j fallback warnings when the graph backend is configured;
  - LLM provider errors, validation fallbacks and spend;
  - resume upload failures and storage capacity.

The application has no metrics backend, tracing exporter or alerting integration. Add those at the
platform layer.

## Backups and recovery

Back up:

- the relational database (PostgreSQL dump or SQLite file as appropriate);
- uploaded resume files in `backend/uploads/` or the configured production storage;
- Neo4j data if the graph backend is used;
- deployment secrets and configuration in the secret manager.

Test a restore into a disposable environment before relying on a backup. The repository does not
include a backup job or restore automation.

## Rollback

Use the hosting platform's previous release artifact and keep the database backup from before the
migration. Because migrations may be forward-only in practice, do not assume that redeploying old
application code is sufficient; check schema compatibility and restore from backup if required.

## Docker Compose

`docker-compose.yml` defines development PostgreSQL 16 and Neo4j containers. The release
environment did not have Docker available, so the Compose file was not executed as part of the
release. The live-service verification path was the GitHub Actions `integration` job's disposable
service containers. If you use Compose:

- treat the sample passwords as development-only;
- run migrations after the containers are healthy;
- never expose the database ports to the public internet;
- do not run destructive Neo4j integration setup against a graph you care about.

## Release checklist

Before inviting untrusted users, restrict `/auth/register` so clients cannot assign themselves the
`admin` role. The current development API accepts a client-supplied role, including `admin`, even
though the web UI exposes only student/alumni choices. It also has no application-level
authentication throttling. Put those controls at the proxy or API gateway, or change the
application before release.

1. Back up the target database and files; record `alembic current`.
2. Set production secrets and exact CORS origins; keep `DEBUG=False`.
3. Apply migrations and run `alembic check`.
4. Run backend tests, frontend lint/tests/build and `pip check`.
5. Build the frontend and deploy the static artifact with the `/api` proxy.
6. Confirm `/health`, a login, a profile update, a gap analysis and an advisor request in a
   staging environment.
7. If the provider is enabled, verify a live advisor explanation and its citations without
   exposing the key.
8. Confirm logs do not contain tokens, passwords, resume text or provider keys.
9. Review [SECURITY.md](SECURITY.md) and complete the deployment hardening checklist.

## Related documentation

- [Development](DEVELOPMENT.md)
- [Testing](TESTING.md)
- [Security](SECURITY.md)
- [Architecture](ARCHITECTURE.md)
