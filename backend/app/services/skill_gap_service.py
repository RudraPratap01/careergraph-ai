"""
Skill-gap & career-readiness service — Phase 4.

Deterministic, explainable scoring. No LLM, no embeddings, no randomness.

Readiness formula
-----------------
For a target occupation with required skills R (each with importance weight w):

    readiness = round( 100 * Σ w(skill for skill in R if user has skill)
                            / Σ w(skill for skill in R) )

Presence of a skill is what counts, not the self-reported proficiency level.
Levels are returned for display only. This keeps the score reproducible and
easy to explain, and it is deliberately **not** a probability of employment.

Only ``required`` skills affect the score. ``optional`` ("bonus") skills are
reported separately so that missing bonuses never penalise a candidate.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.data.occupations import get_occupation
from app.data.skills_taxonomy import get_skill_category, normalize_skill_name
from app.schemas.career import SkillAssessment, SkillContribution, SkillGapResponse

READINESS_DISCLAIMER = (
    "This readiness score measures how much of the target role's curated "
    "required-skill set your profile currently covers. It is a deterministic "
    "coverage metric, not a probability of getting hired and not a guarantee "
    "of employment."
)

# Higher wins when the same skill is listed more than once.
_LEVEL_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3}


def _coerce_level(value: Any) -> str:
    level = str(value or "intermediate").strip().lower()
    return level if level in _LEVEL_RANK else "intermediate"


def normalize_user_skills(
    raw_skills: Optional[List[Any]],
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Normalizes a user's skill list against the canonical taxonomy.

    Accepts entries as dicts ({"name", "level"}) or plain strings.

    Returns:
        (known, unknown)
        known    — canonical skills with the user's highest stated level, sorted
        unknown  — names not present in the taxonomy (original casing, deduped)
    """
    by_name: Dict[str, str] = {}
    unknown: List[str] = []
    unknown_seen = set()

    for item in raw_skills or []:
        if isinstance(item, dict):
            raw_name = item.get("name")
            level = _coerce_level(item.get("level"))
        else:
            raw_name = item
            level = "intermediate"

        if not raw_name or not str(raw_name).strip():
            continue

        canonical = normalize_skill_name(raw_name)
        if not canonical:
            key = str(raw_name).strip()
            if key.lower() not in unknown_seen:
                unknown_seen.add(key.lower())
                unknown.append(key)
            continue

        # Keep the highest level seen for a skill; collapse duplicates.
        if canonical not in by_name or _LEVEL_RANK[level] > _LEVEL_RANK[by_name[canonical]]:
            by_name[canonical] = level

    known = [
        {"name": name, "level": by_name[name]}
        for name in sorted(by_name.keys(), key=lambda n: n.lower())
    ]
    return known, unknown


def compute_readiness(matched_weight: int, total_weight: int) -> int:
    """Deterministic weighted-coverage percentage in [0, 100]."""
    if total_weight <= 0:
        return 0
    return int(round(100.0 * matched_weight / total_weight))


def readiness_band(score: int) -> str:
    """Human-readable band for a readiness score."""
    if score >= 85:
        return "Role-ready"
    if score >= 65:
        return "Proficient"
    if score >= 40:
        return "Developing"
    return "Emerging"


def _sort_assessments(items: List[SkillAssessment]) -> List[SkillAssessment]:
    return sorted(items, key=lambda a: (-a.weight, a.name))


def analyze_skill_gap(
    user_skills: Optional[List[Any]],
    occupation_name: Optional[str],
) -> Optional[SkillGapResponse]:
    """
    Computes the skill-gap analysis for one occupation.

    Returns ``None`` when ``occupation_name`` is empty or does not resolve to a
    known occupation — the caller decides how to surface that (404 / 400).
    """
    occupation = get_occupation(occupation_name)
    if not occupation:
        return None

    known, unknown = normalize_user_skills(user_skills)
    user_map = {s["name"]: s["level"] for s in known}

    def assess(entry: Dict[str, Any]) -> SkillAssessment:
        name = entry["name"]
        matched = name in user_map
        return SkillAssessment(
            name=name,
            category=get_skill_category(name),
            weight=entry["weight"],
            matched=matched,
            user_level=user_map.get(name),
            rationale=(
                f"You have {name} in your skill inventory."
                if matched
                else f"{name} is not in your skill inventory yet."
            ),
        )

    matched_required: List[SkillAssessment] = []
    missing_required: List[SkillAssessment] = []
    for entry in occupation.get("required_skills", []):
        assessment = assess(entry)
        (matched_required if assessment.matched else missing_required).append(assessment)

    matched_bonus: List[SkillAssessment] = []
    missing_bonus: List[SkillAssessment] = []
    for entry in occupation.get("optional_skills", []):
        assessment = assess(entry)
        (matched_bonus if assessment.matched else missing_bonus).append(assessment)

    matched_required = _sort_assessments(matched_required)
    missing_required = _sort_assessments(missing_required)
    matched_bonus = _sort_assessments(matched_bonus)
    missing_bonus = _sort_assessments(missing_bonus)

    total_weight = sum(r.weight for r in (matched_required + missing_required))
    matched_weight = sum(r.weight for r in matched_required)
    score = compute_readiness(matched_weight, total_weight)

    contributions = [
        SkillContribution(name=a.name, weight=a.weight, matched=a.matched)
        for a in _sort_assessments(matched_required + missing_required)
    ]

    explanation = (
        f"{occupation['name']}: you cover {len(matched_required)} of "
        f"{len(matched_required) + len(missing_required)} required skills "
        f"({matched_weight} of {total_weight} importance points), giving a "
        f"readiness of {score}% ({readiness_band(score)}). "
        + (
            "Next focus: " + ", ".join(m.name for m in missing_required[:3]) + "."
            if missing_required
            else "You currently cover every required skill in this catalog."
        )
    )

    return SkillGapResponse(
        occupation_key=occupation["key"],
        occupation_name=occupation["name"],
        occupation_category=occupation["category"],
        target_source="pending",
        readiness_score=score,
        readiness_band=readiness_band(score),
        matched_count=len(matched_required),
        required_count=len(matched_required) + len(missing_required),
        matched_skills=matched_required,
        missing_skills=missing_required,
        bonus_skills=matched_bonus,
        missing_bonus_skills=missing_bonus,
        unknown_skills=unknown,
        contributions=contributions,
        explanation=explanation,
        disclaimer=READINESS_DISCLAIMER,
    )


def get_profile_skills(db, user) -> List[Dict[str, str]]:
    """Reads the student's saved skill inventory from StudentProfile.skills."""
    from app.models.profile import StudentProfile

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile or not profile.skills:
        return []
    return profile.skills
