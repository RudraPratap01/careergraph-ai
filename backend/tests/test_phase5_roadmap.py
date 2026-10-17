"""
Phase 5B/5C tests — personalized learning roadmap.

Covers:
  * generation, ordering invariant, no duplicates, mastered-skill exclusion
  * persistence across requests and a fresh login
  * progress updates and `next_action`
  * refresh preserving progress
  * ownership isolation between users
  * dependency-inspection and graph-stats endpoints
  * transparent partial roadmaps when dependency data is missing
"""

from app.data.occupations import get_occupation
from app.services.graph_service import DependencyEdge, InMemorySkillGraph
from app.services.roadmap_service import build_roadmap_plan


# ─── Pure planner ─────────────────────────────────────────────────────────────
def test_plan_never_places_prerequisite_after_dependent():
    graph = InMemorySkillGraph()
    occupation = get_occupation("frontend-developer")
    plan = build_roadmap_plan(graph, owned_skills=set(), occupation=occupation)
    steps = plan["steps"]
    position = {s["skill"]: s["position"] for s in steps}

    # Every listed prerequisite must appear earlier in the roadmap.
    for step in steps:
        for pre in step["prerequisites"]:
            assert position[pre] < step["position"], f"{pre} must precede {step['skill']}"

    # And the global graph invariant holds across all steps.
    for edge in graph.edges():
        if edge.prerequisite in position and edge.dependent in position:
            assert position[edge.prerequisite] < position[edge.dependent]


def test_plan_includes_non_required_prerequisite():
    """Python is not required for Frontend, but it is a prerequisite of DSA."""
    graph = InMemorySkillGraph()
    plan = build_roadmap_plan(graph, owned_skills=set(), occupation=get_occupation("frontend-developer"))
    by_skill = {s["skill"]: s for s in plan["steps"]}
    assert "Python" in by_skill
    assert by_skill["Python"]["is_target_skill"] is False
    assert by_skill["Python"]["position"] < by_skill["Data Structures & Algorithms"]["position"]


def test_plan_excludes_mastered_skills_from_steps():
    graph = InMemorySkillGraph()
    plan = build_roadmap_plan(
        graph,
        owned_skills={"JavaScript", "HTML"},
        occupation=get_occupation("frontend-developer"),
    )
    step_skills = {s["skill"] for s in plan["steps"]}
    assert "JavaScript" not in step_skills
    assert "HTML" not in step_skills     # mastered -> never re-taught
    assert set(plan["possessed_skills"]) == {"JavaScript", "HTML"}


def test_plan_has_no_duplicate_steps():
    graph = InMemorySkillGraph()
    plan = build_roadmap_plan(graph, owned_skills=set(), occupation=get_occupation("ml-engineer"))
    skills = [s["skill"] for s in plan["steps"]]
    assert len(skills) == len(set(skills))


def test_plan_is_partial_when_dependency_data_missing():
    empty_graph = InMemorySkillGraph(edges=[])
    plan = build_roadmap_plan(empty_graph, owned_skills=set(), occupation=get_occupation("data-analyst"))
    assert plan["is_partial"] is True
    assert plan["notes"]


def test_plan_handles_cycles_transparently():
    graph = InMemorySkillGraph(edges=[
        DependencyEdge("React", "Next.js", "cycle test", "curated"),
        DependencyEdge("Next.js", "Vue.js", "cycle test", "curated"),
        DependencyEdge("Vue.js", "React", "cycle test", "curated"),
    ])
    occupation = {
        "key": "x", "name": "Cycle Role", "category": "test",
        "required_skills": [
            {"name": "React", "weight": 5},
            {"name": "Next.js", "weight": 3},
            {"name": "Vue.js", "weight": 3},
        ],
        "optional_skills": [],
    }
    plan = build_roadmap_plan(graph, owned_skills=set(), occupation=occupation)
    assert plan["is_partial"] is True
    assert "cycle" in plan["notes"].lower()
    assert len({s["skill"] for s in plan["steps"]}) == 3   # no duplicates, all present


# ─── API: auth & validation ───────────────────────────────────────────────────
def test_roadmap_endpoints_require_auth(client):
    assert client.get("/roadmap").status_code == 401
    assert client.post("/roadmap/generate", json={}).status_code == 401


def test_generate_requires_target_occupation(client, make_user):
    headers, _ = make_user()
    res = client.post("/roadmap/generate", json={}, headers=headers)
    assert res.status_code == 400


def test_generate_unknown_occupation_404(client, make_user):
    headers, _ = make_user()
    res = client.post("/roadmap/generate", json={"occupation": "Astronaut"}, headers=headers)
    assert res.status_code == 404


def test_roadmap_forbidden_for_alumni(client, make_user):
    headers, _ = make_user(email="alum2@example.com", role="alumni")
    res = client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers)
    assert res.status_code == 403


def test_current_roadmap_404_when_none(client, make_user):
    headers, _ = make_user()
    assert client.get("/roadmap", headers=headers).status_code == 404


