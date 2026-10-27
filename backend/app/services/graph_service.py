"""
Skill dependency graph service — Phase 5A.

Design
------
``BaseSkillGraph`` holds the *algorithms* (traversal, gap discovery, topological
ordering, cycle detection) and operates on an in-memory edge set. Two backends
share it:

  * ``InMemorySkillGraph`` — the default, always available, loaded from the
    curated edge data. This is what the test-suite exercises.
  * ``Neo4jSkillGraph`` — persists edges in Neo4j and loads them via Cypher.
    The traversal/ordering algorithms are then identical to the in-memory
    backend, which keeps behaviour deterministic and testable.

Honesty note
------------
The Neo4j backend has opt-in live integration tests and is exercised by the CI
``integration`` job against a disposable Neo4j 5.24 service container. A local
live server is not required: if a driver or server is missing, :func:`get_graph`
logs a warning and falls back to the in-memory backend rather than failing. The
ordinary unit suite uses the in-memory backend and this fallback path.

All skills are identified by their canonical taxonomy name. Non-canonical names
are rejected/ignored rather than fabricated.
"""

from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Set, Tuple

from app.config import get_settings
from app.data.skill_prerequisites import (
    PREREQUISITE_SOURCE,
    get_prerequisite_edges,
)
from app.data.skills_taxonomy import get_skill_category, is_known_skill, normalize_skill_name

logger = logging.getLogger(__name__)

DEFAULT_MAX_DEPTH = 12


@dataclass(frozen=True)
class DependencyEdge:
    prerequisite: str
    dependent: str
    rationale: str = ""
    source: str = PREREQUISITE_SOURCE


@dataclass(frozen=True)
class PrerequisiteRef:
    """A prerequisite skill discovered relative to some target skill."""
    name: str
    depth: int
    category: Optional[str] = None
    rationale: str = ""
    source: str = PREREQUISITE_SOURCE


