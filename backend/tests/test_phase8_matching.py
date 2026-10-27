"""
Phase 8 — alumni matching & mentorship requests.

Covers the deterministic scoring function directly, the ranking API, and every
authorization/capacity rule of the request lifecycle.
"""

from app.data.occupations import get_occupation
from app.models.profile import AlumniProfile
from app.services.matching_service import (
    EXPERIENCE_CAP_YEARS,
    W_AVAILABILITY,
    W_CAPACITY,
    W_EXPERIENCE,
    W_GAP_OVERLAP,
    W_SAME_COLLEGE,
    compute_match,
    match_band,
    mentor_covers,
    mentor_skill_index,
)


def mentor(**overrides) -> AlumniProfile:
    """An in-memory AlumniProfile (never persisted) for scoring tests."""
    defaults = dict(
        company="Acme",
        job_title="Software Engineer",
        years_of_experience=5,
        college="IIT Delhi",
        expertise_areas=["Python", "SQL"],
        is_available_for_mentoring=True,
        max_mentees=3,
    )
    defaults.update(overrides)
    return AlumniProfile(**defaults)


def make_mentor_user(client, make_user, email, full_name="Mentor", **profile_fields):
    headers, payload = make_user(email=email, role="alumni", full_name=full_name)
    body = {
        "company": "Acme",
        "job_title": "Software Engineer",
        "years_of_experience": 5,
        "college": "IIT Delhi",
        "expertise_areas": ["Python", "SQL"],
        "is_available_for_mentoring": True,
        "max_mentees": 3,
    }
    body.update(profile_fields)
    res = client.put("/profile/alumni", json=body, headers=headers)
    assert res.status_code == 200, res.text
    return headers, payload["user_id"]


def make_student(client, make_user, email, *, target_role=None, skills=None, college=None):
    headers, payload = make_user(email=email, full_name="Student")
    body = {}
    if target_role:
        body["target_role"] = target_role
    if skills is not None:
        body["skills"] = skills
    if college:
        body["college"] = college
    if body:
        assert client.put("/profile/student", json=body, headers=headers).status_code == 200
    return headers, payload["user_id"]


