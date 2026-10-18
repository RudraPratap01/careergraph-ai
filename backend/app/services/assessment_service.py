"""
Assessment service — Phase 8.

Deterministic grading. No LLM, no randomness.

Grading rules
-------------
* A question is correct when the chosen index equals the stored answer index.
  An unanswered question is simply incorrect (never a crash).
* Assessment score  = round(100 × correct / total questions).
* Skill score       = round(100 × correct / questions tagged with that skill).
* A skill counts as *evidence* only when its score reaches ``PASS_THRESHOLD``
  **and** at least ``MIN_QUESTIONS_PER_SKILL`` questions were asked about it, so
  a single lucky answer can never evidence a skill.
* Passing an assessment never edits the profile by itself. The student is
  *suggested* skills and explicitly confirms which ones to add, mirroring the
  Phase 3 resume-review flow. Confirmation is server-side validated against the
  attempt, so a client cannot claim a skill it did not pass.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.assessments import (
    ASSESSMENT_SOURCE,
    MIN_QUESTIONS_PER_SKILL,
    PASS_THRESHOLD,
    get_assessment,
    list_assessments,
)
from app.data.skills_taxonomy import get_skill_category, normalize_skill_name
from app.models.assessment import STATUS_COMPLETED, STATUS_IN_PROGRESS, AssessmentAttempt
from app.models.profile import StudentProfile
from app.models.user import User
from app.schemas.assessment import (
    AssessmentAttemptResponse,
    AssessmentQuestion,
    AssessmentResultResponse,
    ConfirmSkillsResponse,
    QuestionResult,
    SkillEvidence,
)

ASSESSMENT_DISCLAIMER = (
    "These questions come from a small curated bank written for this project. "
    "They are not a validated psychometric instrument, not a professional "
    "certification, and not proof of on-the-job competence."
)

#: Level recorded when a passed assessment adds a skill to the profile.
EVIDENCE_LEVEL = "intermediate"


# ─── Public views (answers stripped) ──────────────────────────────────────────
def public_question(question: Dict[str, Any]) -> AssessmentQuestion:
    """The client-facing view of a question: never includes the answer."""
    return AssessmentQuestion(
        id=question["id"],
        skill=question["skill"],
        difficulty=question.get("difficulty", "basic"),
        prompt=question["prompt"],
        options=list(question["options"]),
    )


def public_assessment(record: Dict[str, Any]) -> Dict[str, Any]:
    """Assessment detail with every answer stripped."""
    return {
        "key": record["key"],
        "name": record["name"],
        "description": record["description"],
        "skills": list(record["skills"]),
        "question_count": len(record["questions"]),
        "pass_threshold": record.get("pass_threshold", PASS_THRESHOLD),
        "source": record.get("source", ASSESSMENT_SOURCE),
        "questions": [public_question(q) for q in record["questions"]],
    }


def get_catalog() -> List[Dict[str, Any]]:
    return list_assessments()


# ─── Serialization ────────────────────────────────────────────────────────────
def _evidence_from_results(results: Optional[Dict[str, Any]]) -> List[SkillEvidence]:
    return [SkillEvidence(**s) for s in (results or {}).get("skills", [])]


def serialize_attempt(attempt: AssessmentAttempt) -> AssessmentAttemptResponse:
    results = attempt.results or {}
    return AssessmentAttemptResponse(
        id=attempt.id,
        user_id=attempt.user_id,
        assessment_key=attempt.assessment_key,
        assessment_name=attempt.assessment_name,
        status=attempt.status,
        score_percent=attempt.score_percent,
        passed=attempt.passed,
        correct_count=attempt.correct_count,
        total_count=attempt.total_count,
        skills=_evidence_from_results(attempt.results),
        passed_skills=list(results.get("passed_skills", [])),
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
    )


# ─── Attempts ─────────────────────────────────────────────────────────────────
def start_attempt(db: Session, user: User, key: str) -> Optional[Dict[str, Any]]:
    """
    Opens a new attempt for ``key``. Returns ``None`` when the assessment key is
    unknown (the route turns that into a 404).
    """
    record = get_assessment(key)
    if not record:
        return None

    attempt = AssessmentAttempt(
        user_id=user.id,
        assessment_key=record["key"],
        assessment_name=record["name"],
        status=STATUS_IN_PROGRESS,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt": serialize_attempt(attempt),
        "questions": [public_question(q) for q in record["questions"]],
    }


def get_owned_attempt(db: Session, user: User, attempt_id: int) -> Optional[AssessmentAttempt]:
    """Ownership-scoped lookup — never returns another user's attempt."""
    return (
        db.query(AssessmentAttempt)
        .filter(AssessmentAttempt.id == attempt_id, AssessmentAttempt.user_id == user.id)
        .first()
    )


