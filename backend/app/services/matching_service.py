"""
Alumni matching service — Phase 8.

Deterministic, explainable mentor ranking. No LLM, no embeddings, no randomness.

Match score
-----------
Each candidate gets a score out of 100, built from five weighted factors. Every
factor and the points it awarded are returned, so a ranking can always be
audited:

    gap_overlap     40  share of your outstanding required skills the mentor covers
    same_college    20  mentor studied at the same institution
    experience      15  years of experience, scaled up to EXPERIENCE_CAP_YEARS
    availability    15  mentor is currently open to mentoring
    capacity        10  share of the mentor's mentee slots still free

The score is a **ranking heuristic**. It is not a prediction that a mentorship
will succeed, and it is deliberately not a probability of anything.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.skills_taxonomy import normalize_skill_name
from app.models.mentorship import (
    STATUS_ACCEPTED,
    STATUS_PENDING,
    MentorshipRequest,
)
from app.models.profile import AlumniProfile, StudentProfile
from app.models.user import User, UserRole
from app.schemas.mentorship import MatchFactor, MentorMatch, MentorMatchListResponse
from app.services.skill_gap_service import analyze_skill_gap, get_profile_skills

MATCH_DISCLAIMER = (
    "Match scores are a deterministic ranking of mentor profiles against your "
    "outstanding skills. They are a heuristic to help you choose who to talk to "
    "first — not a prediction that a mentorship will be a good fit, and not a "
    "judgement about any mentor."
)

# Factor weights — they sum to 100 so the score is directly interpretable.
W_GAP_OVERLAP = 40
W_SAME_COLLEGE = 20
W_EXPERIENCE = 15
W_AVAILABILITY = 15
W_CAPACITY = 10

#: Years of experience at which the experience factor is fully awarded.
EXPERIENCE_CAP_YEARS = 10


def match_band(score: int) -> str:
    if score >= 75:
        return "Strong"
    if score >= 55:
        return "Good"
    if score >= 35:
        return "Fair"
    return "Low"


# ─── Expertise matching ───────────────────────────────────────────────────────
def mentor_skill_index(expertise_areas: Optional[List[Any]]) -> Tuple[Set[str], Set[str]]:
    """
    Normalises a mentor's free-text ``expertise_areas`` into:
      * canonical taxonomy skill names, and
      * the raw lower-cased strings (used as a fallback for skills the mentor
        wrote in their own words, e.g. "payment systems").
    """
    canonical: Set[str] = set()
    raw: Set[str] = set()
    for area in expertise_areas or []:
        if not isinstance(area, str) or not area.strip():
            continue
        text = area.strip()
        raw.add(text.lower())
        resolved = normalize_skill_name(text)
        if resolved:
            canonical.add(resolved)
    return canonical, raw


def mentor_covers(skill: str, canonical: Set[str], raw: Set[str]) -> bool:
    """True when the mentor's expertise covers ``skill`` (canonical or free text)."""
    if skill in canonical:
        return True
    # Word-boundary match so "Java" does not match the free text "javascript".
    pattern = re.compile(rf"\b{re.escape(skill.lower())}\b")
    return any(pattern.search(text) for text in raw)


