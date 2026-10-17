"""
Phase 4 tests — Skill gaps & career readiness.

Covers:
  * taxonomy / catalog integrity (no collisions, canonical references)
  * deterministic, explainable readiness scoring
  * alias + duplicate normalization
  * unknown skills and empty profiles
  * occupation resolution and error handling
  * API authorization and ownership
"""

import pytest

from app.data.occupations import get_occupation, list_occupations, resolve_occupation_key, validate_catalog
from app.data.skills_taxonomy import (
    TAXONOMY,
    normalize_skill_name,
    _build_alias_index,
)
from app.data.skill_prerequisites import validate_prerequisites
from app.services.skill_gap_service import (
    analyze_skill_gap,
    compute_readiness,
    normalize_user_skills,
    readiness_band,
)


# ─── Data integrity ───────────────────────────────────────────────────────────
def test_catalog_and_prerequisites_are_valid():
    assert validate_catalog() == []
    assert validate_prerequisites() == []


def test_alias_index_has_no_collisions():
    """Re-building the alias index must not drop entries (i.e. no collisions)."""
    rebuilt = _build_alias_index()
    expected = sum(
        1
        + len(cfg.get("aliases", []))
        + len(cfg.get("case_sensitive_aliases", []))
        for cfg in TAXONOMY.values()
    )
    # Each surface form maps to exactly one canonical skill; the index is keyed
    # by lowercase surface form, so a collision would make it smaller.
    unique_forms = {
        name.strip().lower()
        for name in TAXONOMY
    }
    for cfg in TAXONOMY.values():
        for alias in cfg.get("aliases", []) + cfg.get("case_sensitive_aliases", []):
            unique_forms.add(alias.strip().lower())
    assert len(rebuilt) == len(unique_forms)
    assert expected >= len(rebuilt)  # sanity: index smaller or equal to raw count


def test_occupations_all_resolve_to_known_skills():
    for summary in list_occupations():
        occ = get_occupation(summary["key"])
        assert occ is not None
        for entry in occ["required_skills"]:
            assert normalize_skill_name(entry["name"]) == entry["name"]


# ─── Normalization helpers ────────────────────────────────────────────────────
def test_normalize_user_skills_alias_and_dedup():
    known, unknown = normalize_user_skills([
        {"name": "postgres", "level": "beginner"},
        {"name": "PostgreSQL", "level": "advanced"},
        {"name": "js", "level": "intermediate"},
        {"name": "JavaScript", "level": "beginner"},
    ])
    levels = {k["name"]: k["level"] for k in known}
    # Duplicates collapse, highest level wins.
    assert levels["PostgreSQL"] == "advanced"
    assert levels["JavaScript"] == "intermediate"
    assert unknown == []


def test_normalize_user_skills_reports_unknown():
    known, unknown = normalize_user_skills(["Rust", "Underwater Basket Weaving"])
    assert any(k["name"] == "Rust" for k in known)
    assert unknown == ["Underwater Basket Weaving"]


def test_normalize_user_skills_handles_bad_input():
    known, unknown = normalize_user_skills([None, "", "   ", {"level": "advanced"}])
    assert known == []
    assert unknown == []


# ─── Scoring ──────────────────────────────────────────────────────────────────
def test_compute_readiness_is_exact_weighted_coverage():
    assert compute_readiness(0, 40) == 0
    assert compute_readiness(40, 40) == 100
    assert compute_readiness(10, 40) == 25
    assert compute_readiness(1, 3) == 33
    assert compute_readiness(5, 0) == 0  # defensive: no division by zero


def test_readiness_band_thresholds():
    assert readiness_band(0) == "Emerging"
    assert readiness_band(40) == "Developing"
    assert readiness_band(65) == "Proficient"
    assert readiness_band(85) == "Role-ready"


def test_readiness_is_deterministic_and_explainable():
    skills = [{"name": "Python", "level": "advanced"}, {"name": "SQL", "level": "beginner"}]
    first = analyze_skill_gap(skills, "Backend Developer")
    second = analyze_skill_gap(skills, "Backend Developer")
    assert first.readiness_score == second.readiness_score
    assert first.contributions == second.contributions
    # Weighted coverage of Backend Developer required skills:
    # Python(5) + SQL(5) = 10 of 40 total importance -> 25%.
    assert first.readiness_score == 25
    assert first.readiness_band == "Emerging"
    assert first.disclaimer  # explains that it is not a hiring probability
    assert "not a probability" in first.disclaimer.lower()
    assert first.matched_count == 2


def test_readiness_full_coverage_scores_100():
    occ = get_occupation("frontend-developer")
    skills = [r["name"] for r in occ["required_skills"]]
    result = analyze_skill_gap(skills, "frontend-developer")
    assert result.readiness_score == 100
    assert result.missing_skills == []
    assert result.readiness_band == "Role-ready"


def test_empty_profile_yields_zero_and_lists_all_missing():
    result = analyze_skill_gap([], "Data Analyst")
    assert result.readiness_score == 0
    assert result.matched_count == 0
    assert len(result.missing_skills) == result.required_count
    assert result.matched_skills == []