def list_attempts(db: Session, user: User) -> List[AssessmentAttemptResponse]:
    attempts = (
        db.query(AssessmentAttempt)
        .filter(AssessmentAttempt.user_id == user.id)
        .order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id.desc())
        .all()
    )
    return [serialize_attempt(a) for a in attempts]


def _grade_questions(
    record: Dict[str, Any],
    answers: List[Any],
) -> Tuple[List[QuestionResult], int]:
    chosen_by_id: Dict[str, int] = {}
    for answer in answers:
        if answer.question_id in chosen_by_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate answer for question '{answer.question_id}'.",
            )
        chosen_by_id[answer.question_id] = answer.chosen_index

    results: List[QuestionResult] = []
    correct_count = 0
    for question in record["questions"]:
        chosen = chosen_by_id.get(question["id"])
        if chosen is not None and not (0 <= chosen < len(question["options"])):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Answer for '{question['id']}' is out of range "
                    f"(0-{len(question['options']) - 1})."
                ),
            )
        is_correct = chosen is not None and chosen == question["answer_index"]
        correct_count += 1 if is_correct else 0
        results.append(
            QuestionResult(
                question_id=question["id"],
                skill=question["skill"],
                correct=is_correct,
                chosen_index=chosen,
                correct_index=question["answer_index"],
                explanation=question["explanation"],
            )
        )
    return results, correct_count


def _grade_skills(record: Dict[str, Any], results: List[QuestionResult]) -> List[SkillEvidence]:
    tally: Dict[str, List[int]] = {skill: [0, 0] for skill in record["skills"]}
    for result in results:
        bucket = tally.setdefault(result.skill, [0, 0])
        bucket[1] += 1
        if result.correct:
            bucket[0] += 1

    evidence: List[SkillEvidence] = []
    for skill, (correct, total) in tally.items():
        score = int(round(100.0 * correct / total)) if total else 0
        passed = total > 0 and score >= PASS_THRESHOLD
        evidence.append(
            SkillEvidence(
                skill=skill,
                category=get_skill_category(skill),
                correct=correct,
                total=total,
                score_percent=score,
                passed=passed,
                eligible_for_evidence=passed and total >= MIN_QUESTIONS_PER_SKILL,
            )
        )
    evidence.sort(key=lambda e: (-e.score_percent, e.skill.lower()))
    return evidence


