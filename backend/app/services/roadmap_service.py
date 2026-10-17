"""
Learning-roadmap service — Phase 5B / 5C.

Builds a prerequisite-aware, deterministic learning roadmap from:
  * the user's verified skills (StudentProfile.skills),
  * the target occupation's required skills (Phase 4 catalog),
  * prerequisite dependencies in the skill graph (Phase 5A).

Guarantees
----------
* Prerequisite ordering: a prerequisite never appears *after* the skill that
  depends on it (enforced via topological sort + verified in tests).
* No duplicate steps.
* Skills the user already possesses are reported as ``possessed_skills`` and are
  never scheduled as steps.
* When dependency data is incomplete (unknown skills, or an empty dependency
  graph) the roadmap is flagged ``is_partial`` with a transparent note — the
  service never fabricates certainty.
* Explanations are templated and deterministic. No LLM is used.
"""

from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.data.occupations import get_occupation
from app.data.skills_taxonomy import get_skill_category
from app.models.roadmap import Roadmap, RoadmapStepProgress
from app.models.user import User
from app.schemas.roadmap import (
    PrerequisiteItem,
    RoadmapProgress,
    RoadmapResponse,
    RoadmapStep,
    RoadmapStepUpdateResponse,
    SkillDependencyResponse,
)
from app.services.graph_service import DEFAULT_MAX_DEPTH, BaseSkillGraph
from app.services.skill_gap_service import get_profile_skills, normalize_user_skills

ROADMAP_DISCLAIMER = (
    "This roadmap is generated from a curated skill-dependency graph and the "
    "required skills of the target occupation. Ordering reflects known "
    "prerequisites; it is deterministic guidance, not a guarantee of employment."
)

STATE_PENDING = "pending"
STATE_IN_PROGRESS = "in_progress"
STATE_COMPLETED = "completed"


