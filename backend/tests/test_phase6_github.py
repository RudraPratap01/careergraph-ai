"""
Phase 6 — GitHub verification & LinkedIn link.

Covers three things the feature must never get wrong:

1. **Transport honesty** — GitHub failures (404, rate limit, network, 5xx,
   malformed payload) surface as honest HTTP errors, never as a fake success.
2. **Deterministic inference** — repository languages/topics produce the same
   evidence-backed suggestions every time, forks are excluded, and confidence
   stays inside its documented bounds.
3. **Evidence discipline** — only skills actually detected by the stored
   verification can be confirmed; confirmation never downgrades assessment
   evidence, and a resume re-confirm never wipes GitHub evidence.

All GitHub traffic is mocked, so the suite is offline and does not consume the
public rate limit.
"""

import httpx
import pytest

from app.data.skills_taxonomy import is_known_skill, normalize_skill_name
from app.services import github_service
from app.services.github_service import (
    LANGUAGE_TO_SKILL,
    TOPIC_EXTRA_MAP,
    analyze_repositories,
    confidence_for,
    normalize_github_username,
    proficiency_for,
    topic_to_skill,
)


# ── Fixtures / helpers ───────────────────────────────────────────────────────

def _account(login="octocat", **overrides):
    data = {
        "login": login,
        "name": "The Octocat",
        "avatar_url": "https://avatars.githubusercontent.com/u/583231",
        "html_url": f"https://github.com/{login}",
        "bio": "GitHub mascot",
        "public_repos": 8,
        "followers": 120,
        "following": 5,
        "created_at": "2011-01-25T18:44:36Z",
    }
    data.update(overrides)
    return data


def _repo(name, language=None, topics=None, stars=0, fork=False):
    return {
        "name": name,
        "language": language,
        "topics": topics or [],
        "stargazers_count": stars,
        "fork": fork,
    }


DEFAULT_REPOS = [
    _repo("api-service", "Python", ["fastapi", "rest-api", "docker"], stars=12),
    _repo("ml-notebooks", "Python", ["machine-learning", "pandas"], stars=4),
    _repo("web-app", "TypeScript", ["react", "nextjs", "tailwindcss"], stars=7),
    _repo("infra", "Shell", ["docker", "ci-cd"], stars=1),
    _repo("old-fork", "Java", ["spring-boot"], stars=99, fork=True),
]


@pytest.fixture
def fake_github(monkeypatch):
    """Patches the service's transport with an in-memory GitHub."""
    state = {"account": _account(), "repos": list(DEFAULT_REPOS), "calls": []}

    def fake_get(path, params=None, *, not_found_detail="GitHub resource not found."):
        state["calls"].append((path, params))
        if path.endswith("/repos"):
            return state["repos"]
        return state["account"]

    monkeypatch.setattr(github_service, "_github_get", fake_get)
    return state


def _verify(client, headers, username="octocat"):
    return client.post(
        "/verification/github", json={"username": username}, headers=headers
    )


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


# ── Username normalisation ───────────────────────────────────────────────────
class TestUsernameNormalisation:
    def test_bare_username(self):
        assert normalize_github_username("octocat") == "octocat"

    def test_at_prefix(self):
        assert normalize_github_username("  @octocat ") == "octocat"

    def test_profile_url(self):
        assert normalize_github_username("https://github.com/octocat") == "octocat"

    def test_profile_url_with_trailing_slash(self):
        assert normalize_github_username("https://github.com/octocat/") == "octocat"

    def test_rejects_other_hosts(self):
        with pytest.raises(Exception) as exc:
            normalize_github_username("https://gitlab.com/octocat")
        assert "github.com" in str(exc.value)

    def test_rejects_leading_hyphen(self):
        with pytest.raises(Exception):
            normalize_github_username("-octocat")

    def test_rejects_trailing_hyphen(self):
        with pytest.raises(Exception):
            normalize_github_username("octocat-")

    def test_rejects_double_hyphen(self):
        with pytest.raises(Exception):
            normalize_github_username("octo--cat")

    def test_rejects_spaces(self):
        with pytest.raises(Exception):
            normalize_github_username("octo cat")

    def test_empty(self):
        with pytest.raises(Exception):
            normalize_github_username("   ")

    def test_rejects_too_long(self):
        with pytest.raises(Exception):
            normalize_github_username("a" * 40)

    def test_accepts_max_length(self):
        assert normalize_github_username("a" * 39) == "a" * 39


