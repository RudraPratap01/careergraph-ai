# Contributing

Thanks for considering a contribution to CareerGraph AI. The project is a career-intelligence
application with deterministic career logic and an optional, cited LLM explanation layer. Changes
should preserve both the behavior and the honesty of the product.

## Before you start

- Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for setup and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  for component boundaries.
- Open an issue for a large behavioral change, schema change or new integration before investing
  in a large implementation.
- Do not add a license, change repository visibility or change the project's legal terms without
  the owner's decision. No license file is currently declared; see the [license note](README.md#license).

## Branch and pull request workflow

1. Fork the repository or create a branch from `main`.
2. Keep the branch focused: `feat/...`, `fix/...`, `docs/...` or `test/...`.
3. Make the change, add or update tests, and update documentation where behavior changes.
4. Run the checks in [docs/TESTING.md](docs/TESTING.md).
5. Open a pull request using the template. Describe the problem, the change and the evidence.
6. Do not force-push shared branches. Do not rewrite history that other contributors may have
   based work on.

## Code style

- Python: follow the existing service/route separation, type-friendly schemas and PEP 8-style
  formatting. Keep deterministic business logic in `backend/app/services/` and keep routes thin.
- JavaScript/React: use the existing component patterns, 2-space indentation, functional
  components and the shared `frontend/src/services/api.js` HTTP layer. Run `npm run lint`.
- Keep comments useful and brief. Explain why a constraint exists, not what an obvious line does.
- Preserve ownership checks, provenance rules and user-data boundaries when refactoring.
- Avoid introducing a remote service just to make a demo look complete. Prefer an honest fallback
  or a documented limitation.

## Tests required before submission

At minimum:

```bash
cd backend
python -m pytest -q
python -m alembic check

cd ../frontend
npm run lint
npm run test
npm run build
```

Add a regression test for every bug fix. For changes to scoring, graph ordering, evidence
confirmation, mentoring rules or advisor validation, add focused tests that would fail if the
invariant were removed. Do not weaken or delete tests to make a check pass.

## Security and secrets

- Never commit `.env`, credentials, tokens, private resumes, databases, uploaded files, browser
  artifacts or generated build output.
- Use synthetic records for screenshots and documentation.
- Do not ask issue reporters for passwords, tokens or private resume contents.
- If you discover a vulnerability, follow [docs/SECURITY.md](docs/SECURITY.md); do not post exploit
  details or secrets in a public issue.

## Product honesty

- Readiness is weighted coverage of curated required skills, not a probability of employment.
- A passed assessment, extracted resume skill or GitHub-detected language is evidence that must be
  explicitly reviewed and confirmed; it is not an automatic certification.
- LinkedIn remains self-declared and unverified.
- The optional LLM may explain retrieved evidence only. It must not invent skills, alter scores,
  change roadmap order, create course URLs or claim unsupported facts.
- If a feature cannot be verified in the current environment, document the limitation rather than
  inventing results.

## Commit messages

Use a short imperative subject and a useful body when needed:

```text
feat: add cited fallback notice to the advisor response
fix: preserve assessment provenance during resume review
docs: clarify PostgreSQL migration setup
```

## Review expectations

A maintainer will look for correct behavior, tests, security boundaries, accurate documentation
and a clean diff. A documentation-only contribution is still expected to leave the repository's
links and commands consistent.

## Related documents

- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)
- [Testing](docs/TESTING.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
