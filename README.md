# CareerGraph AI

> **Know your gap. Build your path. Meet your mentor.**

A career intelligence platform for BTech / final-year students. It analyzes skills from multiple sources, calculates skill gaps against target careers, generates personalized roadmaps, and matches students with alumni mentors.

---

## Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Foundation — FastAPI, React, Auth, Database |
| Phase 2 | ✅ Complete | User Profiles — Student & Alumni Profile Models, Schemas, Routes & UI |
| Phase 3 | ⏳ Next | Resume Intelligence — Parsing & Skill Extraction |
| Phase 4 | — | GitHub + LinkedIn |
| Phase 5 | — | Career Intelligence |
| Phase 6 | — | Skill Dependency Graph (Neo4j) |
| Phase 7 | — | RAG + Knowledge Base |
| Phase 8 | — | Personalized Roadmap |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL (SQLite for local dev) |
| Graph | Neo4j (Phase 6) |
| NLP/ML | spaCy, sentence-transformers (Phase 3+) |
| LLM | OpenRouter API (Phase 7+) |
| Auth | JWT + bcrypt |

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Git

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000  
API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Environment Configuration

Copy `.env.example` to `backend/.env` and fill in values.

For local development (no Docker):
```
DATABASE_URL=sqlite:///./careergraph_dev.db
```

For PostgreSQL (when Docker is available):
```bash
docker compose up -d
# Then update .env:
DATABASE_URL=postgresql+psycopg2://careergraph:careergraph_pass@localhost:5432/careergraph_db
```

---

## API Endpoints

### Authentication & System (Phase 1)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /health | Server + DB health check | No |
| POST | /auth/register | Create account | No |
| POST | /auth/login | Login, get JWT token | No |
| GET | /auth/me | Get current user | Yes |

### User Profiles & Mentors (Phase 2)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /profile/me | Get current user's profile & completion score | Yes |
| PUT | /profile/student | Update student education, target role & skills | Yes (Student) |
| PUT | /profile/alumni | Update alumni role, expertise & availability | Yes (Alumni) |
| GET | /profile/{user_id} | Get public profile for any user | Yes |
| GET | /alumni | List available alumni mentors (with `expertise` filter) | No |

---

## Architecture

```
Browser (React/Vite :5173)
        │
        │  HTTP + JWT
        ▼
FastAPI Backend (:8000)
        │
        ├── Pydantic validation
        ├── SQLAlchemy ORM
        ├── JWT Auth
        │
        ▼
SQLite (dev) / PostgreSQL (prod)
```

---

## Project Structure

```
careergraph-ai/
├── frontend/           React + Vite + Tailwind
├── backend/
│   └── app/
│       ├── config.py   All settings from .env
│       ├── database/   SQLAlchemy session
│       ├── models/     DB models
│       ├── schemas/    Pydantic schemas
│       ├── routes/     API endpoints
│       ├── services/   Business logic
│       └── utils/      JWT, password hashing
├── docker-compose.yml  PostgreSQL + Neo4j
└── .env.example        Config template
```

---

## Viva Answers

**Why FastAPI?**  
Python-native, fast, auto-generates API docs, integrates naturally with NLP/ML libraries.

**Why SQLAlchemy?**  
ORM that works with both SQLite (dev) and PostgreSQL (prod) — switching is a config change.

**Why JWT?**  
Stateless authentication — the server doesn't need a session store. Token carries identity.

**Why bcrypt?**  
Slow by design — makes brute-force attacks expensive. Never stores plaintext passwords.

**Why separate service layer?**  
Routes handle HTTP. Services handle business logic. Easier to test and maintain.