# ── Pure scoring ──────────────────────────────────────────────────────────────
class TestMatchScoring:
    def test_score_is_exactly_the_sum_of_its_factors(self):
        score, overlap, factors = compute_match(
            mentor(expertise_areas=["Python", "SQL"], years_of_experience=3),
            student_college="IIT Delhi",
            required_skills=["Python", "SQL"],
            missing_skills=["Python", "SQL"],
            target_occupation="Backend Developer",
            accepted_mentees=1,
        )
        assert score == sum(f.earned for f in factors)
        assert all(0 <= f.earned <= f.weight for f in factors)
        assert score <= 100
        assert sorted(overlap) == ["Python", "SQL"]

    def test_ideal_match_scores_the_full_weight(self):
        score, _, factors = compute_match(
            mentor(expertise_areas=["Python", "SQL"], years_of_experience=EXPERIENCE_CAP_YEARS),
            student_college="IIT Delhi",
            required_skills=["Python", "SQL"],
            missing_skills=["Python", "SQL"],
            target_occupation="Backend Developer",
            accepted_mentees=0,
        )
        assert score == (
            W_GAP_OVERLAP + W_SAME_COLLEGE + W_EXPERIENCE + W_AVAILABILITY + W_CAPACITY
        ) == 100
        assert match_band(score) == "Strong"

    def test_no_target_role_disables_only_the_overlap_factor(self):
        score, overlap, factors = compute_match(
            mentor(years_of_experience=EXPERIENCE_CAP_YEARS),
            student_college="IIT Delhi",
            required_skills=[],
            missing_skills=[],
            target_occupation=None,
            accepted_mentees=0,
        )
        gap = next(f for f in factors if f.key == "gap_overlap")
        assert gap.earned == 0
        assert "target role" in gap.detail
        assert overlap == []
        assert score == W_SAME_COLLEGE + W_EXPERIENCE + W_AVAILABILITY + W_CAPACITY

    def test_experience_is_partial_below_the_cap(self):
        _, _, factors = compute_match(
            mentor(years_of_experience=5),
            student_college=None,
            required_skills=[],
            missing_skills=[],
            target_occupation=None,
            accepted_mentees=0,
        )
        experience = next(f for f in factors if f.key == "experience")
        assert experience.earned == round(W_EXPERIENCE * 5 / EXPERIENCE_CAP_YEARS)
        assert experience.earned < W_EXPERIENCE

    def test_full_capacity_awards_no_capacity_points(self):
        _, _, factors = compute_match(
            mentor(max_mentees=2),
            student_college=None,
            required_skills=["Python"],
            missing_skills=["Python"],
            target_occupation="Backend Developer",
            accepted_mentees=2,
        )
        capacity = next(f for f in factors if f.key == "capacity")
        assert capacity.earned == 0

    def test_zero_capacity_capability_is_handled(self):
        _, _, factors = compute_match(
            mentor(max_mentees=0),
            student_college=None,
            required_skills=[],
            missing_skills=[],
            target_occupation=None,
            accepted_mentees=0,
        )
        capacity = next(f for f in factors if f.key == "capacity")
        assert capacity.earned == 0
        assert "capacity" in capacity.detail.lower()

    def test_unavailable_mentor_loses_availability_points(self):
        _, _, factors = compute_match(
            mentor(is_available_for_mentoring=False),
            student_college=None,
            required_skills=[],
            missing_skills=[],
            target_occupation=None,
            accepted_mentees=0,
        )
        availability = next(f for f in factors if f.key == "availability")
        assert availability.earned == 0

    def test_different_college_awards_no_college_points(self):
        _, _, factors = compute_match(
            mentor(college="Some Other College"),
            student_college="IIT Delhi",
            required_skills=[],
            missing_skills=[],
            target_occupation=None,
            accepted_mentees=0,
        )
        college = next(f for f in factors if f.key == "same_college")
        assert college.earned == 0

    def test_experience_is_capped(self):
        _, _, at_cap = compute_match(
            mentor(years_of_experience=EXPERIENCE_CAP_YEARS),
            student_college=None, required_skills=[], missing_skills=[],
            target_occupation=None, accepted_mentees=0,
        )
        _, _, above_cap = compute_match(
            mentor(years_of_experience=EXPERIENCE_CAP_YEARS + 25),
            student_college=None, required_skills=[], missing_skills=[],
            target_occupation=None, accepted_mentees=0,
        )
        cap = next(f for f in at_cap if f.key == "experience").earned
        over = next(f for f in above_cap if f.key == "experience").earned
        assert cap == over == W_EXPERIENCE

    def test_scoring_is_deterministic(self):
        args = dict(
            student_college="IIT Delhi",
            required_skills=["Python", "SQL"],
            missing_skills=["Python"],
            target_occupation="Backend Developer",
            accepted_mentees=1,
        )
        first = compute_match(mentor(), **args)
        second = compute_match(mentor(), **args)
        assert first[0] == second[0]
        assert [f.model_dump() for f in first[2]] == [f.model_dump() for f in second[2]]

    def test_match_bands(self):
        assert match_band(100) == "Strong"
        assert match_band(60) == "Good"
        assert match_band(40) == "Fair"
        assert match_band(0) == "Low"


class TestExpertiseMatching:
    def test_canonical_names_are_resolved_through_aliases(self):
        canonical, raw = mentor_skill_index(["postgres", "js"])
        assert canonical == {"PostgreSQL", "JavaScript"}

    def test_free_text_expertise_matches_on_word_boundaries(self):
        canonical, raw = mentor_skill_index(["payment systems"])
        assert mentor_covers("payment systems", canonical, raw)
        assert not mentor_covers("Python", canonical, raw)

    def test_java_does_not_match_javascript_free_text(self):
        """Regression guard for the substring trap: 'java' ⊂ 'javascript'."""
        canonical, raw = mentor_skill_index(["javascript"])
        assert canonical == {"JavaScript"}
        assert not mentor_covers("Java", canonical, raw)
        assert mentor_covers("JavaScript", canonical, raw)

    def test_blank_and_non_string_entries_are_ignored(self):
        canonical, raw = mentor_skill_index(["  ", None, 42, "Python"])
        assert canonical == {"Python"}
        assert raw == {"python"}