# ── Curated mappings ─────────────────────────────────────────────────────────
class TestCuratedMappings:
    def test_every_language_targets_a_canonical_skill(self):
        for language, skill in LANGUAGE_TO_SKILL.items():
            assert is_known_skill(skill), language
            assert normalize_skill_name(skill) == skill, language

    def test_every_topic_extra_targets_a_canonical_skill(self):
        for topic, skill in TOPIC_EXTRA_MAP.items():
            assert is_known_skill(skill), topic
            assert normalize_skill_name(skill) == skill, topic

    @pytest.mark.parametrize(
        ("topic", "expected"),
        [
            ("machine-learning", "Machine Learning"),
            ("deep-learning", "Deep Learning"),
            ("natural-language-processing", "Natural Language Processing"),
            ("rest-api", "REST APIs"),
            ("nextjs", "Next.js"),
            ("tailwindcss", "Tailwind CSS"),
            ("nodejs", "Node.js"),
            ("ci-cd", "CI/CD"),
            ("github-actions", "CI/CD"),
            ("ml", "Machine Learning"),
            ("aspnet", "ASP.NET"),
            ("penetration-testing", "Penetration Testing"),
        ],
    )
    def test_topic_mapping(self, topic, expected):
        assert topic_to_skill(topic) == expected

    @pytest.mark.parametrize(
        "topic",
        ["jupyter", "hacktoberfest", "portfolio", "unknown-topic-xyz", "", None],
    )
    def test_unmapped_topics_are_skipped(self, topic):
        assert topic_to_skill(topic) is None


# ── Deterministic analysis ──────────────────────────────────────────────────
class TestAnalyzeRepositories:
    def test_language_and_topic_produce_skills(self):
        result = analyze_repositories(DEFAULT_REPOS)
        names = {skill.name for skill in result["skills"]}
        assert {"Python", "TypeScript", "Shell / Bash", "Docker", "REST APIs"} <= names
        # 'fastapi' is an alias of FastAPI, 'react' of React
        assert "FastAPI" in names
        assert "React" in names

    def test_forks_are_analysed_but_excluded_from_evidence(self):
        result = analyze_repositories(DEFAULT_REPOS)
        names = {skill.name for skill in result["skills"]}
        assert result["repos_analyzed"] == len(DEFAULT_REPOS)
        assert result["forks_excluded"] == 1
        # The 99-star fork is Java + spring-boot; neither may appear.
        assert "Java" not in names
        assert "Spring Boot" not in names

    def test_fork_stars_do_not_inflate_totals(self):
        result = analyze_repositories(DEFAULT_REPOS)
        assert result["total_stars"] == 12 + 4 + 7 + 1

    def test_repo_counted_once_when_language_and_topic_overlap(self):
        result = analyze_repositories(
            [_repo("only", "Python", ["python"], stars=3)]
        )
        python = next(s for s in result["skills"] if s.name == "Python")
        assert python.repo_count == 1
        assert python.stars == 3
        assert python.sources == ["language", "topic"]

    def test_deterministic_across_runs(self):
        first = analyze_repositories(DEFAULT_REPOS)
        second = analyze_repositories(DEFAULT_REPOS)
        assert [s.model_dump() for s in first["skills"]] == [
            s.model_dump() for s in second["skills"]
        ]

    def test_skills_sorted_by_confidence_then_count_then_name(self):
        result = analyze_repositories(DEFAULT_REPOS)
        keys = [(-s.confidence, -s.repo_count, s.name) for s in result["skills"]]
        assert keys == sorted(keys)

    def test_languages_sorted_by_count_then_name(self):
        result = analyze_repositories(DEFAULT_REPOS)
        keys = [(-language.count, language.name) for language in result["languages"]]
        assert keys == sorted(keys)

    def test_confidence_bounds_and_monotonicity(self):
        assert confidence_for(1, 0) == 0.60
        assert confidence_for(2, 0) == 0.70
        assert confidence_for(3, 0) == 0.80
        assert confidence_for(5, 0) == 0.90
        assert confidence_for(5, 5) == 0.95
        assert confidence_for(50, 1000) == 0.95
        for count in range(1, 9):
            assert 0.60 <= confidence_for(count, 0) <= 0.95

    def test_proficiency_thresholds(self):
        assert proficiency_for(1, 0) == "beginner"
        assert proficiency_for(1, 1) == "intermediate"
        assert proficiency_for(2, 0) == "intermediate"
        assert proficiency_for(4, 0) == "advanced"
        assert proficiency_for(1, 10) == "advanced"

    def test_evidence_mentions_repos_and_stars(self):
        result = analyze_repositories(DEFAULT_REPOS)
        python = next(s for s in result["skills"] if s.name == "Python")
        assert python.repo_count == 2
        assert "2 non-forked repositories" in python.evidence
        assert python.stars == 16
        assert set(python.repos) == {"api-service", "ml-notebooks"}

    def test_repos_are_capped_but_count_is_truthful(self):
        repos = [_repo(f"r{i}", "Rust", stars=1) for i in range(15)]
        result = analyze_repositories(repos)
        rust = next(s for s in result["skills"] if s.name == "Rust")
        assert rust.repo_count == 15
        assert len(rust.repos) == github_service.MAX_REPOS_SHOWN_PER_SKILL
        assert "and 12 more" in rust.evidence

    def test_empty_input(self):
        result = analyze_repositories([])
        assert result["skills"] == []
        assert result["languages"] == []
        assert result["repos_analyzed"] == 0
        assert result["total_stars"] == 0

    def test_non_dict_entries_are_ignored(self):
        result = analyze_repositories(["not a repo", None, 42])  # type: ignore[list-item]
        assert result["skills"] == []
        assert result["repos_analyzed"] == 0


