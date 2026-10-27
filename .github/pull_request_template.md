## Summary

Describe the problem and the change. Link an issue when applicable.

## Type of change

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation or repository polish
- [ ] Refactor or test-only change
- [ ] Database/migration change
- [ ] Security hardening

## Verification

List the exact commands you ran and their results. Placeholders such as "tests pass" are not
enough.

```text
Backend:
Frontend lint:
Frontend tests:
Frontend build:
Integration (if applicable):
```

## Screenshots or recordings

For UI changes, include a current screenshot or recording made with synthetic data. Do not include
tokens, cookies, real resumes or personal records.

## Security and data checklist

- [ ] I did not commit `.env`, credentials, tokens, private resumes, databases or browser artifacts.
- [ ] The change preserves role checks and user-data isolation.
- [ ] Evidence/provenance rules remain intact, or the migration is explicitly documented.
- [ ] The readiness score, roadmap order and readiness disclaimers remain deterministic unless the change is an approved redesign.
- [ ] The optional LLM still receives only the documented minimal context and cannot change scores or order.
- [ ] Documentation and commands were updated if behavior or configuration changed.

## Database impact

- [ ] No schema or migration change.
- [ ] Migration added/updated and verified with `alembic check`.
- [ ] Rollback/backup considerations documented.

## Additional context

Anything reviewers should know about trade-offs, remaining limitations or unverified paths.
