"""
End-to-end critical journeys.

Phases 1-5 (test_full_career_journey):
 1. authenticate a test user           8. calculate skill gaps and readiness
 2. create/update the profile          9. generate a prerequisite-aware roadmap
 3. upload a supported resume         10. verify prerequisite order
 4. extract and review skills         11. update roadmap progress
 5. save reviewed skills              12. reload the roadmap and verify persistence
 6. reload and verify persistence     13. verify another user cannot access
 7. select a target occupation            the first user's private data

Phase 8 (test_phase8_assessment_to_mentorship_journey):
 assess -> evidence a skill -> readiness improves -> rank mentors ->
 request mentorship -> mentor accepts -> capacity enforced -> isolation holds
"""

from app.data.assessments import ASSESSMENTS

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


def test_phase8_assessment_to_mentorship_journey(client, make_user):
    """
    End-to-end Phase 8 journey:

    1. a student with a target role and no skills
    2. takes a curated assessment and scores 100%
    3. confirms the evidenced skill onto their profile
    4. the Phase 4 readiness score improves as a result
    5. mentors are ranked against their remaining gap
    6. the student requests mentorship
    7. the mentor accepts, and their capacity is then enforced
    8. an unrelated user cannot act on someone else's request
    """
    # ── 1. Student and mentor accounts ────────────────────────────────────────
    student_headers, _ = make_user(email="p8_student@example.com")
    assert client.put(
        "/profile/student",
        headers=student_headers,
        json={"target_role": "Backend Developer", "college": "IIT Example"},
    ).status_code == 200

    mentor_headers, mentor_auth = make_user(
        email="p8_mentor@example.com", role="alumni", full_name="Priya Mentor"
    )
    mentor_id = mentor_auth["user_id"]
    assert client.put(
        "/profile/alumni",
        headers=mentor_headers,
        json={
            "company": "Acme",
            "job_title": "Staff Engineer",
            "years_of_experience": 10,
            "college": "IIT Example",
            "expertise_areas": ["Python", "REST APIs", "SQL"],
            "is_available_for_mentoring": True,
            "max_mentees": 1,
        },
    ).status_code == 200

    # ── 2. Take an assessment ─────────────────────────────────────────────────
    catalog = client.get("/assessments", headers=student_headers).json()
    assert any(a["key"] == "python-fundamentals" for a in catalog)

    started = client.post(
        "/assessments/python-fundamentals/start", headers=student_headers
    )
    assert started.status_code == 201, started.text
    attempt_id = started.json()["attempt"]["id"]
    questions = started.json()["questions"]
    # The correct answers are never in the payload the client receives.
    assert "answer_index" not in started.text

    bank = {q["id"]: q for q in ASSESSMENTS["python-fundamentals"]["questions"]}
    submitted = client.post(
        f"/assessments/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {"question_id": q["id"], "chosen_index": bank[q["id"]]["answer_index"]}
                for q in questions
            ]
        },
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["attempt"]["score_percent"] == 100
    assert submitted.json()["suggested_skills"] == ["Python"]

    # ── 3. Confirm the evidenced skill ────────────────────────────────────────
    confirmed = client.post(
        f"/assessments/attempts/{attempt_id}/confirm-skills",
        headers=student_headers,
        json={"skills": ["Python"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    profile_skills = {
        s["name"]: s for s in client.get("/profile/me", headers=student_headers).json()[
            "student_profile"
        ]["skills"]
    }
    assert profile_skills["Python"]["source"] == "assessment"

    # A skill the student did not evidence cannot be claimed.
    assert client.post(
        f"/assessments/attempts/{attempt_id}/confirm-skills",
        headers=student_headers,
        json={"skills": ["Docker"]},
    ).status_code == 400

    # ── 4. Readiness improves deterministically ───────────────────────────────
    after_gap = client.get("/career/gap-analysis", headers=student_headers).json()
    assert "Python" in {s["name"] for s in after_gap["matched_skills"]}
    assert after_gap["readiness_score"] > 0
    # Python is weight 5 out of the role's 40 total importance points.
    assert after_gap["readiness_score"] == 12

    # ── 5. Mentors are ranked against the remaining gap ───────────────────────
    matches = client.get("/mentorship/matches", headers=student_headers).json()
    top = matches["matches"][0]
    assert top["user_id"] == mentor_id
    assert "Python" not in matches["missing_skills"]        # already evidenced
    assert "Python" not in top["overlap_skills"]            # so it is no longer a gap
    assert {"REST APIs", "SQL"} <= set(top["overlap_skills"])
    assert top["match_score"] == sum(f["earned"] for f in top["factors"])
    assert top["remaining_capacity"] == 1

    # ── 6. The student requests mentorship ────────────────────────────────────
    request = client.post(
        "/mentorship/requests",
        headers=student_headers,
        json={"alumni_user_id": mentor_id, "message": "Could you help me with SQL?"},
    )
    assert request.status_code == 201, request.text
    request_body = request.json()
    request_id = request_body["id"]
    assert request_body["status"] == "pending"
    assert request_body["match_score"] == top["match_score"]
    assert request_body["student_name"] == "Test Student"

    # Duplicate pending requests are refused.
    assert client.post(
        "/mentorship/requests",
        headers=student_headers,
        json={"alumni_user_id": mentor_id},
    ).status_code == 409

    # ── 7. The mentor accepts, and capacity is then enforced ──────────────────
    received = client.get("/mentorship/requests", headers=mentor_headers).json()
    assert [r["id"] for r in received] == [request_id]

    accepted = client.post(
        f"/mentorship/requests/{request_id}/accept", headers=mentor_headers
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["request"]["status"] == "accepted"

    # The student now sees the accepted relationship in both views.
    assert client.get("/mentorship/requests", headers=student_headers).json()[0][
        "status"
    ] == "accepted"
    refreshed = client.get("/mentorship/matches", headers=student_headers).json()
    assert refreshed["matches"][0]["request_status"] == "accepted"

    # A second student cannot be accepted: the mentor's limit is 1.
    second_headers, _ = make_user(email="p8_student2@example.com")
    second_request = client.post(
        "/mentorship/requests",
        headers=second_headers,
        json={"alumni_user_id": mentor_id},
    ).json()
    blocked = client.post(
        f"/mentorship/requests/{second_request['id']}/accept", headers=mentor_headers
    )
    assert blocked.status_code == 409

    # ── 8. Unrelated users cannot act on the request ──────────────────────────
    outsider_headers, _ = make_user(email="p8_outsider@example.com", role="alumni")
    assert client.post(
        f"/mentorship/requests/{request_id}/accept", headers=outsider_headers
    ).status_code == 404
    assert client.post(
        f"/mentorship/requests/{request_id}/cancel", headers=outsider_headers
    ).status_code == 404
