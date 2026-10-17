"""
Phase 5A tests — skill dependency graph.

Covers:
  * duplicate-edge prevention, self-loops, unknown-skill rejection
  * transitive traversal with depth bounds and deterministic ordering
  * missing-prerequisite discovery
  * topological ordering invariant (prerequisite never after dependent)
  * cycle detection
  * graph is acyclic by construction
"""

from app.data.skill_prerequisites import get_edges_by_source, validate_prerequisites
from app.services.graph_service import (
    DependencyEdge,
    InMemorySkillGraph,
    get_graph,
)


def test_curated_graph_is_valid_and_acyclic():
    assert validate_prerequisites() == []
    graph = InMemorySkillGraph()
    assert graph.edge_count() > 0
    assert graph.has_cycle() is False
    assert graph.find_cycle() is None
    # Every curated edge is tagged with a source (never fabricated).
    assert all(e["source"] == "curated" for e in get_edges_by_source("curated"))


def test_default_backend_is_in_memory():
    assert get_graph().source == "memory"


def test_add_edge_rejects_duplicates_selfloops_and_unknowns():
    graph = InMemorySkillGraph()
    # React -> Next.js already exists in the curated data.
    assert graph.add_edge("React", "Next.js") is False
    # Self-loop rejected.
    assert graph.add_edge("React", "React") is False
    # Unknown (non-canonical) skills rejected — never fabricated.
    assert graph.add_edge("Left-Pad", "Moment.js") is False
    # Alias resolves to canonical and is still a duplicate.
    assert graph.add_edge("react", "nextjs") is False
    # A genuinely new, non-duplicate edge is accepted.
    before = graph.edge_count()
    assert graph.add_edge("Rust", "C++") is True
    assert graph.edge_count() == before + 1


def test_direct_prerequisites_are_sorted_and_canonical():
    graph = InMemorySkillGraph()
    prereqs = [e.prerequisite for e in graph.direct_prerequisites("Deep Learning")]
    assert prereqs == ["Machine Learning"]


def test_transitive_traversal_respects_depth_bound():
    graph = InMemorySkillGraph()
    depth1 = graph.transitive_prerequisites("Deep Learning", max_depth=1)
    assert [r.name for r in depth1] == ["Machine Learning"]

    depth2 = graph.transitive_prerequisites("Deep Learning", max_depth=2)
    assert [(r.name, r.depth) for r in depth2] == [
        ("Machine Learning", 1),
        ("Python", 2),
        ("Statistics", 2),
    ]

    # Bounded traversal must terminate even for a large depth on a cyclic graph.
    assert graph.transitive_prerequisites("Deep Learning", max_depth=50)


def test_transitive_traversal_ignores_unknown_skill():
    graph = InMemorySkillGraph()
    assert graph.transitive_prerequisites("Teleportation") == []


def test_missing_prerequisites_excludes_owned_and_targets():
    graph = InMemorySkillGraph()
    missing = graph.missing_prerequisites(
        owned_skills=["Python"],
        target_skills=["Deep Learning"],
    )
    names = [r.name for r in missing]
    assert "Python" not in names          # already owned
    assert "Deep Learning" not in names   # it is the target, not a prerequisite
    assert names == ["Machine Learning", "Statistics"]


def test_topological_order_places_prerequisites_first():
    graph = InMemorySkillGraph()
    skills = ["Machine Learning", "Deep Learning", "PyTorch", "Data Visualization", "Pandas"]
    order, unresolved = graph.topological_order(skills, include_prerequisites=False)
    assert unresolved == []

    index = {skill: i for i, skill in enumerate(order)}
    node_set = set(order)
    for edge in graph.edges():
        if edge.prerequisite in node_set and edge.dependent in node_set:
            assert index[edge.prerequisite] < index[edge.dependent], (
                f"{edge.prerequisite} must come before {edge.dependent}"
            )


def test_topological_order_is_deterministic():
    graph = InMemorySkillGraph()
    skills = ["System Design", "Microservices", "REST APIs", "Docker", "Kubernetes", "Linux"]
    first, _ = graph.topological_order(skills)
    second, _ = graph.topological_order(skills)
    assert first == second


def test_cycle_detection_detects_and_reports_cycle():
    graph = InMemorySkillGraph(edges=[])
    assert graph.add_edge("React", "Next.js") is True
    assert graph.add_edge("Next.js", "Vue.js") is True
    assert graph.add_edge("Vue.js", "React") is True

    assert graph.has_cycle() is True
    cycle = graph.find_cycle()
    assert cycle is not None
    assert cycle[0] == cycle[-1]          # closes the loop
    assert set(cycle) == {"React", "Next.js", "Vue.js"}

    order, unresolved = graph.topological_order(["React", "Next.js", "Vue.js"])
    assert order == []                    # nothing can be safely ordered
    assert set(unresolved) == {"React", "Next.js", "Vue.js"}


def test_empty_graph_behaviour():
    graph = InMemorySkillGraph(edges=[])
    assert graph.edge_count() == 0
    assert graph.node_count() == 0
    assert graph.has_cycle() is False
    order, unresolved = graph.topological_order(["Python", "SQL"])
    assert order == ["Python", "SQL"]     # alphabetical, deterministic
    assert unresolved == []


def test_explicit_edge_construction():
    graph = InMemorySkillGraph(edges=[DependencyEdge("SQL", "PostgreSQL", "rationale", "curated")])
    assert graph.edge_count() == 1
    assert graph.has_node("PostgreSQL")
    assert [e.dependent for e in graph.direct_dependents("SQL")] == ["PostgreSQL"]


# ─── Neo4j fallback (adapter is unverified, but the fallback must be real) ────
def test_neo4j_backend_falls_back_to_memory_when_unreachable(monkeypatch):
    """
    With GRAPH_BACKEND=neo4j and no reachable server, get_graph() must return the
    in-memory graph (and not raise). Port 1 on localhost is guaranteed to refuse.
    """
    from types import SimpleNamespace

    import app.services.graph_service as gs

    fake_settings = SimpleNamespace(
        GRAPH_BACKEND="neo4j",
        NEO4J_URI="bolt://127.0.0.1:1",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="unused",
    )
    monkeypatch.setattr(gs, "get_settings", lambda: fake_settings)
    gs.get_graph.cache_clear()
    try:
        graph = gs.get_graph()
        assert graph.source == "memory"
        assert graph.edge_count() > 0
    finally:
        gs.get_graph.cache_clear()