# ── Ranking API ───────────────────────────────────────────────────────────────
class TestMentorMatchApi:
    def test_requires_auth(self, client):
        assert client.get("/mentorship/matches").status_code == 401

    def test_alumni_cannot_request_matches(self, client, make_user):
        headers, _ = make_user(email="m_alum@example.com", role="alumni")
        assert client.get("/mentorship/matches", headers=headers).status_code == 403

    def test_empty_directory_is_reported_honestly(self, client, make_user):
        headers, _ = make_student(client, make_user, "m_empty@example.com")
        res = client.get("/mentorship/matches", headers=headers)
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["matches"] == []
        assert "No alumni mentors" in body["explanation"]
        assert body["disclaimer"]

    def test_matches_are_ranked_by_score(self, client, make_user):
        student_headers, _ = make_student(
            client, make_user, "m_rank@example.com", target_role="Backend Developer"
        )
        required = [s["name"] for s in get_occupation("Backend Developer")["required_skills"]]
        _, weak_id = make_mentor_user(
            client, make_user, "m_weak@example.com", full_name="Weak Mentor",
            expertise_areas=["Cooking"], years_of_experience=1, max_mentees=1,
        )
        _, strong_id = make_mentor_user(
            client, make_user, "m_strong@example.com", full_name="Strong Mentor",
            expertise_areas=required, years_of_experience=10, max_mentees=5,
        )

        body = client.get("/mentorship/matches", headers=student_headers).json()
        ids = [m["user_id"] for m in body["matches"]]
        assert ids == [strong_id, weak_id]
        scores = [m["match_score"] for m in body["matches"]]
        assert scores == sorted(scores, reverse=True)

        strong = body["matches"][0]
        assert strong["match_band"] == "Strong"
        assert set(strong["overlap_skills"]) == set(required)
        assert set(body["missing_skills"]) == set(required)
        assert "mentor(s)" not in body["explanation"]
        assert "skill(s)" not in body["explanation"]

    def test_overlap_tracks_the_students_outstanding_skills(self, client, make_user):
        student_headers, _ = make_student(
            client, make_user, "m_over@example.com",
            target_role="Backend Developer",
            skills=[{"name": "Python", "level": "advanced"}],
        )
        make_mentor_user(
            client, make_user, "m_over_mentor@example.com", expertise_areas=["Python"]
        )
        body = client.get("/mentorship/matches", headers=student_headers).json()
        # Python is already the student's, so it is not outstanding any more.
        assert "Python" not in body["missing_skills"]
        assert body["matches"][0]["overlap_skills"] == []

    def test_factor_breakdown_is_exposed(self, client, make_user):
        student_headers, student_id = make_student(
            client, make_user, "m_factors@example.com",
            target_role="Backend Developer", college="IIT Delhi",
        )
        make_mentor_user(
            client, make_user, "m_factors_mentor@example.com",
            expertise_areas=["Python"], college="IIT Delhi",
        )
        match = client.get("/mentorship/matches", headers=student_headers).json()["matches"][0]
        keys = {f["key"] for f in match["factors"]}
        assert keys == {"gap_overlap", "same_college", "experience", "availability", "capacity"}
        assert match["match_score"] == sum(f["earned"] for f in match["factors"])
        assert match["remaining_capacity"] == match["max_mentees"]
        assert match["request_status"] is None

    def test_unavailable_mentors_are_still_listed_but_scored_lower(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "m_unavail@example.com")
        make_mentor_user(
            client, make_user, "m_unavail_mentor@example.com",
            is_available_for_mentoring=False,
        )
        match = client.get("/mentorship/matches", headers=student_headers).json()["matches"][0]
        assert match["is_available_for_mentoring"] is False
        availability = next(f for f in match["factors"] if f["key"] == "availability")
        assert availability["earned"] == 0


