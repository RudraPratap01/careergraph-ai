"""
Phase 2 tests — User Profiles & Auth Integration.
Tests:
- Register student & alumni
- Update student profile (target role, skills, education)
- Retrieve student profile & check completion score
- Update alumni profile (company, title, expertise, mentoring availability)
- List alumni mentors with expertise filtering
- Access control verification
"""



def test_student_profile_lifecycle(client):
    # 1. Register student
    reg_res = client.post(
        "/auth/register",
        json={
            "email": "student1@example.com",
            "full_name": "Test Student",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert reg_res.status_code == 201

    # 2. Login
    login_res = client.post(
        "/auth/login",
        json={"email": "student1@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Check initial profile (empty profile)
    me_res = client.get("/profile/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["completion_percentage"] == 0
    assert me_data["student_profile"] is None

    # 4. Update student profile
    profile_payload = {
        "college": "Tech University",
        "degree": "B.Tech Computer Science",
        "current_year": 4,
        "graduation_year": 2026,
        "cgpa": 8.5,
        "target_role": "Backend Developer",
        "target_timeline_months": 6,
        "bio": "Aspiring backend engineer proficient in Python and APIs.",
        "github_username": "testdev",
        "linkedin_url": "https://linkedin.com/in/testdev",
        "portfolio_url": "https://testdev.me",
        "skills": [
            {"name": "Python", "level": "intermediate"},
            {"name": "FastAPI", "level": "intermediate"},
            {"name": "PostgreSQL", "level": "beginner"},
        ],
    }
    update_res = client.put("/profile/student", json=profile_payload, headers=headers)
    assert update_res.status_code == 200
    updated_profile = update_res.json()
    assert updated_profile["target_role"] == "Backend Developer"
    assert len(updated_profile["skills"]) == 3

    # 5. Check completion percentage now
    me_res2 = client.get("/profile/me", headers=headers)
    assert me_res2.status_code == 200
    assert me_res2.json()["completion_percentage"] == 100


def test_alumni_profile_and_mentor_directory(client):
    # 1. Register alumni
    reg_res = client.post(
        "/auth/register",
        json={
            "email": "mentor1@example.com",
            "full_name": "Senior Engineer",
            "password": "Password123!",
            "role": "alumni",
        },
    )
    assert reg_res.status_code == 201

    # 2. Login
    login_res = client.post(
        "/auth/login",
        json={"email": "mentor1@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Update alumni profile
    alumni_payload = {
        "company": "Cloud Corp",
        "job_title": "Senior Systems Architect",
        "years_of_experience": 6,
        "college": "Tech University",
        "graduation_year": 2020,
        "expertise_areas": ["System Design", "Distributed Systems", "Python"],
        "bio": "Mentoring final-year engineering students for backend & distributed systems.",
        "linkedin_url": "https://linkedin.com/in/senioreng",
        "github_username": "senioreng",
        "meeting_link": "https://cal.com/senioreng",
        "is_available_for_mentoring": True,
        "max_mentees": 4,
    }
    update_res = client.put("/profile/alumni", json=alumni_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["company"] == "Cloud Corp"

    # 4. Check mentor directory
    mentors_res = client.get("/alumni")
    assert mentors_res.status_code == 200
    mentors = mentors_res.json()
    assert len(mentors) >= 1
    assert mentors[0]["full_name"] == "Senior Engineer"
    assert "System Design" in mentors[0]["expertise_areas"]

    # 5. Check mentor filter
    filter_match = client.get("/alumni?expertise=Design")
    assert len(filter_match.json()) == 1

    filter_nomatch = client.get("/alumni?expertise=UnrelatedTopic")
    assert len(filter_nomatch.json()) == 0
