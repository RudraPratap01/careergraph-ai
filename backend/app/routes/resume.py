"""
Resume routes — endpoints for resume upload, parsing, and skill confirmation.

Phase 3: Resume Intelligence
Route → Schema validation → Service (business logic) → Response.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.utils.security import get_current_user
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeDetailResponse,
    ConfirmSkillsRequest,
    ConfirmSkillsResponse,
)
from app.services.resume_service import (
    handle_resume_upload,
    get_latest_student_resume,
    confirm_student_skills,
)

router = APIRouter(prefix="/resume", tags=["Resume Intelligence"])


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and analyze a student resume (PDF, DOCX, TXT)",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (.pdf, .docx, or .txt)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Secure resume upload endpoint:
    - Validates file type and size (max 10MB)
    - Extracts raw text
    - Identifies candidate skills with confidence scores and evidence excerpts
    - Persists parsed record in database
    - Returns structured skills for student review
    """
    return await handle_resume_upload(current_user, file, db)


@router.get(
    "/latest",
    response_model=ResumeDetailResponse,
    summary="Get current user's latest uploaded resume and extracted skills",
)
def get_latest_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the most recent resume analysis for the authenticated student.
    """
    resume = get_latest_student_resume(current_user, db)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume uploaded yet for this account.",
        )
    return resume


@router.post(
    "/confirm-skills",
    response_model=ConfirmSkillsResponse,
    summary="Confirm or adjust extracted skills and sync to student profile",
)
def confirm_skills(
    request: ConfirmSkillsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Student review workflow:
    - Confirms approved skills (with selected proficiency levels)
    - Updates resume status to 'reviewed'
    - Synchronizes confirmed skills directly into the StudentProfile skill inventory
    """
    return confirm_student_skills(current_user, request, db)