# ─── Planning (pure, no DB) ───────────────────────────────────────────────────
def build_roadmap_plan(
    graph: BaseSkillGraph,
    owned_skills: Set[str],
    occupation: Dict,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Dict:
    """
    Pure planning step. Returns:
        {
          steps: List[dict],           # ordered, prerequisite-respecting
          possessed_skills: List[str],
          is_partial: bool,
          notes: str,
        }
    """
    required = [r["name"] for r in occupation.get("required_skills", [])]
    required_set = set(required)

    possessed = sorted([s for s in required if s in owned_skills], key=lambda s: s.lower())
    target_skills = [s for s in required if s not in owned_skills]

    # Prerequisites that are missing (not owned, not themselves targets).
    missing_refs = graph.missing_prerequisites(owned_skills, target_skills, max_depth=max_depth)
    depth_by_skill = {ref.name: ref.depth for ref in missing_refs}

    needed: Set[str] = set(target_skills) | set(depth_by_skill.keys())
    needed.discard(None)

    order, unresolved = graph.topological_order(needed, include_prerequisites=False, max_depth=max_depth)

    is_partial = False
    notes: List[str] = []

    unknown_needed = graph.unknown_skills(required)
    if unknown_needed:
        is_partial = True
        notes.append(
            "Some required skills are not in the taxonomy, so their prerequisites "
            f"could not be resolved: {', '.join(unknown_needed)}."
        )

    if graph.edge_count() == 0:
        is_partial = True
        notes.append("No dependency data is available; steps are listed without prerequisite ordering.")

    if unresolved:
        is_partial = True
        cycle = graph.find_cycle(needed) or unresolved
        notes.append(
            "A dependency cycle was detected among: "
            f"{', '.join(cycle)}. Those steps are listed last in a safe order."
        )
        order = order + [s for s in unresolved if s not in order]

    # De-duplicate while preserving order
    seen: Set[str] = set()
    ordered_unique: List[str] = []
    for skill in order:
        if skill not in seen:
            seen.add(skill)
            ordered_unique.append(skill)

    steps: List[dict] = []
    position_of = {skill: i + 1 for i, skill in enumerate(ordered_unique)}
    for idx, skill in enumerate(ordered_unique):
        is_target = skill in required_set
        direct = [
            e.prerequisite
            for e in graph.direct_prerequisites(skill)
            if e.prerequisite in seen
        ]
        steps.append({
            "position": idx + 1,
            "skill": skill,
            "category": get_skill_category(skill),
            "depth": 0 if is_target else depth_by_skill.get(skill, 1),
            "is_target_skill": is_target,
            "prerequisites": sorted(direct, key=lambda s: position_of.get(s, 0)),
            "reason": _step_reason(graph, skill, is_target, occupation["name"], needed),
        })

    return {
        "steps": steps,
        "possessed_skills": possessed,
        "is_partial": is_partial,
        "notes": " ".join(notes) if notes else None,
    }


def _step_reason(
    graph: BaseSkillGraph,
    skill: str,
    is_target: bool,
    occupation_name: str,
    needed: Set[str],
) -> str:
    if is_target:
        return f"{skill} is required for {occupation_name} and is not yet in your profile."

    dependents = sorted(
        {e.dependent for e in graph.direct_dependents(skill) if e.dependent in needed}
    )
    rationale = ""
    for edge in graph.direct_dependents(skill):
        if edge.dependent in needed and edge.rationale:
            rationale = edge.rationale
            break

    if dependents:
        listed = ", ".join(dependents[:2])
        base = f"{skill} is a prerequisite for {listed}."
    else:
        base = f"{skill} supports your target role {occupation_name}."
    return f"{base} {rationale}".strip()


# ─── Persistence ──────────────────────────────────────────────────────────────
def _owned_skills(db: Session, user: User) -> Set[str]:
    known, _unknown = normalize_user_skills(get_profile_skills(db, user))
    return {s["name"] for s in known}


def _archive_active(db: Session, user: User) -> None:
    (
        db.query(Roadmap)
        .filter(Roadmap.user_id == user.id, Roadmap.status == "active")
        .update({Roadmap.status: "archived"}, synchronize_session=False)
    )


def _progress_map(roadmap: Roadmap) -> Dict[str, str]:
    return {row.skill: row.state for row in roadmap.step_progress}


def compute_progress(steps: List[dict], states: Dict[str, str]) -> RoadmapProgress:
    total = len(steps)
    completed = sum(1 for s in steps if states.get(s["skill"]) == STATE_COMPLETED)
    in_progress = sum(1 for s in steps if states.get(s["skill"]) == STATE_IN_PROGRESS)
    percent = int(round(100.0 * completed / total)) if total else 0
    return RoadmapProgress(
        total_steps=total,
        completed_steps=completed,
        in_progress_steps=in_progress,
        percent_complete=percent,
    )


def compute_next_action(steps: List[dict], states: Dict[str, str]) -> Optional[str]:
    if not steps:
        return "No outstanding steps — you already cover this role's required skills."
    for step in steps:
        if states.get(step["skill"]) == STATE_IN_PROGRESS:
            return f"Continue {step['skill']}."
    for step in steps:
        if states.get(step["skill"]) != STATE_COMPLETED:
            return f"Start with {step['skill']} — {step['reason']}"
    return "All roadmap steps completed. Re-run the gap analysis to confirm readiness."


def serialize_roadmap(roadmap: Roadmap) -> RoadmapResponse:
    states = _progress_map(roadmap)
    steps = [
        RoadmapStep(
            position=s["position"],
            skill=s["skill"],
            category=s.get("category"),
            depth=s.get("depth", 0),
            status=states.get(s["skill"], STATE_PENDING),
            is_target_skill=s.get("is_target_skill", False),
            is_mastered=False,
            prerequisites=s.get("prerequisites", []),
            reason=s.get("reason", ""),
        )
        for s in (roadmap.steps or [])
    ]
    progress = compute_progress(roadmap.steps or [], states)
    return RoadmapResponse(
        id=roadmap.id,
        user_id=roadmap.user_id,
        occupation_key=roadmap.occupation_key,
        occupation_name=roadmap.occupation_name,
        occupation_category=roadmap.occupation_category,
        target_source=roadmap.target_source,
        graph_backend=roadmap.graph_backend,
        is_partial=roadmap.is_partial,
        notes=roadmap.notes,
        status=roadmap.status,
        steps=steps,
        possessed_skills=roadmap.possessed_skills or [],
        progress=progress,
        next_action=compute_next_action(roadmap.steps or [], states),
        explanation=(
            f"{roadmap.occupation_name}: {progress.total_steps} step(s) to learn, "
            f"{len(roadmap.possessed_skills or [])} required skill(s) already in your profile. "
            f"{progress.percent_complete}% complete."
        ),
        disclaimer=ROADMAP_DISCLAIMER,
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
    )


def generate_roadmap(
    db: Session,
    user: User,
    graph: BaseSkillGraph,
    occupation_name: Optional[str],
    target_source: str = "request",
    preserve_progress_from: Optional[Roadmap] = None,
) -> Optional[Roadmap]:
    """
    Builds and persists a new active roadmap. Returns ``None`` if the occupation
    is unknown. Archives any previously active roadmap for this user.
    """
    occupation = get_occupation(occupation_name)
    if not occupation:
        return None

    plan = build_roadmap_plan(graph, _owned_skills(db, user), occupation)

    # Carry over progress for skills that remain in the new roadmap.
    preserved: Dict[str, str] = {}
    if preserve_progress_from is not None:
        previous = _progress_map(preserve_progress_from)
        new_skills = {s["skill"] for s in plan["steps"]}
        preserved = {k: v for k, v in previous.items() if k in new_skills}

    _archive_active(db, user)

    roadmap = Roadmap(
        user_id=user.id,
        occupation_key=occupation["key"],
        occupation_name=occupation["name"],
        occupation_category=occupation["category"],
        target_source=target_source,
        graph_backend=graph.source,
        is_partial=plan["is_partial"],
        notes=plan["notes"],
        steps=plan["steps"],
        possessed_skills=plan["possessed_skills"],
        status="active",
    )
    db.add(roadmap)
    db.flush()

    for step in plan["steps"]:
        db.add(RoadmapStepProgress(
            roadmap_id=roadmap.id,
            skill=step["skill"],
            position=step["position"],
            state=preserved.get(step["skill"], STATE_PENDING),
        ))

    db.commit()
    db.refresh(roadmap)
    return roadmap


def get_active_roadmap(db: Session, user: User) -> Optional[Roadmap]:
    return (
        db.query(Roadmap)
        .filter(Roadmap.user_id == user.id, Roadmap.status == "active")
        .order_by(Roadmap.updated_at.desc(), Roadmap.id.desc())
        .first()
    )


def get_roadmap_by_id(db: Session, user: User, roadmap_id: int) -> Optional[Roadmap]:
    """Ownership-scoped lookup — never returns another user's roadmap."""
    return (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, Roadmap.user_id == user.id)
        .first()
    )


