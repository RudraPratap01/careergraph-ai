# Changelog

This project does not yet have a tagged release or a package published to a registry. The dates
below describe repository milestones from the Git history; they are not release dates for a hosted
service.

## Unreleased

### Documentation and repository polish

- Rebuilt the root README as a project landing page with real application screenshots, an
  architecture overview, verified setup commands, configuration reference and honest limitations.
- Added architecture, development, testing, security, deployment and API documentation.
- Added an editable architecture diagram, README banner and GitHub social-preview image under
  `docs/assets/`.
- Added issue-report and pull-request templates, `.editorconfig`, `.gitattributes` and repository
  hygiene notes.
- Documented that no license is currently declared and that a licensing decision belongs to the
  repository owner.
- Did not change application behavior, database models or migrations.

## 2026-10-27

### Verified release candidate

- Added the Phase 7 Grounded Career Advisor: local BM25 retrieval, curated source attribution,
  citation/link validation, optional OpenRouter explanations and deterministic extractive fallback.
- Added advisor frontend states, protected routing, dashboard/gap/roadmap entry points and
  responsive styling.
- Hardened resume-review provenance preservation and GitHub/assessment evidence handling.
- Added opt-in live PostgreSQL and Neo4j tests and hardened Neo4j lifecycle/fallback behavior.
- Recorded successful live PostgreSQL 16 and Neo4j 5.24 integration in GitHub Actions.
- Verified 334 backend tests passed with 7 skips, 60 frontend tests passed, lint clean and
  production build successful.

## 2026-10-21

### Evidence and verification UI

- Added GitHub verification with deterministic public-repository analysis, fork exclusion and
  evidence-only skill confirmation.
- Added LinkedIn URL storage with explicit unverified/self-declared semantics.
- Added verification UI and dashboard integration.

## 2026-10-18

### Assessments and mentorship

- Added the curated assessment bank, deterministic grading, per-step review and evidence-only
  skill confirmation.
- Added alumni matching with itemized factor scoring and a party-scoped mentorship request
  lifecycle.
- Added assessment and mentor screens, tests and documentation.

## 2026-10-17

### Skill gaps, graph and roadmaps

- Added the occupation catalog, deterministic weighted readiness scoring and gap explanations.
- Added the curated skill-dependency graph with in-memory and optional Neo4j adapters.
- Added prerequisite-ordered roadmaps, persisted progress and refresh semantics.
- Added the React dashboard, profile, resume, gap and roadmap screens; expanded the Vitest suite and
  CI.

## 2026-10-14

### Foundation

- Initial FastAPI/React foundation with JWT authentication, profiles, health checks, SQLite
  development setup, resume intelligence and project documentation.

## Related documents

- [README](README.md)
- [Release verification](docs/TESTING.md)
- [Architecture](docs/ARCHITECTURE.md)
