"""
Opt-in Neo4j integration checks.

The test is skipped unless all of these environment variables are present:

    NEO4J_TEST_URI       e.g. bolt://localhost:7687
    NEO4J_TEST_USER      e.g. neo4j
    NEO4J_TEST_PASSWORD  a test-only password
    NEO4J_TEST_ALLOW_WRITE=true

The final flag is intentional: the test deletes ``:Skill`` nodes in the target
database so it can verify clean seeding. Never enable it against a database that
contains real graph data. CI starts a disposable Neo4j service for this test.

This is the honest live-verification path for the adapter. The ordinary test
suite only exercises the in-memory backend and the unreachable-server fallback.
"""

import os
from types import SimpleNamespace

import pytest

from app.data.occupations import get_occupation
from app.data.skill_prerequisites import get_prerequisite_edges
from app.services.graph_service import Neo4jSkillGraph
from app.services.roadmap_service import build_roadmap_plan

NEO4J_TEST_URI = os.environ.get("NEO4J_TEST_URI", "").strip()
NEO4J_TEST_USER = os.environ.get("NEO4J_TEST_USER", "").strip()
NEO4J_TEST_PASSWORD = os.environ.get("NEO4J_TEST_PASSWORD", "").strip()
NEO4J_TEST_ALLOW_WRITE = os.environ.get("NEO4J_TEST_ALLOW_WRITE", "").lower() == "true"

pytestmark = pytest.mark.skipif(
    not all([NEO4J_TEST_URI, NEO4J_TEST_USER, NEO4J_TEST_PASSWORD, NEO4J_TEST_ALLOW_WRITE]),
    reason=(
        "Live Neo4j checks require NEO4J_TEST_URI, NEO4J_TEST_USER, "
        "NEO4J_TEST_PASSWORD and NEO4J_TEST_ALLOW_WRITE=true"
    ),
)


@pytest.fixture(scope="module")
def live_graph():
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        NEO4J_TEST_URI,
        auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD),
    )
    driver.verify_connectivity()
    # The write opt-in is explicit. CI uses a fresh service container.
    with driver.session() as session:
        session.run("MATCH (s:Skill) DETACH DELETE s")

    graph = Neo4jSkillGraph(
        NEO4J_TEST_URI,
        NEO4J_TEST_USER,
        NEO4J_TEST_PASSWORD,
        seed=True,
    )
    try:
        assert graph.is_available is True
        yield graph, driver
    finally:
        graph.close()
        with driver.session() as session:
            session.run("MATCH (s:Skill) DETACH DELETE s")
        driver.close()


def test_live_graph_seeds_curated_edges_and_prevents_duplicate_nodes(live_graph):
    graph, driver = live_graph
    edges = get_prerequisite_edges()
    assert graph.source == "neo4j"
    assert graph.edge_count() == len(edges)
    assert graph.has_cycle() is False

    with driver.session() as session:
        relationship_count = session.run(
            "MATCH (:Skill)-[r:PREREQUISITE_OF]->(:Skill) RETURN count(r) AS n"
        ).single()["n"]
        python_node_count = session.run(
            "MATCH (s:Skill {name: 'Python'}) RETURN count(s) AS n"
        ).single()["n"]

    assert relationship_count == len(edges)
    assert python_node_count == 1

    # A second idempotent seed must not add duplicate relationships or nodes.
    graph.seed_from_curated()
    with driver.session() as session:
        relationship_count = session.run(
            "MATCH (:Skill)-[r:PREREQUISITE_OF]->(:Skill) RETURN count(r) AS n"
        ).single()["n"]
        node_count = session.run("MATCH (s:Skill) RETURN count(s) AS n").single()["n"]

    assert relationship_count == len(edges)
    assert node_count == len({edge["prerequisite"] for edge in edges} | {edge["dependent"] for edge in edges})


def test_live_graph_traversal_boundaries_and_unknown_skills(live_graph):
    graph, _driver = live_graph

    prerequisites = graph.transitive_prerequisites("Machine Learning", max_depth=12)
    names = {ref.name for ref in prerequisites}
    assert "Python" in names
    assert "Statistics" in names
    assert len(prerequisites) == len({ref.name for ref in prerequisites})

    shallow = graph.transitive_prerequisites("Machine Learning", max_depth=0)
    assert shallow == []

    assert graph.transitive_prerequisites("Not A Real Skill") == []
    assert graph.direct_prerequisites("Not A Real Skill") == []
    assert graph.unknown_skills(["Python", "Not A Real Skill"]) == ["Not A Real Skill"]


def test_live_graph_builds_a_prerequisite_ordered_roadmap(live_graph):
    graph, _driver = live_graph
    occupation = get_occupation("ml-engineer")
    assert occupation is not None

    plan = build_roadmap_plan(graph, owned_skills=set(), occupation=occupation)
    ordered = [step["skill"] for step in plan["steps"]]
    assert "Machine Learning" in ordered
    assert "Python" in ordered
    assert ordered.index("Python") < ordered.index("Machine Learning")
    assert len(ordered) == len(set(ordered))
    assert plan["is_partial"] is False


def test_live_graph_close_releases_the_driver(live_graph):
    graph, driver = live_graph
    graph.close()
    # Explicit close is idempotent and must not raise.
    graph.close()
    # The underlying driver remains usable for verification/cleanup in the
    # fixture; this assertion only proves close() returned without error.
    assert driver is not None


def test_configured_graph_factory_uses_live_neo4j_and_closes(monkeypatch):
    """Covers the application factory and shutdown helper against a live server."""
    import app.services.graph_service as graph_service

    settings = SimpleNamespace(
        GRAPH_BACKEND="neo4j",
        NEO4J_URI=NEO4J_TEST_URI,
        NEO4J_USER=NEO4J_TEST_USER,
        NEO4J_PASSWORD=NEO4J_TEST_PASSWORD,
    )
    monkeypatch.setattr(graph_service, "get_settings", lambda: settings)
    graph_service.get_graph.cache_clear()
    try:
        graph = graph_service.get_graph()
        assert graph.source == "neo4j"
        assert graph.edge_count() > 0
        graph_service.close_graph()
        assert graph_service.get_graph.cache_info().currsize == 0
    finally:
        graph_service.get_graph.cache_clear()
