# CareerGraph AI — Frontend

React 19 + Vite client for CareerGraph AI. The root [README](../README.md) is the project landing
page; architecture and setup details live in [`docs/`](../docs/).

## Local development

Start the backend on `http://127.0.0.1:8000` first, then:

```bash
npm ci
npm run dev
```

The Vite dev server runs at `http://localhost:5173` and proxies `/api` to the backend. No frontend
environment file or secret is required.

## Commands

```bash
npm run dev         # Vite dev server
npm run test        # Vitest, run once
npm run test:watch  # Vitest watch mode
npm run lint        # oxlint
npm run build       # production build into dist/
npm run preview     # preview the production build
```

For the complete backend/frontend/integration workflow, see
[`docs/DEVELOPMENT.md`](../docs/DEVELOPMENT.md) and [`docs/TESTING.md`](../docs/TESTING.md).

## Structure

- `src/pages/` — route-level screens, including the advisor and catch-all 404.
- `src/components/` — shared UI (navigation, icons, forms, headers, empty/loading states,
  dashboard cards).
- `src/context/`, `src/hooks/` — authentication state and `useAuth`.
- `src/services/api.js` — the single HTTP layer and FastAPI error normalization.
- `src/index.css` — design tokens, layout, component styles and responsive/reduced-motion rules.
- Colocated `*.test.jsx` files — Vitest + Testing Library coverage.

## Routes

Public: `/`, `/login`, `/register`.

Protected: `/dashboard`, `/profile`, `/resume`, `/career-gap`, `/roadmap`, `/assessments`,
`/mentors`, `/verification`, `/advisor`.

The frontend is a static SPA. A deployment must serve `dist/` with an `index.html` fallback and
proxy `/api` to the FastAPI service.