# ─── Scoring ──────────────────────────────────────────────────────────────────
def compute_match(
    mentor: AlumniProfile,
    *,
    student_college: Optional[str],
    required_skills: List[str],
    missing_skills: List[str],
    target_occupation: Optional[str],
    accepted_mentees: int,
) -> Tuple[int, List[str], List[MatchFactor]]:
    """
    Pure scoring function. Returns ``(score, overlap_skills, factors)``.
    The score is exactly ``sum(factor.earned)``, which tests assert.
    """
    canonical, raw = mentor_skill_index(mentor.expertise_areas)

    # ── 1. Overlap with the student's outstanding required skills ─────────────
    if target_occupation and missing_skills:
        basis = missing_skills
        basis_kind = "outstanding"
    elif target_occupation and required_skills:
        basis = required_skills
        basis_kind = "already-covered"
    else:
        basis = []
        basis_kind = "unavailable"

    overlap = [s for s in basis if mentor_covers(s, canonical, raw)]
    if not basis:
        gap_earned = 0
        gap_detail = (
            "No target occupation on your profile yet, so overlap could not be "
            "measured. Add a target role to unlock this factor."
        )
    elif basis_kind == "outstanding":
        gap_earned = int(round(W_GAP_OVERLAP * len(overlap) / len(basis)))
        gap_detail = (
            f"Covers {len(overlap)} of your {len(basis)} outstanding required "
            f"skill(s) for {target_occupation}"
            + (f": {', '.join(overlap)}." if overlap else ".")
        )
    else:
        gap_earned = int(round(W_GAP_OVERLAP * len(overlap) / len(basis)))
        gap_detail = (
            f"You already cover every required skill for {target_occupation}, so "
            f"this measures general overlap with the role ({len(overlap)} of "
            f"{len(basis)})."
        )

    # ── 2. Same institution ──────────────────────────────────────────────────
    a = (student_college or "").strip().lower()
    b = (mentor.college or "").strip().lower()
    if a and b and a == b:
        college_earned = W_SAME_COLLEGE
        college_detail = f"Same institution as you ({mentor.college})."
    elif not a:
        college_earned = 0
        college_detail = "Add your college to your profile to unlock this factor."
    elif not b:
        college_earned = 0
        college_detail = "This mentor has not listed a college."
    else:
        college_earned = 0
        college_detail = f"Different institution ({mentor.college})."

    # ── 3. Experience ────────────────────────────────────────────────────────
    years = int(mentor.years_of_experience or 0)
    capped = min(max(years, 0), EXPERIENCE_CAP_YEARS)
    experience_earned = int(round(W_EXPERIENCE * capped / EXPERIENCE_CAP_YEARS))
    experience_detail = (
        f"{years} year(s) of experience "
        f"(full {W_EXPERIENCE} points from {EXPERIENCE_CAP_YEARS} years)."
    )

    # ── 4. Availability ──────────────────────────────────────────────────────
    if mentor.is_available_for_mentoring:
        availability_earned = W_AVAILABILITY
        availability_detail = "Currently open to mentoring."
    else:
        availability_earned = 0
        availability_detail = "Not currently open to mentoring."

    # ── 5. Remaining capacity ────────────────────────────────────────────────
    max_mentees = int(mentor.max_mentees or 0)
    remaining = max(0, max_mentees - max(accepted_mentees, 0))
    if max_mentees <= 0:
        capacity_earned = 0
        capacity_detail = "This mentor has no mentee capacity configured."
    else:
        capacity_earned = int(round(W_CAPACITY * remaining / max_mentees))
        capacity_detail = f"{remaining} of {max_mentees} mentee slot(s) free."

    factors = [
        MatchFactor(key="gap_overlap", label="Skill-gap overlap", weight=W_GAP_OVERLAP,
                    earned=gap_earned, detail=gap_detail),
        MatchFactor(key="same_college", label="Same institution", weight=W_SAME_COLLEGE,
                    earned=college_earned, detail=college_detail),
        MatchFactor(key="experience", label="Experience", weight=W_EXPERIENCE,
                    earned=experience_earned, detail=experience_detail),
        MatchFactor(key="availability", label="Availability", weight=W_AVAILABILITY,
                    earned=availability_earned, detail=availability_detail),
        MatchFactor(key="capacity", label="Free mentee slots", weight=W_CAPACITY,
                    earned=capacity_earned, detail=capacity_detail),
    ]
    score = sum(f.earned for f in factors)
    return score, overlap, factors


# ─── Candidate listing ────────────────────────────────────────────────────────
def _accepted_counts(db: Session) -> Dict[int, int]:
    rows = (
        db.query(MentorshipRequest.alumni_id, func.count(MentorshipRequest.id))
        .filter(MentorshipRequest.status == STATUS_ACCEPTED)
        .group_by(MentorshipRequest.alumni_id)
        .all()
    )
    return {alumni_id: count for alumni_id, count in rows}