def update_step_state(
    db: Session,
    user: User,
    roadmap: Roadmap,
    skill: str,
    state: str,
) -> Optional[RoadmapStepUpdateResponse]:
    """
    Updates one step's progress. Returns ``None`` if the skill is not a step in
    this roadmap (route turns that into a 404).
    """
    step_snapshot = next((s for s in (roadmap.steps or []) if s["skill"] == skill), None)
    if not step_snapshot:
        # Allow case-insensitive canonical match for convenience.
        normalized = {s["skill"].lower(): s for s in (roadmap.steps or [])}
        step_snapshot = normalized.get(skill.strip().lower())
    if not step_snapshot:
        return None

    row = (
        db.query(RoadmapStepProgress)
        .filter(
            RoadmapStepProgress.roadmap_id == roadmap.id,
            RoadmapStepProgress.skill == step_snapshot["skill"],
        )
        .first()
    )
    if row is None:
        row = RoadmapStepProgress(
            roadmap_id=roadmap.id,
            skill=step_snapshot["skill"],
            position=step_snapshot["position"],
            state=state,
        )
        db.add(row)
    else:
        row.state = state

    # Touch the roadmap so updated_at reflects progress changes.
    roadmap.updated_at = roadmap.updated_at
    db.commit()
    db.refresh(roadmap)

    states = _progress_map(roadmap)
    updated_step = RoadmapStep(
        position=step_snapshot["position"],
        skill=step_snapshot["skill"],
        category=step_snapshot.get("category"),
        depth=step_snapshot.get("depth", 0),
        status=states.get(step_snapshot["skill"], STATE_PENDING),
        is_target_skill=step_snapshot.get("is_target_skill", False),
        prerequisites=step_snapshot.get("prerequisites", []),
        reason=step_snapshot.get("reason", ""),
    )
    return RoadmapStepUpdateResponse(
        message=f"Step '{step_snapshot['skill']}' marked as {state}.",
        step=updated_step,
        progress=compute_progress(roadmap.steps or [], states),
        next_action=compute_next_action(roadmap.steps or [], states),
    )


# ─── Dependency inspection ────────────────────────────────────────────────────
def dependency_info(graph: BaseSkillGraph, skill: str, max_depth: int = DEFAULT_MAX_DEPTH) -> SkillDependencyResponse:
    from app.data.skills_taxonomy import normalize_skill_name

    canonical = normalize_skill_name(skill)
    if not canonical:
        return SkillDependencyResponse(
            skill=skill,
            known=False,
            unknown_related=[skill],
        )

    prerequisites = [
        PrerequisiteItem(
            skill=ref.name,
            depth=ref.depth,
            category=ref.category,
            rationale=ref.rationale,
            source=ref.source,
        )
        for ref in graph.transitive_prerequisites(canonical, max_depth=max_depth)
    ]
    dependents = [
        PrerequisiteItem(
            skill=edge.dependent,
            depth=1,
            category=get_skill_category(edge.dependent),
            rationale=edge.rationale,
            source=edge.source,
        )
        for edge in graph.direct_dependents(canonical)
    ]
    return SkillDependencyResponse(
        skill=canonical,
        known=True,
        category=get_skill_category(canonical),
        has_prerequisites=bool(prerequisites),
        prerequisites=prerequisites,
        dependents=dependents,
    )
