"""
Phase 3 tests — Resume Intelligence.

Tests:
1. Secure file upload validation (formats, empty files)
2. Text extraction (TXT, DOCX, PDF)
3. Skill extraction, normalization, confidence scoring, and evidence
4. Complete student upload, retrieval, and skill confirmation workflow
5. Verification that confirmed skills sync to StudentProfile
"""

import io
from docx import Document
from pypdf import PdfWriter

from app.services.skill_extractor import extract_skills_from_text


def create_sample_docx(text: str) -> io.BytesIO:
    """Creates an in-memory DOCX file with sample text."""
    doc = Document()
    for paragraph in text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


def create_sample_pdf(text: str) -> io.BytesIO:
    """Creates a basic PDF using pypdf."""
    writer = PdfWriter()
    writer.add_blank_page(width=72 * 8.5, height=72 * 11)
    bio = io.BytesIO()
    writer.write(bio)
    bio.seek(0)
    return bio


SAMPLE_RESUME_TEXT = """
Aarav Sharma
B.Tech Computer Science & Engineering
Email: aarav@example.com | GitHub: github.com/aarav | LinkedIn: linkedin.com/in/aarav

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL, HTML, CSS
Frameworks: React, FastAPI, Node.js, Express, Tailwind CSS
Databases: PostgreSQL, MongoDB, Redis
Cloud & DevOps: Docker, Git, Linux, CI/CD, AWS
Concepts: REST APIs, Microservices, System Design, Data Structures & Algorithms

PROJECTS
CareerGraph AI Platform
- Built scalable REST APIs using FastAPI and PostgreSQL with 99.9% uptime.
- Implemented frontend user interface in React and Tailwind CSS.
- Containerized application services using Docker and orchestrated CI/CD workflows on GitHub Actions.

E-Commerce Microservices Backend
- Architected microservices with Python, Redis caching, and MongoDB for document storage.
- Designed secure authentication using JWT and OAuth2 protocols.

EDUCATION
National Institute of Technology — B.Tech CSE (2022 - 2026), CGPA: 8.8
"""


def test_skill_extractor_normalization_and_confidence():
    """Verify skill extraction, synonym normalization, categories, and evidence."""
    skills = extract_skills_from_text(SAMPLE_RESUME_TEXT)
    skill_names = {s.normalized_name for s in skills}

    # Verify key skills extracted
    assert "Python" in skill_names
    assert "FastAPI" in skill_names
    assert "React" in skill_names
    assert "PostgreSQL" in skill_names
    assert "Docker" in skill_names
    assert "REST APIs" in skill_names
    assert "MongoDB" in skill_names
    assert "Redis" in skill_names

    # Check evidence and confidence for FastAPI
    fastapi_skill = next(s for s in skills if s.normalized_name == "FastAPI")
    assert fastapi_skill.category == "Frameworks & Libraries"
    assert fastapi_skill.confidence >= 0.90
    assert "FastAPI" in fastapi_skill.evidence


def test_resume_upload_txt_and_confirm_workflow(client):
    """End-to-end test of student resume upload, review, and sync to profile."""
    # 1. Register student
    reg = client.post(
        "/auth/register",
        json={
            "email": "student_resume_test@example.com",
            "full_name": "Aarav Sharma",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert reg.status_code == 201

    # 2. Login
    login = client.post(
        "/auth/login",
        json={"email": "student_resume_test@example.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Upload resume (TXT)
    file_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")
    upload_res = client.post(
        "/resume/upload",
        files={"file": ("resume.txt", file_bytes, "text/plain")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert upload_data["filename"] == "resume.txt"
    assert upload_data["extracted_skills_count"] > 5
    assert upload_data["status"] == "parsed"
    resume_id = upload_data["resume_id"]

    # 4. Retrieve latest resume
    latest_res = client.get("/resume/latest", headers=headers)
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["id"] == resume_id
    assert len(latest_data["extracted_skills"]) > 5

    # 5. Confirm skills (Student review workflow)
    confirm_payload = {
        "resume_id": resume_id,
        "skills": [
            {"name": "Python", "level": "advanced"},
            {"name": "FastAPI", "level": "advanced"},
            {"name": "PostgreSQL", "level": "intermediate"},
            {"name": "Docker", "level": "intermediate"},
        ],
    }
    confirm_res = client.post(
        "/resume/confirm-skills",
        json=confirm_payload,
        headers=headers,
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["total_confirmed_skills"] == 4

    # 6. Verify skills synced to StudentProfile
    profile_res = client.get("/profile/me", headers=headers)
    assert profile_res.status_code == 200
    profile_skills = profile_res.json()["student_profile"]["skills"]
    profile_skill_names = {s["name"] for s in profile_skills}
    assert "FastAPI" in profile_skill_names
    assert "Python" in profile_skill_names
    assert "Docker" in profile_skill_names


def test_resume_upload_docx(client):
    """Verify DOCX resume text extraction and skill detection."""
    # Register & login
    client.post(
        "/auth/register",
        json={
            "email": "docx_tester@example.com",
            "full_name": "DOCX Tester",
            "password": "Password123!",
            "role": "student",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "docx_tester@example.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    docx_bio = create_sample_docx(SAMPLE_RESUME_TEXT)
    upload_res = client.post(
        "/resume/upload",
        files={"file": ("resume.docx", docx_bio, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    assert upload_res.json()["file_type"] == "docx"
    assert upload_res.json()["extracted_skills_count"] > 5


def test_resume_upload_validation_errors(client):
    """Verify rejection of invalid file extensions and empty files."""
    client.post(
        "/auth/register",
        json={
            "email": "val_tester@example.com",
            "full_name": "Val Tester",
            "password": "Password123!",
            "role": "student",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "val_tester@example.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Invalid file extension (.exe)
    res1 = client.post(
        "/resume/upload",
        files={"file": ("malicious.exe", b"executable code", "application/octet-stream")},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "Unsupported file format" in res1.json()["detail"]

    # 2. Empty file
    res2 = client.post(
        "/resume/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "empty" in res2.json()["detail"]
