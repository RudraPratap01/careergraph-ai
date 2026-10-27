# API Reference

The FastAPI application serves routes at the backend root (`http://localhost:8000`). The React
client calls `/api/...`; in local development Vite rewrites `/api` to the backend. A deployed
reverse proxy must provide the same mapping.

Interactive OpenAPI documentation is available at `/docs` and `/openapi.json` while the API is
running.

## Authentication

- Protected routes require `Authorization: Bearer <JWT>`.
- Obtain a token with `POST /auth/login`.
- Tokens expire according to `ACCESS_TOKEN_EXPIRE_MINUTES` (24 hours by default).
- Missing, malformed or expired tokens return `401`.
- Role or ownership failures use `403` where the role is the problem and `404` where revealing
  another user's resource would leak its existence.

## System and authentication

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| GET | `/health` | Server and database health | No |
| POST | `/auth/register` | Create a student, alumni or admin account | No |
| POST | `/auth/login` | Log in and receive a JWT | No |
| GET | `/auth/me` | Current user | Yes |

## Profiles and mentors

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| GET | `/profile/me` | Current profile and completion score | Yes |
| PUT | `/profile/student` | Update student education, target role and skills | Student |
| PUT | `/profile/alumni` | Update alumni role, expertise and availability | Alumni |
| GET | `/profile/{user_id}` | Public profile | Yes |
| GET | `/alumni` | Available alumni mentors, optional `expertise` filter | No |

## Resume intelligence

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| POST | `/resume/upload` | Upload and parse PDF, DOCX or TXT (10 MB limit) | Student |
| GET | `/resume/latest` | Most recent parsed resume for the current user | Student |
| POST | `/resume/confirm-skills` | Confirm reviewed skills with `resume` or `self` provenance | Student |

Resume confirmation preserves assessment and GitHub evidence and does not accept those sources in
the request.

## Skill gaps and readiness

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| GET | `/career/occupations` | Curated occupation catalog | Yes |
| GET | `/career/occupations/{key}` | Occupation with required and optional skills | Yes |
| GET | `/career/gap-analysis` | Deterministic readiness analysis, optional `?occupation=` | Student |

Readiness is a weighted coverage metric, not a probability of employment.

## Skill dependency graph

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| GET | `/graph/stats` | Active backend, node/edge counts and acyclicity | Yes |
| GET | `/graph/skills/{skill}` | Transitive prerequisites and direct dependents | Yes |

## Learning roadmap

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| POST | `/roadmap/generate` | Generate a prerequisite-ordered roadmap | Student |
| GET | `/roadmap` | Current active roadmap | Student |
| GET | `/roadmap/{roadmap_id}` | A roadmap owned by the current user | Student |
| GET | `/roadmap/{roadmap_id}/explanations` | Per-step explanations | Student |
| POST | `/roadmap/{roadmap_id}/steps` | Update one step's progress | Student |
| POST | `/roadmap/refresh` | Regenerate from current skills and target role | Student |

Roadmap endpoints are ownership-scoped. Requesting another user's roadmap returns `404`.

## Skill assessments

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| GET | `/assessments` | Curated assessment catalogue | Student |
| GET | `/assessments/attempts` | Attempt history, newest first | Student |
| GET | `/assessments/{key}` | One assessment's questions; answers are not included | Student |
| POST | `/assessments/{key}/start` | Start an attempt and return questions | Student |
| POST | `/assessments/attempts/{id}/submit` | Grade an attempt deterministically | Student |
| POST | `/assessments/attempts/{id}/confirm-skills` | Add skills passed in that attempt | Student |

A pass suggests evidence; the student confirms what is added. It is not a certification.

## Alumni matching and mentorship

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| GET | `/mentorship/matches` | Rank available alumni for the current student | Student |
| GET | `/mentorship/requests` | Sent requests (student) or received requests (alumni) | Yes |
| POST | `/mentorship/requests` | Request mentorship | Student |
| POST | `/mentorship/requests/{id}/accept` | Accept a request (targeted mentor; capacity enforced) | Alumni |
| POST | `/mentorship/requests/{id}/decline` | Decline a request (targeted mentor) | Alumni |
| POST | `/mentorship/requests/{id}/cancel` | Cancel your own pending request | Student |

Request actions are party-scoped. A non-party gets `404`; a party without the required role gets
`403`.

## GitHub and LinkedIn verification

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| POST | `/verification/github` | Fetch a public GitHub account and repositories; store analysis | Student |
| GET | `/verification/github` | Stored verification, `404` if none | Student |
| DELETE | `/verification/github` | Unlink account; GitHub-sourced skills become self-reported | Student |
| POST | `/verification/github/confirm-skills` | Add selected detected skills | Student |
| POST | `/verification/linkedin` | Save a LinkedIn URL as self-declared, unverified | Student |
| GET | `/verification/linkedin` | Stored LinkedIn link, `404` if none | Student |
| GET | `/verification/status` | Combined GitHub and LinkedIn status | Student |

GitHub uses the public, unauthenticated REST API. Upstream failures map to `404` for an unknown
account, `503` for rate limits/network failures and `502` for other upstream errors. LinkedIn is
always `verified: false`.

## Grounded career intelligence

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| POST | `/intelligence/ask` | Ask a career-learning question; return answer, mode, sources, context, privacy note and limitations | Student/Admin |
| GET | `/intelligence/status` | Retrieval, LLM and corpus status without exposing the key | Yes |

`occupation` is optional and defaults to the student's saved target role. An explicitly requested
unknown occupation returns `404`; a stale role on the profile is treated as no target role. The
route does not accept a user ID, resume payload or arbitrary prompt context.

The response's `llm_used` is exactly `mode == "llm"`. When no key is configured, the backend uses
`grounded_extractive` and still returns cited source cards. When a model response fails citation or
link validation, the same deterministic fallback is used with an explicit notice.

## Error handling

- FastAPI validation errors return `422` with field details.
- API errors use a string or structured `detail`; the frontend's `formatApiError` normalizes both.
- The API never reports a successful verification or LLM answer that did not actually pass its
  checks.