def test_optionals_do_not_affect_score():
    occ = get_occupation("backend-developer")
    required_only = [r["name"] for r in occ["required_skills"]]
    with_bonus = required_only + [o["name"] for o in occ["optional_skills"]]
    assert analyze_skill_gap(required_only, "backend-developer").readiness_score == 100
    assert analyze_skill_gap(with_bonus, "backend-developer").readiness_score == 100
    assert len(analyze_skill_gap(with_bonus, "backend-developer").bonus_skills) > 0


def test_unknown_skills_are_reported_not_dropped_silently():
    result = analyze_skill_gap(["Python", "Teleportation"], "Backend Developer")
    assert result.unknown_skills == ["Teleportation"]


def test_unknown_occupation_returns_none():
    assert analyze_skill_gap(["Python"], "Astronaut") is None
    assert analyze_skill_gap(["Python"], None) is None


@pytest.mark.parametrize("alias", ["backend", "Backend Developer", "backend-developer", "Back End Developer"])
def test_occupation_aliases_resolve(alias):
    assert resolve_occupation_key(alias) == "backend-developer"


# ─── API ──────────────────────────────────────────────────────────────────────
def test_occupations_require_authentication(client):
    assert client.get("/career/occupations").status_code == 401


def test_list_and_detail_endpoints(client, make_user):
    headers, _ = make_user()

    listed = client.get("/career/occupations", headers=headers)
    assert listed.status_code == 200
    keys = [o["key"] for o in listed.json()]
    assert "backend-developer" in keys

    detail = client.get("/career/occupations/backend-developer", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert "Python" in body["required_skills"]
    assert len(body["required_skills"]) == body["required_skill_count"]

    assert client.get("/career/occupations/nope", headers=headers).status_code == 404


def test_gap_analysis_requires_target_role(client, make_user):
    headers, _ = make_user()
    res = client.get("/career/gap-analysis", headers=headers)
    assert res.status_code == 400
    assert "target occupation" in res.json()["detail"].lower()


def test_gap_analysis_uses_profile_target_role(client, make_user):
    headers, _ = make_user()
    client.put(
        "/profile/student",
        headers=headers,
        json={"target_role": "Backend Developer", "skills": [{"name": "Python", "level": "advanced"}]},
    )
    res = client.get("/career/gap-analysis", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["occupation_key"] == "backend-developer"
    assert body["target_source"] == "profile.target_role"
    assert body["readiness_score"] > 0


def test_gap_analysis_explicit_occupation_overrides_profile(client, make_user):
    headers, _ = make_user()
    client.put(
        "/profile/student",
        headers=headers,
        json={"target_role": "Backend Developer", "skills": [{"name": "React", "level": "advanced"}]},
    )
    res = client.get("/career/gap-analysis?occupation=Frontend Developer", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["occupation_key"] == "frontend-developer"
    assert body["target_source"] == "request"
    assert any(m["name"] == "React" for m in body["matched_skills"])


def test_gap_analysis_unknown_occupation_404(client, make_user):
    headers, _ = make_user()
    res = client.get("/career/gap-analysis?occupation=Astronaut", headers=headers)
    assert res.status_code == 404


def test_gap_analysis_forbidden_for_alumni(client, make_user):
    headers, _ = make_user(email="alum@example.com", role="alumni")
    res = client.get("/career/gap-analysis?occupation=Backend Developer", headers=headers)
    assert res.status_code == 403


def test_confirmed_resume_skills_feed_gap_analysis(client, make_user):
    """End-to-end: confirmed skills sync to the profile and drive the score."""
    headers, _ = make_user()
    client.post(
        "/resume/confirm-skills",
        headers=headers,
        json={
            "skills": [
                {"name": "Python", "level": "advanced", "category": "Languages"},
                {"name": "SQL", "level": "intermediate", "category": "Languages"},
                {"name": "Git", "level": "intermediate"},
            ]
        },
    )
    res = client.get("/career/gap-analysis?occupation=Backend Developer", headers=headers)
    assert res.status_code == 200
    matched = {m["name"] for m in res.json()["matched_skills"]}
    assert {"Python", "SQL", "Git"} <= matched


# ─── Contract with the frontend presets ───────────────────────────────────────
def test_frontend_role_presets_all_resolve_to_catalog_occupations():
    """
    The role shortcuts offered by ProfilePage.jsx must resolve in the backend
    catalog, so a student selecting one always gets a working gap analysis.
    """
    frontend_roles = [
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Data Analyst",
        "ML Engineer",
        "Cybersecurity Analyst",
        "Cloud / DevOps Engineer",
    ]
    for role in frontend_roles:
        assert resolve_occupation_key(role) is not None, f"{role} does not resolve"


def test_frontend_skill_presets_are_canonical():
    """The skill shortcuts offered by ProfilePage.jsx must be canonical names."""
    frontend_skills = [
        "Python", "JavaScript", "TypeScript", "React", "FastAPI",
        "SQL", "PostgreSQL", "Docker", "Git", "Linux", "Pandas", "Node.js",
    ]
    for skill in frontend_skills:
        assert normalize_skill_name(skill) == skill, f"{skill} is not canonical"