class BaseSkillGraph:
    """Shared, backend-agnostic graph algorithms."""

    source = "base"

    def __init__(self, edges: Optional[Sequence[DependencyEdge]] = None):
        # dependent -> list of edges pointing in
        self._prereqs: Dict[str, List[DependencyEdge]] = {}
        # prerequisite -> list of edges pointing out
        self._dependents: Dict[str, List[DependencyEdge]] = {}
        self._edges: List[DependencyEdge] = []
        self._edge_keys: Set[Tuple[str, str]] = set()
        self._nodes: Set[str] = set()
        for edge in edges or []:
            self.add_edge(edge.prerequisite, edge.dependent, edge.rationale, edge.source)

    # ── Mutation ────────────────────────────────────────────────────────────
    def add_edge(
        self,
        prerequisite: str,
        dependent: str,
        rationale: str = "",
        source: str = PREREQUISITE_SOURCE,
    ) -> bool:
        """
        Adds a directed prerequisite -> dependent edge.

        Returns ``False`` (no-op) when the edge is rejected: non-canonical skill
        name, self-loop, or duplicate. Rejecting rather than guessing keeps the
        graph free of fabricated identifiers.
        """
        pre = normalize_skill_name(prerequisite)
        dep = normalize_skill_name(dependent)
        if not pre or not dep or pre == dep:
            return False
        key = (pre, dep)
        if key in self._edge_keys:
            return False

        edge = DependencyEdge(prerequisite=pre, dependent=dep, rationale=rationale, source=source)
        self._edge_keys.add(key)
        self._edges.append(edge)
        self._prereqs.setdefault(dep, []).append(edge)
        self._dependents.setdefault(pre, []).append(edge)
        self._nodes.add(pre)
        self._nodes.add(dep)
        return True

    # ── Introspection ───────────────────────────────────────────────────────
    def edge_count(self) -> int:
        return len(self._edges)

    def node_count(self) -> int:
        return len(self._nodes)

    def has_node(self, skill: str) -> bool:
        canonical = normalize_skill_name(skill)
        return bool(canonical and canonical in self._nodes)

    def is_known_skill(self, skill: str) -> bool:
        return is_known_skill(skill)

    def edges(self) -> List[DependencyEdge]:
        """All edges, deterministically ordered."""
        return sorted(self._edges, key=lambda e: (e.dependent, e.prerequisite))

    def unknown_skills(self, skills: Sequence[str]) -> List[str]:
        """Returns the subset of names that are not canonical taxonomy skills."""
        out: List[str] = []
        seen = set()
        for name in skills or []:
            if not name or not str(name).strip():
                continue
            canonical = normalize_skill_name(name)
            if canonical:
                continue
            key = str(name).strip().lower()
            if key not in seen:
                seen.add(key)
                out.append(str(name).strip())
        return sorted(out, key=lambda n: n.lower())

    def direct_prerequisites(self, skill: str) -> List[DependencyEdge]:
        canonical = normalize_skill_name(skill)
        if not canonical:
            return []
        return sorted(self._prereqs.get(canonical, []), key=lambda e: e.prerequisite)

    def direct_dependents(self, skill: str) -> List[DependencyEdge]:
        canonical = normalize_skill_name(skill)
        if not canonical:
            return []
        return sorted(self._dependents.get(canonical, []), key=lambda e: e.dependent)

    # ── Traversal ───────────────────────────────────────────────────────────
    def transitive_prerequisites(self, skill: str, max_depth: int = DEFAULT_MAX_DEPTH) -> List[PrerequisiteRef]:
        """
        Breadth-first traversal collecting all prerequisites of ``skill`` up to
        ``max_depth`` hops. Cycle-safe, de-duplicated, deterministic ordering
        (depth, then name).
        """
        canonical = normalize_skill_name(skill)
        if not canonical:
            return []

        depth_limit = max(0, int(max_depth))
        best_depth: Dict[str, int] = {}
        rationale_by_name: Dict[str, str] = {}
        source_by_name: Dict[str, str] = {}

        frontier = [canonical]
        visited = {canonical}
        depth = 0
        while frontier and depth < depth_limit:
            depth += 1
            next_frontier: List[str] = []
            for node in sorted(frontier):
                for edge in self.direct_prerequisites(node):
                    pre = edge.prerequisite
                    if pre not in best_depth:
                        best_depth[pre] = depth
                        rationale_by_name[pre] = edge.rationale
                        source_by_name[pre] = edge.source
                    if pre not in visited:
                        visited.add(pre)
                        next_frontier.append(pre)
            frontier = next_frontier

        refs = [
            PrerequisiteRef(
                name=name,
                depth=d,
                category=get_skill_category(name),
                rationale=rationale_by_name.get(name, ""),
                source=source_by_name.get(name, PREREQUISITE_SOURCE),
            )
            for name, d in best_depth.items()
        ]
        return sorted(refs, key=lambda r: (r.depth, r.name))

    def missing_prerequisites(
        self,
        owned_skills: Sequence[str],
        target_skills: Sequence[str],
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> List[PrerequisiteRef]:
        """
        Prerequisites required by ``target_skills`` that are NOT already owned.

        Target skills themselves are never returned. Result is deterministic and
        de-duplicated (minimum depth wins).
        """
        owned = {normalize_skill_name(s) for s in (owned_skills or [])}
        owned.discard(None)

        targets: List[str] = []
        for s in target_skills or []:
            canonical = normalize_skill_name(s)
            if canonical:
                targets.append(canonical)
        target_set = set(targets)

        best: Dict[str, PrerequisiteRef] = {}
        for target in sorted(target_set):
            for ref in self.transitive_prerequisites(target, max_depth=max_depth):
                if ref.name in owned or ref.name in target_set:
                    continue
                current = best.get(ref.name)
                if current is None or ref.depth < current.depth:
                    best[ref.name] = ref

        return sorted(best.values(), key=lambda r: (r.depth, r.name))

    # ── Ordering & cycles ───────────────────────────────────────────────────
    def topological_order(
        self,
        skills: Sequence[str],
        include_prerequisites: bool = True,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> Tuple[List[str], List[str]]:
        """
        Deterministic topological order (prerequisites before dependents).

        Returns ``(order, unresolved)`` where ``unresolved`` is non-empty only
        when the induced subgraph contains a cycle. Deterministic because ready
        nodes are always taken in lexicographic order.
        """
        nodes: Set[str] = set()
        for s in skills or []:
            canonical = normalize_skill_name(s)
            if canonical:
                nodes.add(canonical)

        if include_prerequisites:
            for s in sorted(nodes):
                for ref in self.transitive_prerequisites(s, max_depth=max_depth):
                    nodes.add(ref.name)

        indegree: Dict[str, int] = {n: 0 for n in nodes}
        adjacency: Dict[str, List[str]] = {n: [] for n in nodes}
        for edge in self._edges:
            if edge.prerequisite in nodes and edge.dependent in nodes:
                adjacency[edge.prerequisite].append(edge.dependent)
                indegree[edge.dependent] += 1

        ready = [n for n in nodes if indegree[n] == 0]
        heapq.heapify(ready)

        order: List[str] = []
        while ready:
            node = heapq.heappop(ready)
            order.append(node)
            for dep in sorted(adjacency[node]):
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    heapq.heappush(ready, dep)

        unresolved = sorted(n for n in nodes if indegree[n] > 0)
        return order, unresolved

    def find_cycle(self, max_nodes: Optional[Sequence[str]] = None) -> Optional[List[str]]:
        """
        Returns one cycle as a list of skill names, or ``None`` if acyclic.

        Optional ``max_nodes`` restricts the search to an induced subgraph.
        """
        allowed = None
        if max_nodes is not None:
            allowed = {normalize_skill_name(n) for n in max_nodes}
            allowed.discard(None)

        WHITE, GREY, BLACK = 0, 1, 2
        color: Dict[str, int] = {}
        path: List[str] = []

        def visit(node: str) -> Optional[List[str]]:
            color[node] = GREY
            path.append(node)
            for edge in self.direct_dependents(node):
                nxt = edge.dependent
                if allowed is not None and nxt not in allowed:
                    continue
                if color.get(nxt, WHITE) == GREY:
                    return path[path.index(nxt):] + [nxt]
                if color.get(nxt, WHITE) == WHITE:
                    found = visit(nxt)
                    if found:
                        return found
            path.pop()
            color[node] = BLACK
            return None

        roots = sorted(allowed) if allowed is not None else sorted(self._nodes)
        for root in roots:
            if color.get(root, WHITE) == WHITE:
                found = visit(root)
                if found:
                    return found
        return None

    def has_cycle(self) -> bool:
        return self.find_cycle() is not None


class InMemorySkillGraph(BaseSkillGraph):
    """Default backend — loaded from the curated edge data."""

    source = "memory"

    def __init__(self, edges: Optional[Sequence[DependencyEdge]] = None):
        if edges is None:
            edges = [
                DependencyEdge(
                    prerequisite=e["prerequisite"],
                    dependent=e["dependent"],
                    rationale=e.get("rationale", ""),
                    source=e.get("source", PREREQUISITE_SOURCE),
                )
                for e in get_prerequisite_edges()
            ]
        super().__init__(edges)


class Neo4jSkillGraph(BaseSkillGraph):
    """
    Neo4j-backed store.

    Persists skills/relationships in Neo4j and loads edges via Cypher, then
    reuses the shared algorithms. ``is_available`` is False when the driver or
    server is unavailable, and :func:`get_graph` falls back to in-memory.

    NOTE: unverified against a live Neo4j in this environment.
    """

    source = "neo4j"

    def __init__(self, uri: str, user: str, password: str, seed: bool = True):
        self.is_available = False
        self._driver = None
        self._loading = False
        super().__init__([])
        try:
            from neo4j import GraphDatabase  # local import — optional dependency
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("Neo4j driver not installed (%s); graph backend unavailable.", exc)
            return
        driver = None
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver = driver
            self._driver.verify_connectivity()
            self.is_available = True
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("Neo4j unreachable at %s (%s); falling back to in-memory.", uri, exc)
            if driver is not None:
                try:
                    driver.close()
                except Exception:
                    pass
            self._driver = None
            self.is_available = False
            return

        try:
            if seed:
                self.seed_from_curated()
            # Reloading should not re-persist every edge it just read.
            self._loading = True
            self._reload()
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("Neo4j graph initialisation failed (%s); falling back to in-memory.", exc)
            self.close()
            self.is_available = False
        finally:
            self._loading = False

    # ── Persistence ─────────────────────────────────────────────────────────
    def seed_from_curated(self) -> int:
        """Merges the curated skills/edges into Neo4j. Idempotent."""
        if not self._driver:
            return 0
        edges = [
            DependencyEdge(
                prerequisite=e["prerequisite"],
                dependent=e["dependent"],
                rationale=e.get("rationale", ""),
                source=e.get("source", PREREQUISITE_SOURCE),
            )
            for e in get_prerequisite_edges()
        ]
        query = (
            "UNWIND $rows AS row "
            "MERGE (p:Skill {name: row.prerequisite}) "
            "MERGE (d:Skill {name: row.dependent}) "
            "MERGE (p)-[r:PREREQUISITE_OF]->(d) "
            "SET r.rationale = row.rationale, r.source = row.source "
            "RETURN count(r) AS n"
        )
        rows = [e.__dict__ for e in edges]
        with self._driver.session() as session:
            result = session.run(query, rows=rows)
            return int(result.single()["n"])

    def _reload(self) -> None:
        """Rebuilds the in-memory edge set from Neo4j."""
        if not self._driver:
            return
        self._prereqs.clear()
        self._dependents.clear()
        self._edges.clear()
        self._edge_keys.clear()
        self._nodes.clear()
        query = (
            "MATCH (p:Skill)-[r:PREREQUISITE_OF]->(d:Skill) "
            "RETURN p.name AS prerequisite, d.name AS dependent, "
            "r.rationale AS rationale, r.source AS source"
        )
        with self._driver.session() as session:
            for record in session.run(query):
                self.add_edge(
                    record["prerequisite"],
                    record["dependent"],
                    record.get("rationale") or "",
                    record.get("source") or PREREQUISITE_SOURCE,
                )

    def add_edge(self, prerequisite, dependent, rationale="", source=PREREQUISITE_SOURCE) -> bool:
        added = super().add_edge(prerequisite, dependent, rationale, source)
        if added and getattr(self, "_driver", None) and not getattr(self, "_loading", False):
            query = (
                "MERGE (p:Skill {name: $pre}) "
                "MERGE (d:Skill {name: $dep}) "
                "MERGE (p)-[r:PREREQUISITE_OF]->(d) "
                "SET r.rationale = $rationale, r.source = $source"
            )
            try:
                with self._driver.session() as session:
                    session.run(query, pre=prerequisite, dep=dependent, rationale=rationale, source=source)
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to persist edge to Neo4j: %s", exc)
        return added

    def close(self) -> None:
        if self._driver:
            try:
                self._driver.close()
            except Exception:  # pragma: no cover
                pass


@lru_cache(maxsize=1)
def get_graph() -> BaseSkillGraph:
    """
    Returns the configured skill graph.

    Uses Neo4j only when ``GRAPH_BACKEND=neo4j`` AND the server is reachable.
    Otherwise returns the always-available in-memory graph.
    """
    settings = get_settings()
    backend = (getattr(settings, "GRAPH_BACKEND", "memory") or "memory").strip().lower()
    if backend == "neo4j":
        try:
            graph = Neo4jSkillGraph(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            if getattr(graph, "is_available", False):
                logger.info("Skill graph backend: neo4j (%s)", settings.NEO4J_URI)
                return graph
            logger.warning("Neo4j requested but unavailable; using in-memory skill graph.")
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("Neo4j graph backend failed to initialise (%s); using in-memory.", exc)
    return InMemorySkillGraph()


def close_graph() -> None:
    """
    Releases a cached Neo4j driver during application shutdown.

    In-memory graphs have nothing to release. Clearing the lru_cache prevents a
    closed driver from being handed out if the process initialises the app again
    (for example in a test harness).
    """
    graph = get_graph()
    close = getattr(graph, "close", None)
    if callable(close):
        close()
    get_graph.cache_clear()
