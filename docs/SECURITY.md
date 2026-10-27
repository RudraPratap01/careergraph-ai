# Security

CareerGraph AI is a development-stage application. This document describes the implemented
security boundaries and the work that remains before operating it as a public service. It is not a
claim of a security audit or certification.

## Secret management

- Never commit `.env`, API keys, database passwords, JWT secrets, tokens or private resumes.
- `.env` and database files are ignored by Git; `backend/uploads/` is ignored because uploaded
  user files are runtime data, not repository content.
- `OPENROUTER_API_KEY`, `SECRET_KEY`, `NEO4J_PASSWORD` and database credentials belong in the
  server environment or a managed secret store.
- Use a different, random `SECRET_KEY` per environment. A leaked secret allows token forgery; a
  changed secret invalidates existing tokens.
- The advisor status endpoint never returns the OpenRouter key or full secret configuration.

## Authentication and sessions

- Passwords are hashed with bcrypt; plaintext passwords are never stored.
- Authentication is a signed JWT (HS256 by default) with a configurable expiry, 24 hours in the
  reference configuration.
- The frontend stores the token in `localStorage` and sends it as a bearer token.
  - This is simple for a single-page client, but any successful XSS can read the token.
  - Deploy with a strict Content Security Policy, avoid untrusted script injection, and consider a
    hardened same-site cookie session if the threat model requires it.
- There is no refresh-token rotation, password-reset flow, multi-factor authentication or
  server-side session revocation list in the current implementation.
- Missing, malformed or expired tokens return `401`.

## Authorization and user-data isolation

- Roles are enforced on protected routes: student, alumni and admin capabilities are not
  interchangeable.
- Roadmaps, resumes, assessments, mentorship requests and verification records are scoped to the
  authenticated user or to the parties in the relationship.
- Requests for another user's owned roadmap or mentorship record use `404` rather than confirming
  that the record exists.
- Assessment answers are not included in the public question schema and are only returned after a
  submission is graded.
- Evidence confirmation is rechecked on the server. A client cannot claim a skill was passed,
  detected from GitHub, or extracted from a resume without the matching stored evidence.
- Mentor matching is deterministic and itemized; it is not a hiring prediction and does not expose
  private profile fields beyond the mentor-facing profile contract.

## Resume and upload handling

- Accepted formats are PDF, DOCX and TXT with a 10 MB limit.
- Extraction happens in the backend against the curated taxonomy. No external AI/NLP service
  receives the file.
- Resume files are runtime user data. Production storage must have access controls, backup policy
  and retention/deletion procedures.
- The review flow carries existing profile skills forward and preserves assessment/GitHub
  provenance; it must not be used to silently delete evidence.

## Grounded advisor and LLM privacy

- Retrieval is local lexical BM25 over a curated in-repo corpus. It is not a web search and does
  not fetch arbitrary URLs.
- The question alone is the retrieval query. Profile context is added separately, so an unrelated
  question is not made relevant by the saved target role.
- When an OpenRouter key is configured, the backend may send only:
  - the question;
  - target occupation and canonical skill names;
  - deterministic gap summary and roadmap step names;
  - retrieved curated excerpts with source IDs.
- Resume files/text, names, email addresses, account IDs, tokens and raw profile records are not
  included in the LLM prompt.
- The backend validates the answer before accepting it: at least one valid `[S#]` citation, only
  retrieved citation IDs, no external URL, and 20-3000 characters. On validation failure, timeout,
  provider error or missing key, the deterministic extractive answer is returned with an explicit
  mode/notice.
- Citation validation reduces obvious fabrication; it is not a truth guarantee. The displayed
  excerpts and limitations remain part of the response.
- There is no application-level per-user LLM quota. If a paid provider is enabled for a public
  deployment, add rate limiting, request caps, spend alarms and a kill switch at the API gateway.

## Deployment hardening checklist

- Set `DEBUG=False`, `ENVIRONMENT=production`, a strong `SECRET_KEY` and exact `CORS_ORIGINS`.
- Serve the frontend and API over HTTPS; do not expose the development Vite server.
- Put the API behind a reverse proxy that enforces request-size limits, rate limits and timeouts.
- Use a least-privilege database account; do not use the development Compose credentials in
  production.
- Restrict Neo4j network access and use a dedicated password when the adapter is enabled.
- Keep `/docs` and `/openapi.json` behind appropriate access policy if exposing them is not
  intended.
- Add security headers at the proxy: CSP, HSTS, `X-Content-Type-Options`, frame restrictions and a
  referrer policy.
- Back up PostgreSQL/SQLite data, Neo4j data and uploaded files; test restore procedures.
- Monitor authentication failures, 5xx responses, GitHub rate-limit responses, provider failures
  and unexpected LLM spend.
- Update pinned dependencies deliberately and re-run the test suite and CI after upgrades.

## Reporting a vulnerability

Do not publish credentials, private resumes, personal records or exploit details in a public
issue. If GitHub private vulnerability reporting / Security Advisories is enabled for the
repository, use the repository's **Security** tab. Otherwise contact the repository owner through
GitHub without including secrets, and agree on a private channel before sharing reproduction data.

There is no bug-bounty program or response-time guarantee.

## Known limitations

- No formal security audit, penetration test or compliance certification has been performed.
- No MFA, password reset, refresh-token rotation, audit log, per-user LLM quota or WAF is included.
- JWT in `localStorage` is exposed to XSS; deployment CSP and dependency hygiene are essential.
- The public GitHub integration is unauthenticated and subject to GitHub's 60-request/hour IP rate
  limit.
- The frontend stylesheet imports Google Fonts, so a browser makes a third-party request to Google
  unless the deployment self-hosts the font files. This is not a backend data flow, but it belongs
  in a deployment privacy review.
- LinkedIn links are self-declared and never verified.
- Live OpenRouter behavior has not been verified without a provider key.

## Related documentation

- [Architecture](ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)
- [Testing](TESTING.md)
- [Contributing](../CONTRIBUTING.md)
