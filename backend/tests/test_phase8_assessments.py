"""
Phase 8 — assessments.

Covers the curated question bank's integrity, deterministic grading, the
"answers are never leaked" guarantee, and the rule that a passed attempt is the
*only* thing that can add evidenced skills to a profile.
"""

import json

from app.data.assessments import (
    ASSESSMENTS,
    MIN_QUESTIONS_PER_SKILL,
    PASS_THRESHOLD,
    skills_covered_by_assessments,
    validate_assessment_bank,
)
from app.data.skills_taxonomy import is_known_skill, normalize_skill_name

PYTHON = "python-fundamentals"
BACKEND = "backend-engineering"


def _bank(key):
    return {q["id"]: q for q in ASSESSMENTS[key]["questions"]}


def _wrong_index(question):
    return (question["answer_index"] + 1) % len(question["options"])


def _start(client, headers, key):
    res = client.post(f"/assessments/{key}/start", headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def _answers_for(key, questions, correct=True):
    bank = _bank(key)
    answers = []
    for q in questions:
        source = bank[q["id"]]
        answers.append({
            "question_id": q["id"],
            "chosen_index": source["answer_index"] if correct else _wrong_index(source),
        })
    return answers


def _take(client, headers, key, correct=True):
    """Starts and submits an assessment. Returns (attempt_id, submit_response)."""
    started = _start(client, headers, key)
    answers = _answers_for(key, started["questions"], correct=correct)
    res = client.post(
        f"/assessments/attempts/{started['attempt']['id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    return started["attempt"]["id"], res


# ── Bank integrity ────────────────────────────────────────────────────────────
class TestAssessmentBank:
    def test_bank_is_valid(self):
        assert validate_assessment_bank() == []

    def test_every_skill_has_enough_questions(self):
        for key, data in ASSESSMENTS.items():
            for skill in data["skills"]:
                tagged = [q for q in data["questions"] if q["skill"] == skill]
                assert len(tagged) >= MIN_QUESTIONS_PER_SKILL, (key, skill)

    def test_covered_skills_are_canonical(self):
        covered = skills_covered_by_assessments()
        assert covered
        for skill in covered:
            assert is_known_skill(skill)
            assert normalize_skill_name(skill) == skill

    def test_question_ids_are_globally_unique(self):
        ids = [q["id"] for data in ASSESSMENTS.values() for q in data["questions"]]
        assert len(ids) == len(set(ids))

    def test_answers_are_within_range(self):
        for data in ASSESSMENTS.values():
            for q in data["questions"]:
                assert 0 <= q["answer_index"] < len(q["options"])


# ── Catalog ───────────────────────────────────────────────────────────────────
class TestAssessmentCatalog:
    def test_lists_assessments(self, client, make_user):
        headers, _ = make_user(email="a_cat@example.com")
        res = client.get("/assessments", headers=headers)
        assert res.status_code == 200, res.text
        body = res.json()
        assert len(body) == len(ASSESSMENTS)
        assert body == sorted(body, key=lambda a: a["name"])
        first = body[0]
        assert first["question_count"] == len(ASSESSMENTS[first["key"]]["questions"])
        assert first["pass_threshold"] == PASS_THRESHOLD
        assert first["source"] == "curated"

    def test_detail_never_leaks_answers(self, client, make_user):
        headers, _ = make_user(email="a_det@example.com")
        res = client.get(f"/assessments/{PYTHON}", headers=headers)
        assert res.status_code == 200, res.text
        raw = json.dumps(res.json())
        assert "answer_index" not in raw
        assert "correct_index" not in raw
        for question in res.json()["questions"]:
            assert set(question.keys()) == {"id", "skill", "difficulty", "prompt", "options"}

    def test_unknown_assessment_is_404(self, client, make_user):
        headers, _ = make_user(email="a_unk@example.com")
        assert client.get("/assessments/does-not-exist", headers=headers).status_code == 404

    def test_requires_auth(self, client):
        assert client.get("/assessments").status_code == 401
        assert client.get(f"/assessments/{PYTHON}").status_code == 401
        assert client.post(f"/assessments/{PYTHON}/start").status_code == 401

    def test_alumni_cannot_take_assessments(self, client, make_user):
        headers, _ = make_user(email="a_alum@example.com", role="alumni")
        assert client.get("/assessments", headers=headers).status_code == 403
        assert client.post(f"/assessments/{PYTHON}/start", headers=headers).status_code == 403

    def test_start_unknown_assessment_is_404(self, client, make_user):
        headers, _ = make_user(email="a_st@example.com")
        assert client.post("/assessments/nope/start", headers=headers).status_code == 404


# ── Grading ───────────────────────────────────────────────────────────────────
class TestGrading:
    def test_all_correct_scores_100_and_passes_every_skill(self, client, make_user):
        headers, _ = make_user(email="g_all@example.com")
        _, res = _take(client, headers, BACKEND)
        body = res.json()
        assert body["attempt"]["score_percent"] == 100
        assert body["attempt"]["passed"] is True
        assert body["attempt"]["correct_count"] == body["attempt"]["total_count"]
        assert set(body["suggested_skills"]) == set(ASSESSMENTS[BACKEND]["skills"])
        assert body["disclaimer"]

    def test_all_wrong_scores_zero_and_suggests_nothing(self, client, make_user):
        headers, _ = make_user(email="g_none@example.com")
        _, res = _take(client, headers, BACKEND, correct=False)
        body = res.json()
        assert body["attempt"]["score_percent"] == 0
        assert body["attempt"]["passed"] is False
        assert body["suggested_skills"] == []
        for skill in body["attempt"]["skills"]:
            assert skill["passed"] is False
            assert skill["eligible_for_evidence"] is False

    def test_unanswered_questions_count_as_incorrect(self, client, make_user):
        headers, _ = make_user(email="g_skip@example.com")
        started = _start(client, headers, PYTHON)
        res = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/submit",
            json={"answers": []},
            headers=headers,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["attempt"]["score_percent"] == 0
        assert all(r["chosen_index"] is None for r in body["results"])

    def test_partial_pass_is_not_evidence(self, client, make_user):
        """One of two questions correct is 50% — below the evidence threshold."""
        headers, _ = make_user(email="g_part@example.com")
        started = _start(client, headers, PYTHON)
        bank = _bank(PYTHON)
        questions = started["questions"]
        answers = [
            {"question_id": questions[0]["id"], "chosen_index": bank[questions[0]["id"]]["answer_index"]},
            {"question_id": questions[1]["id"], "chosen_index": _wrong_index(bank[questions[1]["id"]])},
        ]
        res = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/submit",
            json={"answers": answers},
            headers=headers,
        )
        body = res.json()
        assert body["attempt"]["score_percent"] == 50
        assert body["suggested_skills"] == []
        skill = body["attempt"]["skills"][0]
        assert skill["score_percent"] == 50
        assert skill["passed"] is False

    def test_results_include_explanations_and_correct_answers(self, client, make_user):
        headers, _ = make_user(email="g_exp@example.com")
        _, res = _take(client, headers, PYTHON)
        for result in res.json()["results"]:
            assert result["explanation"]
            assert isinstance(result["correct_index"], int)

    def test_duplicate_answer_is_rejected(self, client, make_user):
        headers, _ = make_user(email="g_dup@example.com")
        started = _start(client, headers, PYTHON)
        qid = started["questions"][0]["id"]
        res = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/submit",
            json={"answers": [
                {"question_id": qid, "chosen_index": 0},
                {"question_id": qid, "chosen_index": 1},
            ]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_out_of_range_answer_is_rejected(self, client, make_user):
        headers, _ = make_user(email="g_range@example.com")
        started = _start(client, headers, PYTHON)
        res = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/submit",
            json={"answers": [{"question_id": started["questions"][0]["id"], "chosen_index": 99}]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_resubmitting_an_attempt_is_a_conflict(self, client, make_user):
        headers, _ = make_user(email="g_resub@example.com")
        attempt_id, _ = _take(client, headers, PYTHON)
        res = client.post(
            f"/assessments/attempts/{attempt_id}/submit",
            json={"answers": []},
            headers=headers,
        )
        assert res.status_code == 409

    def test_grading_is_deterministic(self, client, make_user):
        headers, _ = make_user(email="g_det@example.com")
        _, first = _take(client, headers, BACKEND)
        _, second = _take(client, headers, BACKEND)
        assert first.json()["attempt"]["score_percent"] == second.json()["attempt"]["score_percent"]
        assert first.json()["suggested_skills"] == second.json()["suggested_skills"]


# ── Ownership ─────────────────────────────────────────────────────────────────
class TestAttemptOwnership:
    def test_cannot_submit_someone_elses_attempt(self, client, make_user):
        headers_a, _ = make_user(email="own_a@example.com")
        headers_b, _ = make_user(email="own_b@example.com")
        started = _start(client, headers_a, PYTHON)

        res = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/submit",
            json={"answers": []},
            headers=headers_b,
        )
        assert res.status_code == 404

        # …and the original owner can still submit it afterwards.
        ok = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/submit",
            json={"answers": []},
            headers=headers_a,
        )
        assert ok.status_code == 200

    def test_history_is_owner_scoped_and_newest_first(self, client, make_user):
        headers_a, _ = make_user(email="hist_a@example.com")
        headers_b, _ = make_user(email="hist_b@example.com")

        _take(client, headers_a, PYTHON)
        _take(client, headers_a, BACKEND)
        _take(client, headers_b, PYTHON)

        mine = client.get("/assessments/attempts", headers=headers_a).json()
        assert len(mine) == 2
        assert {a["assessment_key"] for a in mine} == {PYTHON, BACKEND}
        assert mine[0]["started_at"] >= mine[1]["started_at"]

        theirs = client.get("/assessments/attempts", headers=headers_b).json()
        assert len(theirs) == 1

    def test_unknown_attempt_is_404(self, client, make_user):
        headers, _ = make_user(email="own_404@example.com")
        assert client.post(
            "/assessments/attempts/999999/submit", json={"answers": []}, headers=headers
        ).status_code == 404
        assert client.post(
            "/assessments/attempts/999999/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        ).status_code == 404


# ── Evidenced skills ──────────────────────────────────────────────────────────
class TestConfirmSkills:
    def test_confirming_a_passed_skill_adds_it_to_the_profile(self, client, make_user):
        headers, _ = make_user(email="cs_add@example.com")
        attempt_id, _ = _take(client, headers, PYTHON)

        res = client.post(
            f"/assessments/attempts/{attempt_id}/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )
        assert res.status_code == 200, res.text
        assert res.json()["added"] == ["Python"]

        profile = client.get("/profile/me", headers=headers).json()
        skills = {s["name"]: s for s in profile["student_profile"]["skills"]}
        assert "Python" in skills
        assert skills["Python"]["source"] == "assessment"

    def test_cannot_confirm_a_skill_that_was_not_passed(self, client, make_user):
        headers, _ = make_user(email="cs_bad@example.com")
        attempt_id, _ = _take(client, headers, PYTHON)

        res = client.post(
            f"/assessments/attempts/{attempt_id}/confirm-skills",
            json={"skills": ["SQL"]},
            headers=headers,
        )
        assert res.status_code == 400
        assert "SQL" in res.json()["detail"]

        profile = client.get("/profile/me", headers=headers).json()
        assert profile["student_profile"] is None or profile["student_profile"]["skills"] == []

    def test_cannot_confirm_an_unknown_skill_name(self, client, make_user):
        headers, _ = make_user(email="cs_unknown@example.com")
        attempt_id, _ = _take(client, headers, PYTHON)
        res = client.post(
            f"/assessments/attempts/{attempt_id}/confirm-skills",
            json={"skills": ["Teleportation"]},
            headers=headers,
        )
        assert res.status_code == 400

    def test_confirm_preserves_existing_level_and_marks_evidence(self, client, make_user):
        headers, _ = make_user(email="cs_merge@example.com")
        client.put(
            "/profile/student",
            json={
                "target_role": "Backend Developer",
                "skills": [{"name": "Python", "level": "advanced"}],
            },
            headers=headers,
        )

        attempt_id, _ = _take(client, headers, PYTHON)
        res = client.post(
            f"/assessments/attempts/{attempt_id}/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )
        assert res.status_code == 200, res.text
        assert res.json()["added"] == []
        assert res.json()["already_present"] == ["Python"]

        profile = client.get("/profile/me", headers=headers).json()
        skills = {s["name"]: s for s in profile["student_profile"]["skills"]}
        assert skills["Python"]["level"] == "advanced"      # level not clobbered
        assert skills["Python"]["source"] == "assessment"   # now evidenced

    def test_confirm_requires_a_submitted_attempt(self, client, make_user):
        headers, _ = make_user(email="cs_open@example.com")
        started = _start(client, headers, PYTHON)
        res = client.post(
            f"/assessments/attempts/{started['attempt']['id']}/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )
        assert res.status_code == 409

    def test_evidence_feeds_the_readiness_score(self, client, make_user):
        """A confirmed skill must show up in the Phase 4 gap analysis."""
        headers, _ = make_user(email="cs_gap@example.com")
        client.put(
            "/profile/student",
            json={"target_role": "Backend Developer"},
            headers=headers,
        )
        before = client.get(
            "/career/gap-analysis", params={"occupation": "Backend Developer"}, headers=headers
        ).json()
        assert "Python" in [s["name"] for s in before["missing_skills"]]

        attempt_id, _ = _take(client, headers, PYTHON)
        client.post(
            f"/assessments/attempts/{attempt_id}/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )

        after = client.get(
            "/career/gap-analysis", params={"occupation": "Backend Developer"}, headers=headers
        ).json()
        assert "Python" in [s["name"] for s in after["matched_skills"]]
        assert after["readiness_score"] > before["readiness_score"]

    def test_resume_review_does_not_discard_evidenced_skills(self, client, make_user):
        """
        Phase 3 confirmation replaces the skill list; it must not delete skills
        that a passed assessment evidenced.
        """
        headers, _ = make_user(email="cs_resume@example.com")
        attempt_id, _ = _take(client, headers, PYTHON)
        client.post(
            f"/assessments/attempts/{attempt_id}/confirm-skills",
            json={"skills": ["Python"]},
            headers=headers,
        )

        client.post(
            "/resume/confirm-skills",
            json={"skills": [{"name": "Docker", "level": "beginner"}]},
            headers=headers,
        )

        profile = client.get("/profile/me", headers=headers).json()
        skills = {s["name"]: s for s in profile["student_profile"]["skills"]}
        assert skills["Python"]["source"] == "assessment"
        assert skills["Docker"]["source"] == "resume"
