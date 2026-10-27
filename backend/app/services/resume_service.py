"""
Resume service — business logic for Phase 3: Resume Intelligence.

Coordinates:
  1. Secure resume file upload and text extraction
  2. Skill extraction, normalization, confidence scoring, and evidence collection
  3. Student review, skill confirmation, and sync to StudentProfile
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.models.user import User, UserRole
from app.models.profile import StudentProfile
from app.models.resume import Resume
from app.schemas.resume import (
    ExtractedSkill,
    ResumeUploadResponse,
    ResumeDetailResponse,
    ConfirmSkillsRequest,
    ConfirmSkillsResponse,
    ConfirmSkillItem,
)
from app.services.text_extractor import validate_and_extract_text
from app.services.skill_extractor import extract_skills_from_text


async def handle_resume_upload(
    user: User,
    file: UploadFile,
    db: Session,
) -> ResumeUploadResponse:
    """
    Handles resume upload:
    - Extracts clean text from PDF / DOCX / TXT
    - Runs skill extraction with confidence and evidence
    - Stores record in 'resumes' table
    - Returns structured summary for student review
    """
    if user.role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can upload resumes for analysis.",
        )

    # 1. Validate & extract text
    cleaned_text, file_type, file_size = await validate_and_extract_text(file)

    # 2. Extract & normalize skills with evidence
    extracted_skills: List[ExtractedSkill] = extract_skills_from_text(cleaned_text)

    # 3. Save Resume record to database
    resume = Resume(
        user_id=user.id,
        filename=file.filename or f"resume.{file_type}",
        file_type=file_type,
        file_size_bytes=file_size,
        raw_text=cleaned_text,
        extracted_skills=[s.model_dump() for s in extracted_skills],
        status="parsed",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 4. Create snippet of raw text (first ~300 chars)
    raw_snippet = cleaned_text[:300].strip() + ("…" if len(cleaned_text) > 300 else "")

    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        extracted_skills_count=len(extracted_skills),
        extracted_skills=extracted_skills,
        raw_text_snippet=raw_snippet,
        status=resume.status,
        created_at=resume.created_at,
    )


def get_latest_student_resume(user: User, db: Session) -> Optional[ResumeDetailResponse]:
    """Retrieves the user's latest uploaded resume and extracted skills."""
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    if not resume:
        return None

    extracted_skills = [ExtractedSkill(**s) for s in (resume.extracted_skills or [])]

    return ResumeDetailResponse(
        id=resume.id,
        user_id=resume.user_id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        extracted_skills=extracted_skills,
        raw_text=resume.raw_text,
        status=resume.status,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


def confirm_student_skills(
    user: User,
    request: ConfirmSkillsRequest,
    db: Session,
) -> ConfirmSkillsResponse:
    """
    Student review workflow:
    - Approves, modifies, or adds extracted skills
    - Marks resume as 'reviewed'
    - Synchronizes the complete confirmed skill list into StudentProfile.skills

    Semantics: The confirmation payload represents the student's complete
    reviewed skill list (auto-extracted skills the student kept, skills the
    student edited, any skills the student manually added during review, and
    existing profile skills the review UI kept so they are not lost).
    Skills that the student removed from the review pane are intentionally
    absent from the payload and will NOT appear in the saved profile.

    The optional ``source`` field distinguishes a resume match from a skill
    that was already on the profile (``self``). Only those two values are
    accepted, so this endpoint cannot be used to claim assessment or GitHub
    evidence; those sources are preserved separately below.

    Unrelated profile fields (college, degree, bio, etc.) are not modified.
    Repeated confirmations are idempotent — duplicates by name are collapsed.
    """
    if user.role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can confirm resume skills.",
        )

    # 1. If resume_id is provided, verify ownership and mark as reviewed
    if request.resume_id:
        resume = (
            db.query(Resume)
            .filter(Resume.id == request.resume_id, Resume.user_id == user.id)
            .first()
        )
        if resume:
            resume.status = "reviewed"
        # If resume_id given but not found/not owned, silently skip rather than error
        # (user may have uploaded a new resume in parallel)

    # 2. Retrieve or create StudentProfile
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        profile = StudentProfile(user_id=user.id, skills=[])
        db.add(profile)
        db.flush()

    # 3. Replace profile skills with the complete confirmed list.
    # Deduplicate by lowercased name (preserving the last value for each name,
    # matching the order of request.skills so later items take precedence).
    seen: dict = {}

    # Skills already evidenced by a passed assessment (Phase 8) or a verified
    # GitHub account (Phase 6) are preserved at the front of the list: reviewing a
    # resume must not discard verified evidence. A resume text match never
    # downgrades an evidenced skill.
    evidenced_sources = ("assessment", "github")
    for entry in profile.skills or []:
        if isinstance(entry, dict) and entry.get("source") in evidenced_sources:
            key = str(entry.get("name", "")).strip().lower()
            if key:
                seen[key] = dict(entry)

    for skill_item in request.skills:
        name_key = skill_item.name.strip().lower()
        if not name_key:
            continue
        existing = seen.get(name_key)
        if existing is not None and existing.get("source") in evidenced_sources:
            continue
        seen[name_key] = {
            "name": skill_item.name.strip(),
            "level": skill_item.level,
            "source": skill_item.source,
        }

    profile.skills = list(seen.values())
    db.commit()

    return ConfirmSkillsResponse(
        message="Resume skills confirmed and synced to student profile successfully.",
        total_confirmed_skills=len(seen),
        synced_to_profile=True,
        skills=request.skills,
    )

