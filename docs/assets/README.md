# Documentation Assets

These files are used by the README and docs. Everything here is repository-local; no external
image host is required.

| File | Purpose | Provenance |
| --- | --- | --- |
| `readme-banner.svg` | README visual header | Original SVG created for this repository |
| `architecture.svg` | System architecture diagram | Original SVG based on the implemented components |
| `github-social-preview.svg` | Editable source for the social preview | Original SVG created for this repository |
| `github-social-preview.png` | GitHub repository social preview (1280x640) | Rendered locally from the SVG |
| `screenshots/dashboard.png` | Dashboard | Running app, synthetic demo data |
| `screenshots/resume.png` | Resume analysis/review | Running app, synthetic demo data |
| `screenshots/career-gap.png` | Skill gaps and readiness | Running app, synthetic demo data |
| `screenshots/roadmap.png` | Learning roadmap | Running app, synthetic demo data |
| `screenshots/advisor.png` | Grounded advisor with cited sources | Running app, synthetic demo data |
| `screenshots/advisor-mobile.png` | Advisor at 390px | Running app, synthetic demo data |

## Screenshots

Screenshots were captured on 2026-10-27 from the running React client and FastAPI backend using a
disposable SQLite database. The demo accounts, profile, resume, mentors and companies are
synthetic (`demo.student@example.com` and example organizations). No real user records, session
cookies, tokens, credentials or private resumes are shown. The records are not a claim about a
hosted deployment.

## Social preview

GitHub does not read a social-preview image from the repository automatically. A repository owner
with settings permission must upload `github-social-preview.png` under
**Settings -> General -> Social preview**. The image is decorative and is not an application
screenshot.

## Diagram editing

The SVG files are self-contained: they use installed/system fonts, gradients, filters and shapes,
but no remote fonts, scripts or network requests. Keep labels readable at normal GitHub display
width when editing. The architecture diagram must remain aligned with the actual fallback paths in
`backend/app/services/career_intelligence_service.py`.
