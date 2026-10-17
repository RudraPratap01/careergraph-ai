"""
End-to-end critical journey (Phases 1–5).

1. authenticate a test user           8. calculate skill gaps and readiness
2. create/update the profile          9. generate a prerequisite-aware roadmap
3. upload a supported resume         10. verify prerequisite order
4. extract and review skills         11. update roadmap progress
5. save reviewed skills              12. reload the roadmap and verify persistence
6. reload and verify persistence     13. verify another user cannot access
7. select a target occupation            the first user's private data
"""

RESUME_TEXT = """
Aarav Sharma
Frontend Developer

SKILLS
JavaScript, HTML, CSS, React, Git, TypeScript, REST APIs

PROJECTS
Built a React dashboard consuming REST APIs with JavaScript and TypeScript.
Developed responsive layouts using HTML and CSS.
Maintained source control with Git.

EDUCATION
B.Tech Computer Science & Engineering, 2026
""".strip()


def test_full_career_journey(client, make_user):
    # ── 1. Authenticate ───────────────────────────────────────────────────────
    headers, auth = make_user(email="journey@example.com")
    assert client.get("/auth/me", headers=headers).status_code == 200

    # ── 2. Create / update the profile ────────────────────────────────────────
    profile = client.put(
        "/profile/student",
        headers=headers,
        json={
            "college": "IIT Example",
            "degree": "B.Tech Computer Science & Engineering",
            "graduation_year": 2026,
            "target_role": "Frontend Developer",
            "skills": [{"name": "Python", "level": "beginner"}],
        },
    )
    assert profile.status_code == 200

    # ── 3. Upload a supported resume ──────────────────────────────────────────
    upload = client.post(
        "/resume/upload",
        headers=headers,
        files={"file": ("resume.txt", RESUME_TEXT.encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    upload_body = upload.json()
    resume_id = upload_body["resume_id"]
    extracted = {s["name"] for s in upload_body["extracted_skills"]}
    assert {"JavaScript", "HTML", "CSS", "React"} <= extracted

    # ── 4. Review extracted skills (student keeps a subset) ───────────────────
    kept = [
        {"name": "JavaScript", "level": "advanced", "category": "Languages"},
        {"name": "HTML", "level": "intermediate", "category": "Languages"},
        {"name": "CSS", "level": "intermediate", "category": "Languages"},
        {"name": "React", "level": "intermediate", "category": "Frameworks & Libraries"},
        {"name": "Custom Tooling", "level": "beginner"},   # manually added
    ]

    # ── 5. Save reviewed skills (syncs to the profile) ────────────────────────
    confirm = client.post(
        "/resume/confirm-skills",
        headers=headers,
        json={"resume_id": resume_id, "skills": kept},
    )
    assert confirm.status_code == 200
    assert confirm.json()["total_confirmed_skills"] == len(kept)

    # ── 6. Reload and verify persistence ──────────────────────────────────────
    me = client.get("/profile/me", headers=headers).json()
    saved = {s["name"] for s in me["student_profile"]["skills"]}
    assert {"JavaScript", "HTML", "CSS", "React", "Custom Tooling"} == saved
    # Skills the student removed are gone (they do not reappear on reload).
    assert "TypeScript" not in saved
    assert "Git" not in saved

    # ── 7. Target occupation is selected ──────────────────────────────────────
    assert me["student_profile"]["target_role"] == "Frontend Developer"

    # ── 8. Skill gaps and readiness ───────────────────────────────────────────
    gap = client.get("/career/gap-analysis", headers=headers)
    assert gap.status_code == 200
    gap_body = gap.json()
    assert gap_body["occupation_key"] == "frontend-developer"
    assert 0 < gap_body["readiness_score"] < 100
    matched = {m["name"] for m in gap_body["matched_skills"]}
    assert {"JavaScript", "HTML", "CSS", "React"} <= matched
    assert gap_body["disclaimer"]

    # ── 9. Generate a prerequisite-aware roadmap ──────────────────────────────
    roadmap_res = client.post("/roadmap/generate", headers=headers, json={})
    assert roadmap_res.status_code == 201, roadmap_res.text
    roadmap = roadmap_res.json()
    roadmap_id = roadmap["id"]
    assert roadmap["progress"]["total_steps"] > 0
    # Mastered skills are reported, not re-taught.
    assert {"JavaScript", "HTML", "CSS", "React"} <= set(roadmap["possessed_skills"])
    step_skills = [s["skill"] for s in roadmap["steps"]]
    assert "JavaScript" not in step_skills

    # ── 10. Verify prerequisite order ─────────────────────────────────────────
    position = {s["skill"]: s["position"] for s in roadmap["steps"]}
    for step in roadmap["steps"]:
        for pre in step["prerequisites"]:
            assert position[pre] < step["position"]
    assert len(step_skills) == len(set(step_skills))   # no duplicates

    # ── 11. Update progress ───────────────────────────────────────────────────
    first = roadmap["steps"][0]["skill"]
    update = client.post(
        f"/roadmap/{roadmap_id}/steps",
        headers=headers,
        json={"skill": first, "state": "completed"},
    )
    assert update.status_code == 200
    assert update.json()["progress"]["completed_steps"] == 1

    # ── 12. Reload and verify persistence ─────────────────────────────────────
    reloaded = client.get(f"/roadmap/{roadmap_id}", headers=headers).json()
    states = {s["skill"]: s["status"] for s in reloaded["steps"]}
    assert states[first] == "completed"
    assert reloaded["progress"]["completed_steps"] == 1

    # ── 13. Another user cannot access the first user's private data ──────────
    other_headers, _ = make_user(email="intruder@example.com")
    assert client.get(f"/roadmap/{roadmap_id}", headers=other_headers).status_code == 404
    assert client.get(f"/roadmap/{roadmap_id}/explanations", headers=other_headers).status_code == 404
    assert client.post(
        f"/roadmap/{roadmap_id}/steps",
        headers=other_headers,
        json={"skill": first, "state": "completed"},
    ).status_code == 404
    # The intruder sees their own (empty) state, not the victim's.
    assert client.get("/roadmap", headers=other_headers).status_code == 404
    assert client.get(f"/profile/{auth['user_id']}", headers=other_headers).status_code == 200  # public view only