# ── Verification endpoint ───────────────────────────────────────────────────
class TestVerifyGithubEndpoint:
    def test_requires_authentication(self, client):
        assert client.post("/verification/github", json={"username": "octocat"}).status_code == 401

    def test_alumni_forbidden(self, client, make_user, fake_github):
        headers, _ = make_user(email="alum@example.com", role="alumni")
        assert _verify(client, headers).status_code == 403

    def test_successful_verification(self, client, make_user, fake_github):
        headers, _ = make_user()
        res = _verify(client, headers)
        assert res.status_code == 200, res.text
        body = res.json()

        assert body["source"] == "github"
        assert body["account"]["username"] == "octocat"
        assert body["account"]["name"] == "The Octocat"
        assert body["account"]["profile_url"] == "https://github.com/octocat"
        assert body["account"]["account_age_days"] > 0
        assert body["repos_analyzed"] == 5
        assert body["forks_excluded"] == 1
        assert body["repos_truncated"] is False
        assert body["total_stars"] == 24
        assert body["skills"]
        assert body["disclaimer"]
        assert "github.com/octocat" in body["explanation"]

    def test_uses_public_api_paths(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        paths = [path for path, _ in fake_github["calls"]]
        assert "/users/octocat" in paths
        assert "/users/octocat/repos" in paths
        repo_call = next(call for call in fake_github["calls"] if call[0].endswith("/repos"))
        assert repo_call[1]["type"] == "owner"
        assert repo_call[1]["per_page"] == github_service.MAX_REPOS

    def test_accepts_profile_url(self, client, make_user, fake_github):
        headers, _ = make_user()
        assert _verify(client, headers, "https://github.com/octocat").status_code == 200

    def test_invalid_username_is_400(self, client, make_user, fake_github):
        headers, _ = make_user()
        assert _verify(client, headers, "octo cat").status_code == 400

    def test_github_404_maps_to_404(self, client, make_user, monkeypatch):
        headers, _ = make_user()

        def boom(*args, **kwargs):
            raise github_service.HTTPException(status_code=404, detail="GitHub user 'x' was not found.")

        monkeypatch.setattr(github_service, "_github_get", boom)
        assert _verify(client, headers, "nobody").status_code == 404

    def test_mirrors_username_onto_profile(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        profile = client.get("/profile/me", headers=headers).json()
        assert profile["student_profile"]["github_username"] == "octocat"

    def test_reverification_updates_single_row(self, client, make_user, fake_github, db_session):
        from app.models.github_verification import GitHubVerification

        headers, _ = make_user()
        _verify(client, headers)
        fake_github["account"] = _account(login="octocat", followers=999)
        assert _verify(client, headers).status_code == 200

        rows = db_session.query(GitHubVerification).all()
        assert len(rows) == 1
        assert rows[0].followers == 999

    def test_same_account_cannot_be_claimed_twice(self, client, make_user, fake_github):
        first, _ = make_user(email="one@example.com")
        assert _verify(client, first).status_code == 200

        second, _ = make_user(email="two@example.com")
        res = _verify(client, second)
        assert res.status_code == 409
        assert "already linked" in res.json()["detail"]

    def test_claim_check_is_case_insensitive(self, client, make_user, fake_github):
        first, _ = make_user(email="one@example.com")
        _verify(client, first)

        second, _ = make_user(email="two@example.com")
        assert _verify(client, second, "OCTOCAT").status_code == 409

    def test_truncation_flag_when_cap_is_hit(self, client, make_user, fake_github):
        headers, _ = make_user()
        fake_github["repos"] = [
            _repo(f"r{i}", "Python") for i in range(github_service.MAX_REPOS)
        ]
        body = _verify(client, headers).json()
        assert body["repos_truncated"] is True
        assert "most recently pushed" in body["explanation"]

    def test_relevant_to_target_uses_required_skills(self, client, make_user, fake_github):
        headers, _ = make_user()
        client.put(
            "/profile/student",
            json={"target_role": "Backend Developer", "skills": []},
            headers=headers,
        )
        body = _verify(client, headers).json()
        assert body["target_role"] == "Backend Developer"
        # Python is required for Backend Developer and present in the fake repos.
        assert "Python" in body["relevant_to_target"]
        # TypeScript is not required for Backend Developer.
        assert "TypeScript" not in body["relevant_to_target"]

    def test_get_verification_404_before_verifying(self, client, make_user):
        headers, _ = make_user()
        assert client.get("/verification/github", headers=headers).status_code == 404

    def test_get_verification_returns_stored_copy(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        res = client.get("/verification/github", headers=headers)
        assert res.status_code == 200
        assert res.json()["account"]["username"] == "octocat"


# ── Transport failure mapping ───────────────────────────────────────────────
class TestTransportFailures:
    def _patch(self, monkeypatch, response=None, exc=None):
        def fake_get(*args, **kwargs):
            if exc is not None:
                raise exc
            return response

        monkeypatch.setattr(github_service.httpx, "get", fake_get)

    def test_timeout_is_503(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(monkeypatch, exc=httpx.TimeoutException("slow"))
        res = _verify(client, headers)
        assert res.status_code == 503
        assert "did not respond" in res.json()["detail"]

    def test_network_error_is_503(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(monkeypatch, exc=httpx.ConnectError("offline"))
        res = _verify(client, headers)
        assert res.status_code == 503
        assert "Could not reach GitHub" in res.json()["detail"]

    def test_rate_limit_is_503_with_explicit_message(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(
            monkeypatch,
            response=FakeResponse(403, headers={"x-ratelimit-remaining": "0"}),
        )
        res = _verify(client, headers)
        assert res.status_code == 503
        assert "rate limit" in res.json()["detail"]

    def test_429_is_rate_limit(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(monkeypatch, response=FakeResponse(429))
        assert _verify(client, headers).status_code == 503

    def test_plain_403_is_502(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(
            monkeypatch,
            response=FakeResponse(403, headers={"x-ratelimit-remaining": "42"}),
        )
        assert _verify(client, headers).status_code == 502

    def test_500_is_502(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(monkeypatch, response=FakeResponse(500))
        assert _verify(client, headers).status_code == 502

    def test_invalid_json_is_502(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(monkeypatch, response=FakeResponse(200, payload=None))
        assert _verify(client, headers).status_code == 502

    def test_non_object_account_is_502(self, client, make_user, monkeypatch):
        headers, _ = make_user()
        self._patch(monkeypatch, response=FakeResponse(200, payload=[]))
        assert _verify(client, headers).status_code == 502


# ── Confirming inferred skills ──────────────────────────────────────────────
class TestConfirmGitHubSkills:
    def test_confirm_before_verifying_is_404(self, client, make_user):
        headers, _ = make_user()
        res = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )
        assert res.status_code == 404

    def test_confirm_adds_with_github_source(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)

        res = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python", "TypeScript"]},
            headers=headers,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["added"] == ["Python", "TypeScript"]
        assert body["upgraded"] == []
        assert body["already_present"] == []

        by_name = {s["name"]: s for s in body["skills"]}
        assert by_name["Python"]["source"] == "github"
        # Two Python repos with 16 combined stars -> advanced per the thresholds.
        assert by_name["Python"]["level"] == "advanced"
        assert by_name["TypeScript"]["source"] == "github"
        # One repo with stars -> intermediate by the documented thresholds.
        assert by_name["TypeScript"]["level"] == "intermediate"

    def test_confirm_rejects_undetected_skill(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        res = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Kubernetes"]},
            headers=headers,
        )
        assert res.status_code == 400
        assert "was not detected" in res.json()["detail"]

    def test_confirm_normalises_aliases(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        body = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["python"]},
            headers=headers,
        ).json()
        assert body["added"] == ["Python"]

    def test_confirm_empty_selection_is_400(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        assert (
            client.post(
                "/verification/github/confirm-skills",
                json={"skills": []},
                headers=headers,
            ).status_code
            == 400
        )

    def test_confirm_is_idempotent(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )
        body = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        ).json()
        assert body["added"] == []
        assert body["already_present"] == ["Python"]
        assert sum(1 for s in body["skills"] if s["name"] == "Python") == 1

    def test_confirm_upgrades_self_reported_skill_but_keeps_level(
        self, client, make_user, fake_github
    ):
        headers, _ = make_user()
        client.put(
            "/profile/student",
            json={"skills": [{"name": "Python", "level": "advanced", "source": "self"}]},
            headers=headers,
        )
        _verify(client, headers)
        body = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        ).json()
        assert body["added"] == []
        assert body["upgraded"] == ["Python"]
        skill = next(s for s in body["skills"] if s["name"] == "Python")
        assert skill["source"] == "github"
        assert skill["level"] == "advanced"

    def test_confirm_never_downgrades_assessment_evidence(
        self, client, make_user, fake_github
    ):
        headers, _ = make_user()
        client.put(
            "/profile/student",
            json={"skills": [{"name": "Python", "level": "advanced", "source": "assessment"}]},
            headers=headers,
        )
        _verify(client, headers)
        body = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        ).json()
        assert body["already_present"] == ["Python"]
        skill = next(s for s in body["skills"] if s["name"] == "Python")
        assert skill["source"] == "assessment"

    def test_resume_reconfirm_preserves_github_evidence(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )

        # A resume review that does not mention Python must not erase it.
        res = client.post(
            "/resume/confirm-skills",
            json={"skills": [{"name": "Docker", "level": "beginner", "source": "self"}]},
            headers=headers,
        )
        assert res.status_code == 200, res.text

        skills = client.get("/profile/me", headers=headers).json()["student_profile"]["skills"]
        by_name = {s["name"]: s for s in skills}
        assert by_name["Python"]["source"] == "github"
        assert by_name["Docker"]["source"] == "resume"

    def test_alumni_cannot_confirm(self, client, make_user, fake_github):
        headers, _ = make_user(email="alum@example.com", role="alumni")
        res = client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )
        assert res.status_code == 403


# ── Disconnect ──────────────────────────────────────────────────────────────
class TestDisconnect:
    def test_disconnect_removes_verification_and_downgrades_skills(
        self, client, make_user, fake_github
    ):
        headers, _ = make_user()
        _verify(client, headers)
        client.post(
            "/verification/github/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )

        res = client.delete("/verification/github", headers=headers)
        assert res.status_code == 200
        assert res.json()["disconnected"] is True

        assert client.get("/verification/github", headers=headers).status_code == 404
        profile = client.get("/profile/me", headers=headers).json()["student_profile"]
        assert profile["github_username"] is None
        python = next(s for s in profile["skills"] if s["name"] == "Python")
        assert python["source"] == "self"

    def test_disconnect_without_link_is_harmless(self, client, make_user):
        headers, _ = make_user()
        res = client.delete("/verification/github", headers=headers)
        assert res.status_code == 200
        assert res.json()["disconnected"] is True


# ── LinkedIn (explicitly unverified) ────────────────────────────────────────
class TestLinkedIn:
    def test_valid_profile_url_is_stored_unverified(self, client, make_user):
        headers, _ = make_user()
        res = client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/in/jane-doe/?trk=public"},
            headers=headers,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["linkedin_url"] == "https://www.linkedin.com/in/jane-doe"
        assert body["verified"] is False
        assert "public api" in body["note"].lower()

    def test_url_without_scheme_is_accepted(self, client, make_user):
        headers, _ = make_user()
        res = client.post(
            "/verification/linkedin",
            json={"url": "linkedin.com/in/jane-doe"},
            headers=headers,
        )
        assert res.status_code == 200

    def test_other_host_rejected(self, client, make_user):
        headers, _ = make_user()
        res = client.post(
            "/verification/linkedin",
            json={"url": "https://example.com/in/jane-doe"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_non_profile_path_rejected(self, client, make_user):
        headers, _ = make_user()
        res = client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/company/acme"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_missing_slug_rejected(self, client, make_user):
        headers, _ = make_user()
        res = client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/in/"},
            headers=headers,
        )
        assert res.status_code == 400

    def test_stored_on_profile(self, client, make_user):
        headers, _ = make_user()
        client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/in/jane-doe"},
            headers=headers,
        )
        profile = client.get("/profile/me", headers=headers).json()["student_profile"]
        assert profile["linkedin_url"] == "https://www.linkedin.com/in/jane-doe"

    def test_get_linkedin_404_before_linking(self, client, make_user):
        headers, _ = make_user()
        assert client.get("/verification/linkedin", headers=headers).status_code == 404

    def test_get_linkedin_returns_unverified(self, client, make_user):
        headers, _ = make_user()
        client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/in/jane-doe"},
            headers=headers,
        )
        body = client.get("/verification/linkedin", headers=headers).json()
        assert body["verified"] is False

    def test_alumni_forbidden(self, client, make_user):
        headers, _ = make_user(email="alum@example.com", role="alumni")
        res = client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/in/jane-doe"},
            headers=headers,
        )
        assert res.status_code == 403


# ── Combined status ─────────────────────────────────────────────────────────
class TestStatus:
    def test_requires_authentication(self, client):
        assert client.get("/verification/status").status_code == 401

    def test_empty_status(self, client, make_user):
        headers, _ = make_user()
        body = client.get("/verification/status", headers=headers).json()
        assert body["github"] is None
        assert body["linkedin"] is None

    def test_combined_status(self, client, make_user, fake_github):
        headers, _ = make_user()
        _verify(client, headers)
        client.post(
            "/verification/linkedin",
            json={"url": "https://www.linkedin.com/in/jane-doe"},
            headers=headers,
        )
        body = client.get("/verification/status", headers=headers).json()
        assert body["github"]["account"]["username"] == "octocat"
        assert body["linkedin"]["verified"] is False


# ── OpenAPI surface ─────────────────────────────────────────────────────────
def test_openapi_exposes_verification_paths(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/verification/github" in paths
    assert "/verification/github/confirm-skills" in paths
    assert "/verification/linkedin" in paths
    assert "/verification/status" in paths