def grade_attempt(
    db: Session,
    user: User,
    attempt_id: int,
    answers: List[Any],
) -> Optional[AssessmentResultResponse]:
    """
    Grades a submitted attempt. Returns ``None`` when the attempt does not exist
    or is not owned by the user. Raises ``409`` when it was already submitted.
    """
    attempt = get_owned_attempt(db, user, attempt_id)
    if attempt is None:
        return None
    if attempt.status == STATUS_COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This attempt has already been submitted.",
        )

    record = get_assessment(attempt.assessment_key)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment is no longer in the question bank. Start a new attempt.",
        )

    results, correct_count = _grade_questions(record, answers)
    total_count = len(record["questions"])
    score = int(round(100.0 * correct_count / total_count)) if total_count else 0
    evidence = _grade_skills(record, results)
    passed_skills = [e.skill for e in evidence if e.eligible_for_evidence]

    attempt.status = STATUS_COMPLETED
    attempt.score_percent = score
    attempt.passed = score >= record.get("pass_threshold", PASS_THRESHOLD)
    attempt.correct_count = correct_count
    attempt.total_count = total_count
    attempt.results = {
        "answers": [
            {
                "question_id": r.question_id,
                "chosen_index": r.chosen_index,
                "correct": r.correct,
            }
            for r in results
        ],
        "skills": [e.model_dump() for e in evidence],
        "passed_skills": passed_skills,
    }
    attempt.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)

    if passed_skills:
        explanation = (
            f"You scored {score}% ({correct_count}/{total_count}). These skills can be "
            f"added to your profile as evidenced: {', '.join(passed_skills)}."
        )
    else:
        explanation = (
            f"You scored {score}% ({correct_count}/{total_count}). No skill reached the "
            f"{record.get('pass_threshold', PASS_THRESHOLD)}% evidence threshold yet — "
            "review the explanations and try again."
        )

    return AssessmentResultResponse(
        attempt=serialize_attempt(attempt),
        results=results,
        suggested_skills=passed_skills,
        explanation=explanation,
        disclaimer=ASSESSMENT_DISCLAIMER,
    )


# ─── Turning a pass into profile evidence ─────────────────────────────────────
def confirm_skills(
    db: Session,
    user: User,
    attempt_id: int,
    requested_skills: List[str],
) -> Optional[ConfirmSkillsResponse]:
    """
    Adds assessment-evidenced skills to the student's profile.

    Every requested skill must be a canonical skill that this attempt actually
    passed — the client cannot assert evidence it does not have. Existing
    profile entries are kept (their level is preserved); a confirmed skill is
    marked ``source="assessment"``.
    """
    attempt = get_owned_attempt(db, user, attempt_id)
    if attempt is None:
        return None
    if attempt.status != STATUS_COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Submit this attempt before confirming its skills.",
        )

    allowed = set((attempt.results or {}).get("passed_skills", []))

    canonical_requested: List[str] = []
    invalid: List[str] = []
    for raw in requested_skills:
        canonical = normalize_skill_name(raw)
        if canonical is None:
            invalid.append(str(raw))
        elif canonical not in allowed:
            invalid.append(canonical)
        elif canonical not in canonical_requested:
            canonical_requested.append(canonical)

    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "These skills were not evidenced by this attempt: "
                + ", ".join(sorted(set(invalid)))
                + "."
            ),
        )

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile is None:
        profile = StudentProfile(user_id=user.id, skills=[])
        db.add(profile)
        db.flush()

    existing: List[Dict[str, Any]] = list(profile.skills or [])
    by_canonical: Dict[str, Dict[str, Any]] = {}
    for entry in existing:
        name = entry.get("name") if isinstance(entry, dict) else entry
        canonical = normalize_skill_name(name)
        if canonical:
            by_canonical[canonical] = dict(entry) if isinstance(entry, dict) else {"name": name}

    added: List[str] = []
    already_present: List[str] = []
    for skill in canonical_requested:
        if skill in by_canonical:
            already_present.append(skill)
            by_canonical[skill]["name"] = skill
            by_canonical[skill].setdefault("level", EVIDENCE_LEVEL)
            by_canonical[skill]["source"] = "assessment"
        else:
            added.append(skill)
            by_canonical[skill] = {
                "name": skill,
                "level": EVIDENCE_LEVEL,
                "source": "assessment",
            }

    # Preserve anything that did not resolve to a canonical skill.
    unresolved = [
        entry
        for entry in existing
        if not normalize_skill_name(entry.get("name") if isinstance(entry, dict) else entry)
    ]
    merged = sorted(by_canonical.values(), key=lambda e: str(e.get("name", "")).lower()) + unresolved

    profile.skills = merged
    db.commit()
    db.refresh(profile)

    return ConfirmSkillsResponse(
        added=sorted(added, key=lambda s: s.lower()),
        already_present=sorted(already_present, key=lambda s: s.lower()),
        skills=profile.skills,
        message=(
            f"Added {len(added)} evidenced skill(s) to your profile; "
            f"{len(already_present)} were already present and are now marked as evidenced."
        ),
    )
