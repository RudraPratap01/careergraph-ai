# Development

This guide covers a local development setup. The default configuration uses SQLite and the
in-memory skill graph, so Docker is optional for everyday work.

## Prerequisites

- Python 3.11 or newer. The release was verified with Python 3.14.
- Node.js 22 or newer. CI uses Node 22.
- npm (included with Node.js).
- Git.
- Optional: Docker Desktop only if you want local PostgreSQL/Neo4j containers. Docker was not
  available in the release environment; the CI integration job uses disposable service containers
  instead.

## Clone and install

```bash
git clone https://github.com/RudraPratap01/careergraph-ai.git
cd careergraph-ai
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

Copy-Item .env.example backend\.env
# Edit backend\.env before starting the API.

Set-Location backend
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

cp .env.example backend/.env
# Edit backend/.env before starting the API.

cd backend
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The backend starts at <http://localhost:8000>. API docs are at
<http://localhost:8000/docs> and health is at <http://localhost:8000/health>.

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

The Vite client starts at <http://localhost:5173>. It proxies `/api` to
`http://localhost:8000`; see `frontend/vite.config.js`.

## Environment configuration

The backend reads `backend/.env` when run from the `backend/` directory. Copy
[`.env.example`](../.env.example) to `backend/.env`; do not edit or commit a real `.env` file.
The default values are safe for local development but not for a public deployment.

| Variable | Required | Purpose | Safe example |
| --- | --- | --- | --- |
| `APP_NAME` | Optional | Display name in the API metadata | `CareerGraph AI` |
| `APP_VERSION` | Optional | Application version string | `0.1.0` |
| `DEBUG` | Optional | FastAPI debug flag; should be `False` outside local development | `True` |
| `ENVIRONMENT` | Optional | Human-readable environment label | `development` |
| `DATABASE_URL` | Required for the target environment | SQLAlchemy database URL | `sqlite:///./careergraph_dev.db` |
| `SECRET_KEY` | **Required** | JWT signing secret; generate a long random value per environment | `<random 64+ character hex value>` |
| `ALGORITHM` | Optional | JWT algorithm; keep `HS256` unless the deployment has a reason to change it | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Access-token lifetime in minutes | `1440` |
| `CORS_ORIGINS` | Required for browser deployments | JSON array of allowed frontend origins | `["https://app.example.com"]` |
| `GRAPH_BACKEND` | Optional | `memory` (default) or `neo4j` | `memory` |
| `NEO4J_URI` | Required if `GRAPH_BACKEND=neo4j` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Required if `GRAPH_BACKEND=neo4j` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Required if `GRAPH_BACKEND=neo4j` | Neo4j password; keep it in the environment, not Git | `<test-only-password>` |
| `OPENROUTER_API_KEY` | Optional | Enables the optional LLM explanation path; leave blank for local-only answers | `<provider key>` |
| `OPENROUTER_BASE_URL` | Optional | OpenRouter-compatible API base URL | `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | Optional | Model identifier used when the key is present | `openai/gpt-4o-mini` |
| `LLM_TIMEOUT_SECONDS` | Optional | Provider request timeout | `20` |
| `LLM_MAX_TOKENS` | Optional | Maximum generated tokens | `600` |
| `LLM_TEMPERATURE` | Optional | Sampling temperature | `0.2` |
| `RAG_TOP_K` | Optional | Maximum retrieved chunks | `6` |
| `RAG_MIN_SCORE` | Optional | Minimum BM25 score; lower values retrieve more but may weaken grounding | `1.0` |

Generate a secret locally with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Never put backend secrets in a frontend environment file. The frontend does not need any
credentials; it calls the API through the same-origin `/api` path.

### PostgreSQL mode

The repository includes a Docker Compose definition for PostgreSQL 16 and Neo4j. Do not assume it
has been executed in your environment. The release verified PostgreSQL and Neo4j through the
GitHub Actions `integration` job's disposable service containers.

If you use the Compose services, review the passwords in `docker-compose.yml` and treat them as
development-only:

```bash
docker compose up -d
```

Then set a PostgreSQL URL in `backend/.env`:

```ini
DATABASE_URL=postgresql+psycopg2://careergraph:careergraph_pass@localhost:5432/careergraph_db
```

Run migrations from `backend/` before starting the API:

```bash
python -m alembic upgrade head
python -m alembic check
```

### Existing SQLite databases

A SQLite file created before Alembic was introduced may not contain an `alembic_version` table.
Back it up before attempting any migration, and do not stamp or delete it unless you understand the
data it contains. The repository does not automate destructive resets.

## Project structure

```text
careergraph-ai/
├── backend/
│   ├── alembic/                 # Migration environment and revisions
│   ├── app/
│   │   ├── data/                # Curated taxonomy, occupations, prerequisites, corpus
│   │   ├── database/            # SQLAlchemy engine/session
│   │   ├── models/              # ORM models
│   │   ├── routes/              # FastAPI HTTP surface
│   │   ├── schemas/             # Pydantic models
│   │   ├── services/            # Deterministic business logic
│   │   └── utils/               # JWT/password helpers
│   └── tests/                   # Pytest suite, including opt-in live-service tests
├── frontend/
│   └── src/
│       ├── components/          # Shared UI and dashboard cards
│       ├── context/             # Authentication state
│       ├── hooks/               # React hooks
│       ├── pages/               # Route screens
│       └── services/api.js      # Single HTTP layer
├── docs/                        # Architecture, testing, security, deployment and assets
├── .github/workflows/ci.yml     # Backend, frontend and integration jobs
├── .env.example
└── docker-compose.yml
```

## Common workflows

### Apply a model change

1. Update the SQLAlchemy model.
2. Create a new Alembic revision from `backend/`.
3. Apply it to a disposable database and run `python -m alembic check`.
4. Add or update a test that exercises the model's behavior.
5. Do not rewrite already-shared migration history.

### Run the checks before a pull request

```bash
cd backend
python -m pytest -q

cd ../frontend
npm run lint
npm run test
npm run build
```

See [TESTING.md](TESTING.md) for the full test matrix, live-service opt-ins and known gaps.

### Add a documentation change

- Keep commands aligned with `frontend/package.json`, `backend/requirements.txt` and the CI workflow.
- Use repository-relative paths for assets.
- Do not include credentials, real user records or browser artifacts.
- Check internal links after editing; see the documentation checks in [TESTING.md](TESTING.md).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `python` is not recognized | Use the platform launcher, such as `py -3.14 -m venv .venv`, and activate the environment |
| Backend starts but `/health` reports a database failure | Confirm `DATABASE_URL` and that the target database is reachable; SQLite paths are relative to `backend/` |
| Frontend requests fail with `401` | Log in again; a changed `SECRET_KEY` invalidates existing tokens |
| Frontend requests fail with a CORS error | Add the exact frontend origin to `CORS_ORIGINS` as a JSON array |
| Advisor returns `grounded_extractive` | This is expected when `OPENROUTER_API_KEY` is blank or the provider fails validation |
| Neo4j is unreachable | Set `GRAPH_BACKEND=memory` for development; the app logs a warning and can fall back |
| Migration reports an unknown database state | Back up the database, inspect `alembic current`, and do not reset data to force a pass |
| Ports 8000/5173 are already in use | Stop the other process or use a different port and update the Vite proxy/config consistently |

## Related documentation

- [Architecture](ARCHITECTURE.md)
- [Testing](TESTING.md)
- [Security](SECURITY.md)
- [Deployment](DEPLOYMENT.md)
- [Contributing](../CONTRIBUTING.md)