# ─── API: generation & persistence ────────────────────────────────────────────
def test_generate_roadmap_is_ordered_and_persisted(client, make_user):
    headers, _ = make_user()
    res = client.post("/roadmap/generate", json={"occupation": "Frontend Developer"}, headers=headers)
    assert res.status_code == 201, res.text
    body = res.json()
    roadmap_id = body["id"]

    assert body["occupation_key"] == "frontend-developer"
    assert body["progress"]["total_steps"] == len(body["steps"]) > 0
    assert body["next_action"]
    assert body["disclaimer"]

    position = {s["skill"]: s["position"] for s in body["steps"]}
    for step in body["steps"]:
        for pre in step["prerequisites"]:
            assert position[pre] < step["position"]

    # Persisted under the current roadmap (survives a fresh request).
    current = client.get("/roadmap", headers=headers)
    assert current.status_code == 200
    assert current.json()["id"] == roadmap_id

    # And retrievable by id.
    by_id = client.get(f"/roadmap/{roadmap_id}", headers=headers)
    assert by_id.status_code == 200


def test_roadmap_survives_a_fresh_login(client, make_user):
    headers, payload = make_user(email="persist@example.com")
    client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers)

    # Simulate a brand-new session: log in again to obtain a new token.
    relogin = client.post("/auth/login", json={"email": "persist@example.com", "password": "Password123!"})
    new_headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}
    res = client.get("/roadmap", headers=new_headers)
    assert res.status_code == 200
    assert res.json()["occupation_key"] == "backend-developer"


def test_progress_update_persists(client, make_user):
    headers, _ = make_user()
    created = client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers).json()
    roadmap_id = created["id"]
    first_skill = created["steps"][0]["skill"]

    updated = client.post(
        f"/roadmap/{roadmap_id}/steps",
        json={"skill": first_skill, "state": "completed"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["step"]["status"] == "completed"
    assert updated.json()["progress"]["completed_steps"] == 1

    # Re-fetch and confirm persistence.
    again = client.get(f"/roadmap/{roadmap_id}", headers=headers).json()
    states = {s["skill"]: s["status"] for s in again["steps"]}
    assert states[first_skill] == "completed"
    assert again["progress"]["completed_steps"] == 1
    # next_action should no longer point at the completed step.
    assert first_skill not in (again["next_action"] or "")


def test_progress_update_unknown_skill_404(client, make_user):
    headers, _ = make_user()
    created = client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers).json()
    res = client.post(
        f"/roadmap/{created['id']}/steps",
        json={"skill": "Teleportation", "state": "completed"},
        headers=headers,
    )
    assert res.status_code == 404


def test_progress_update_invalid_state_422(client, make_user):
    headers, _ = make_user()
    created = client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers).json()
    res = client.post(
        f"/roadmap/{created['id']}/steps",
        json={"skill": created["steps"][0]["skill"], "state": "wizard"},
        headers=headers,
    )
    assert res.status_code == 422


def test_refresh_preserves_progress_for_remaining_steps(client, make_user):
    headers, _ = make_user()
    created = client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers).json()
    roadmap_id = created["id"]
    first_skill = created["steps"][0]["skill"]
    client.post(f"/roadmap/{roadmap_id}/steps", json={"skill": first_skill, "state": "completed"}, headers=headers)

    refreshed = client.post("/roadmap/refresh", headers=headers)
    assert refreshed.status_code == 200
    states = {s["skill"]: s["status"] for s in refreshed.json()["steps"]}
    assert states.get(first_skill) == "completed"
    # Old roadmap archived; exactly one active roadmap remains.
    assert client.get("/roadmap", headers=headers).json()["id"] == refreshed.json()["id"]


def test_explanations_endpoint(client, make_user):
    headers, _ = make_user()
    created = client.post("/roadmap/generate", json={"occupation": "Data Analyst"}, headers=headers).json()
    res = client.get(f"/roadmap/{created['id']}/explanations", headers=headers)
    assert res.status_code == 200
    explanations = res.json()
    assert len(explanations) == len(created["steps"])
    assert all(e["reason"] for e in explanations)


# ─── Ownership isolation ──────────────────────────────────────────────────────
def test_users_cannot_access_each_others_roadmaps(client, make_user):
    headers_a, _ = make_user(email="a@example.com")
    headers_b, _ = make_user(email="b@example.com")

    created = client.post("/roadmap/generate", json={"occupation": "Backend Developer"}, headers=headers_a).json()
    roadmap_id = created["id"]
    skill = created["steps"][0]["skill"]

    # B cannot read A's roadmap…
    assert client.get(f"/roadmap/{roadmap_id}", headers=headers_b).status_code == 404
    # …nor its explanations…
    assert client.get(f"/roadmap/{roadmap_id}/explanations", headers=headers_b).status_code == 404
    # …nor mutate its progress.
    forbidden = client.post(
        f"/roadmap/{roadmap_id}/steps",
        json={"skill": skill, "state": "completed"},
        headers=headers_b,
    )
    assert forbidden.status_code == 404
    # B has no current roadmap of their own.
    assert client.get("/roadmap", headers=headers_b).status_code == 404
    # A's roadmap is untouched.
    assert client.get(f"/roadmap/{roadmap_id}", headers=headers_a).status_code == 200


# ─── Graph inspection endpoints ───────────────────────────────────────────────
def test_graph_stats_endpoint(client, make_user):
    headers, _ = make_user()
    res = client.get("/graph/stats", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["backend"] == "memory"
    assert body["edges"] > 0
    assert body["has_cycle"] is False


def test_skill_dependency_endpoint(client, make_user):
    headers, _ = make_user()
    res = client.get("/graph/skills/Deep Learning", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["known"] is True
    names = [p["skill"] for p in body["prerequisites"]]
    assert "Machine Learning" in names

    unknown = client.get("/graph/skills/Teleportation", headers=headers).json()
    assert unknown["known"] is False
