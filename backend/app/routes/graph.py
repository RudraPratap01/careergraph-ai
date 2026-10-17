"""
Graph routes — Phase 5A: skill dependency inspection.

GET /graph/stats              backend + size + acyclicity
GET /graph/skills/{skill}     prerequisites and dependents for a skill
"""

from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.schemas.roadmap import SkillDependencyResponse
from app.services.graph_service import DEFAULT_MAX_DEPTH, get_graph
from app.services.roadmap_service import dependency_info
from app.utils.security import get_current_user

router = APIRouter(prefix="/graph", tags=["Skill Graph (Phase 5)"])


@router.get(
    "/stats",
    summary="Skill-graph backend and size",
)
def graph_stats(current_user: User = Depends(get_current_user)):
    """Reports which graph backend is active and basic graph statistics."""
    graph = get_graph()
    return {
        "backend": graph.source,
        "nodes": graph.node_count(),
        "edges": graph.edge_count(),
        "has_cycle": graph.has_cycle(),
        "source": "curated",
    }


@router.get(
    "/skills/{skill}",
    response_model=SkillDependencyResponse,
    summary="Inspect the prerequisites and dependents of a skill",
)
def skill_dependencies(
    skill: str,
    max_depth: int = Query(DEFAULT_MAX_DEPTH, ge=1, le=25, description="Traversal depth bound"),
    current_user: User = Depends(get_current_user),
):
    """
    Returns transitive prerequisites and direct dependents.

    Unknown skills are reported with ``known=false`` rather than guessed.
    """
    return dependency_info(get_graph(), skill, max_depth=max_depth)