# ── Request lifecycle ─────────────────────────────────────────────────────────
class TestMentorshipRequests:
    def test_student_creates_a_request_and_it_snapshots_the_score(self, client, make_user):
        student_headers, student_id = make_student(
            client, make_user, "r_create@example.com", target_role="Backend Developer"
        )
        _, mentor_id = make_mentor_user(client, make_user, "r_mentor@example.com")

        listed = client.get("/mentorship/matches", headers=student_headers).json()
        expected = next(m for m in listed["matches"] if m["user_id"] == mentor_id)["match_score"]

        res = client.post(
            "/mentorship/requests",
            json={"alumni_user_id": mentor_id, "message": "Could you mentor me?"},
            headers=student_headers,
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["status"] == "pending"
        assert body["match_score"] == expected
        assert body["student_id"] == student_id
        assert body["alumni_id"] == mentor_id
        assert body["message"] == "Could you mentor me?"

    def test_request_status_is_reflected_in_matches(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_status@example.com")
        _, mentor_id = make_mentor_user(client, make_user, "r_status_mentor@example.com")
        client.post(
            "/mentorship/requests",
            json={"alumni_user_id": mentor_id},
            headers=student_headers,
        )
        match = client.get("/mentorship/matches", headers=student_headers).json()["matches"][0]
        assert match["request_status"] == "pending"

    def test_duplicate_pending_request_is_a_conflict(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_dup@example.com")
        _, mentor_id = make_mentor_user(client, make_user, "r_dup_mentor@example.com")
        payload = {"alumni_user_id": mentor_id}
        assert client.post(
            "/mentorship/requests", json=payload, headers=student_headers
        ).status_code == 201
        assert client.post(
            "/mentorship/requests", json=payload, headers=student_headers
        ).status_code == 409

    def test_a_declined_request_can_be_sent_again(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_again@example.com")
        mentor_headers, mentor_id = make_mentor_user(client, make_user, "r_again_mentor@example.com")

        created = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        ).json()
        client.post(
            f"/mentorship/requests/{created['id']}/decline", headers=mentor_headers
        )
        again = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        )
        assert again.status_code == 201
        assert again.json()["id"] != created["id"]

    def test_cannot_request_yourself(self, client, make_user):
        headers, user_id = make_student(client, make_user, "r_self@example.com")
        res = client.post(
            "/mentorship/requests", json={"alumni_user_id": user_id}, headers=headers
        )
        assert res.status_code == 400

    def test_cannot_request_a_student_account(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_tostudent@example.com")
        _, other_student_id = make_student(client, make_user, "r_student2@example.com")
        res = client.post(
            "/mentorship/requests",
            json={"alumni_user_id": other_student_id},
            headers=student_headers,
        )
        assert res.status_code == 400

    def test_unknown_mentor_is_404(self, client, make_user):
        headers, _ = make_student(client, make_user, "r_unknown@example.com")
        res = client.post(
            "/mentorship/requests", json={"alumni_user_id": 999999}, headers=headers
        )
        assert res.status_code == 404

    def test_alumni_cannot_create_requests(self, client, make_user):
        mentor_headers, mentor_id = make_mentor_user(client, make_user, "r_alum@example.com")
        res = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=mentor_headers
        )
        assert res.status_code == 403

    def test_mentor_accepts_and_capacity_is_respected(self, client, make_user):
        mentor_headers, mentor_id = make_mentor_user(
            client, make_user, "r_cap_mentor@example.com", max_mentees=1
        )
        first_headers, _ = make_student(client, make_user, "r_cap_1@example.com")
        second_headers, _ = make_student(client, make_user, "r_cap_2@example.com")

        first = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=first_headers
        ).json()
        second = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=second_headers
        ).json()

        accepted = client.post(
            f"/mentorship/requests/{first['id']}/accept", headers=mentor_headers
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["request"]["status"] == "accepted"

        # The mentor is now full.
        blocked = client.post(
            f"/mentorship/requests/{second['id']}/accept", headers=mentor_headers
        )
        assert blocked.status_code == 409
        assert "mentee limit" in blocked.json()["detail"].lower()

    def test_only_the_targeted_mentor_can_accept_or_decline(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_authz@example.com")
        target_headers, target_id = make_mentor_user(client, make_user, "r_target@example.com")
        other_headers, _ = make_mentor_user(client, make_user, "r_other@example.com")

        req = client.post(
            "/mentorship/requests", json={"alumni_user_id": target_id}, headers=student_headers
        ).json()

        # A mentor who is not a party to the request cannot even see it: 404 (not
        # 403), so the endpoint never confirms that someone else's request exists.
        assert client.post(
            f"/mentorship/requests/{req['id']}/accept", headers=other_headers
        ).status_code == 404
        assert client.post(
            f"/mentorship/requests/{req['id']}/decline", headers=other_headers
        ).status_code == 404

        # The student IS a party, so ownership passes and the role rule gives 403.
        assert client.post(
            f"/mentorship/requests/{req['id']}/accept", headers=student_headers
        ).status_code == 403
        assert client.post(
            f"/mentorship/requests/{req['id']}/decline", headers=student_headers
        ).status_code == 403

        # The real target still can.
        assert client.post(
            f"/mentorship/requests/{req['id']}/accept", headers=target_headers
        ).status_code == 200

    def test_student_cancels_their_own_pending_request(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_cancel@example.com")
        mentor_headers, mentor_id = make_mentor_user(client, make_user, "r_cancel_mentor@example.com")
        req = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        ).json()

        res = client.post(
            f"/mentorship/requests/{req['id']}/cancel", headers=student_headers
        )
        assert res.status_code == 200
        assert res.json()["request"]["status"] == "cancelled"

        # A mentor cannot cancel on the student's behalf.
        req2 = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        ).json()
        assert client.post(
            f"/mentorship/requests/{req2['id']}/cancel", headers=mentor_headers
        ).status_code == 403

    def test_cannot_act_on_a_closed_request(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_closed@example.com")
        mentor_headers, mentor_id = make_mentor_user(client, make_user, "r_closed_mentor@example.com")
        req = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        ).json()

        assert client.post(
            f"/mentorship/requests/{req['id']}/accept", headers=mentor_headers
        ).status_code == 200
        # Already accepted → no longer pending.
        assert client.post(
            f"/mentorship/requests/{req['id']}/accept", headers=mentor_headers
        ).status_code == 409
        assert client.post(
            f"/mentorship/requests/{req['id']}/decline", headers=mentor_headers
        ).status_code == 409
        assert client.post(
            f"/mentorship/requests/{req['id']}/cancel", headers=student_headers
        ).status_code == 409

    def test_requests_are_listed_per_party(self, client, make_user):
        student_headers, student_id = make_student(client, make_user, "r_list@example.com")
        mentor_headers, mentor_id = make_mentor_user(client, make_user, "r_list_mentor@example.com")
        other_headers, _ = make_student(client, make_user, "r_list_other@example.com")

        req = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        ).json()

        sent = client.get("/mentorship/requests", headers=student_headers).json()
        assert [r["id"] for r in sent] == [req["id"]]
        assert sent[0]["alumni_id"] == mentor_id
        assert sent[0]["alumni_name"] == "Mentor"

        received = client.get("/mentorship/requests", headers=mentor_headers).json()
        assert [r["id"] for r in received] == [req["id"]]
        assert received[0]["student_id"] == student_id

        assert client.get("/mentorship/requests", headers=other_headers).json() == []

    def test_unrelated_users_cannot_see_or_act_on_a_request(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_iso@example.com")
        mentor_headers, mentor_id = make_mentor_user(client, make_user, "r_iso_mentor@example.com")
        outsider_headers, _ = make_mentor_user(client, make_user, "r_iso_out@example.com")

        req = client.post(
            "/mentorship/requests", json={"alumni_user_id": mentor_id}, headers=student_headers
        ).json()

        for action in ("accept", "decline", "cancel"):
            assert client.post(
                f"/mentorship/requests/{req['id']}/{action}", headers=outsider_headers
            ).status_code == 404

    def test_unknown_request_is_404(self, client, make_user):
        student_headers, _ = make_student(client, make_user, "r_missing@example.com")
        assert client.post(
            "/mentorship/requests/999999/accept", headers=student_headers
        ).status_code == 404