def _student_request_status(db: Session, student_id: int) -> Dict[int, str]:
    """
    One status per mentor for this student, with a fixed precedence so the UI
    never hides an active relationship: accepted > pending > most recent.
    """
    rows = (
        db.query(MentorshipRequest)
        .filter(MentorshipRequest.student_id == student_id)
        .order_by(MentorshipRequest.created_at.desc(), MentorshipRequest.id.desc())
        .all()
    )
    statuses: Dict[int, str] = {}
    for row in rows:  # newest first
        current = statuses.get(row.alumni_id)
        if current is None:
            statuses[row.alumni_id] = row.status
        elif current != STATUS_ACCEPTED and row.status == STATUS_ACCEPTED:
            statuses[row.alumni_id] = STATUS_ACCEPTED
        elif current not in (STATUS_ACCEPTED, STATUS_PENDING) and row.status == STATUS_PENDING:
            statuses[row.alumni_id] = STATUS_PENDING
    return statuses


def list_mentor_matches(db: Session, student: User) -> MentorMatchListResponse:
    """Ranks every active alumni mentor for the given student."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student.id).first()
    target_role = profile.target_role if profile else None
    student_college = profile.college if profile else None

    required_skills: List[str] = []
    missing_skills: List[str] = []
    target_occupation: Optional[str] = None

    if target_role:
        gap = analyze_skill_gap(get_profile_skills(db, student), target_role)
        if gap is not None:
            target_occupation = gap.occupation_name
            required_skills = [a.name for a in gap.matched_skills] + [
                a.name for a in gap.missing_skills
            ]
            missing_skills = [a.name for a in gap.missing_skills]

    accepted = _accepted_counts(db)
    request_statuses = _student_request_status(db, student.id)

    candidates = (
        db.query(AlumniProfile, User)
        .join(User, AlumniProfile.user_id == User.id)
        .filter(User.is_active == True, User.id != student.id)  # noqa: E712
        .all()
    )

    matches: List[MentorMatch] = []
    for alumni_profile, alumni_user in candidates:
        if alumni_user.role not in (UserRole.ALUMNI, UserRole.ADMIN):
            continue

        accepted_count = accepted.get(alumni_user.id, 0)
        score, overlap, factors = compute_match(
            alumni_profile,
            student_college=student_college,
            required_skills=required_skills,
            missing_skills=missing_skills,
            target_occupation=target_occupation,
            accepted_mentees=accepted_count,
        )
        max_mentees = int(alumni_profile.max_mentees or 0)
        matches.append(
            MentorMatch(
                user_id=alumni_user.id,
                full_name=alumni_user.full_name,
                company=alumni_profile.company,
                job_title=alumni_profile.job_title,
                years_of_experience=int(alumni_profile.years_of_experience or 0),
                college=alumni_profile.college,
                expertise_areas=list(alumni_profile.expertise_areas or []),
                bio=alumni_profile.bio,
                linkedin_url=alumni_profile.linkedin_url,
                github_username=alumni_profile.github_username,
                meeting_link=alumni_profile.meeting_link,
                is_available_for_mentoring=bool(alumni_profile.is_available_for_mentoring),
                max_mentees=max_mentees,
                accepted_mentees=accepted_count,
                remaining_capacity=max(0, max_mentees - accepted_count),
                match_score=score,
                match_band=match_band(score),
                overlap_skills=overlap,
                factors=factors,
                request_status=request_statuses.get(alumni_user.id),
            )
        )

    # Deterministic ordering: score, then overlap, then name, then id.
    matches.sort(
        key=lambda m: (-m.match_score, -len(m.overlap_skills), m.full_name.lower(), m.user_id)
    )

    if not matches:
        explanation = (
            "No alumni mentors are registered yet. Once alumni complete their "
            "profiles they will appear here."
        )
    elif not target_role:
        explanation = (
            f"Ranked {len(matches)} mentor(s) on experience, availability, capacity "
            "and institution. Set a target role on your profile to include skill-gap "
            "overlap in the ranking."
        )
    else:
        explanation = (
            f"Ranked {len(matches)} mentor(s) against {target_occupation}"
            + (
                f", focusing on your {len(missing_skills)} outstanding required skill(s)."
                if missing_skills
                else ", which you already cover — so overlap is measured against the role itself."
            )
        )

    return MentorMatchListResponse(
        target_occupation=target_occupation,
        missing_skills=missing_skills,
        matches=matches,
        explanation=explanation,
        disclaimer=MATCH_DISCLAIMER,
    )
