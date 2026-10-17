"""
Skill prerequisite edges (curated, internal).

Phase 5: Skill dependency graph.

Each edge means: the ``prerequisite`` skill should be learned *before* the
``dependent`` skill. Edges are directed prerequisite -> dependent.

Source
------
``DATA_SOURCE_CURATED`` ("curated") — hand-authored by the CareerGraph AI team.
These relationships are pedagogical guidance curated for this project. They are
**not** official ESCO/O*NET "essential-for" relationships and carry no official
identifiers. Any relationship inferred rather than curated must be tagged with a
different source value (see ``get_edges_by_source``).

Contract
--------
Every ``prerequisite`` and ``dependent`` value must be a canonical skill name
from ``app/data/skills_taxonomy.py``. ``validate_prerequisites()`` verifies this
and ``tests/test_phase5_graph.py`` asserts the graph is acyclic.
"""

from typing import Dict, List

from app.data import DATA_SOURCE_CURATED
from app.data.skills_taxonomy import is_known_skill, normalize_skill_name

PREREQUISITE_SOURCE = DATA_SOURCE_CURATED


def _edge(prerequisite: str, dependent: str, rationale: str) -> Dict[str, str]:
    return {
        "prerequisite": prerequisite,
        "dependent": dependent,
        "rationale": rationale,
        "source": PREREQUISITE_SOURCE,
    }


# ─── Curated prerequisite edges ───────────────────────────────────────────────
PREREQUISITE_EDGES: List[Dict[str, str]] = [
    # ── Programming foundations ──────────────────────────────────────────────
    _edge("Python", "NumPy", "NumPy is a Python library; Python fluency is expected first."),
    _edge("Python", "Pandas", "Pandas is a Python library built on Python data structures."),
    _edge("Python", "Data Structures & Algorithms",
          "Implementing data structures and algorithms requires a working programming language."),
    _edge("Python", "Machine Learning",
          "The machine-learning tooling in this catalog is Python-centric."),
    _edge("Python", "TensorFlow", "TensorFlow's primary API is Python."),
    _edge("NumPy", "Pandas", "Pandas builds on NumPy arrays."),
    _edge("NumPy", "Scikit-learn", "Scikit-learn operates on NumPy arrays."),
    _edge("JavaScript", "TypeScript", "TypeScript is a typed superset of JavaScript."),
    _edge("JavaScript", "React", "React components are written in JavaScript/JSX."),
    _edge("JavaScript", "Vue.js", "Vue components are written in JavaScript."),
    _edge("JavaScript", "Angular", "Angular applications are written in JavaScript/TypeScript."),
    _edge("JavaScript", "Node.js", "Node.js is a JavaScript runtime."),
    _edge("TypeScript", "Angular", "Angular applications are conventionally written in TypeScript."),
    _edge("React", "Next.js", "Next.js is a React framework."),
    _edge("Node.js", "Express.js", "Express.js runs on the Node.js runtime."),

    # ── Web fundamentals ─────────────────────────────────────────────────────
    _edge("HTML", "CSS", "CSS styles HTML documents, so HTML structure comes first."),
    _edge("CSS", "Tailwind CSS", "Tailwind is a CSS utility framework."),

    # ── Data & AI ────────────────────────────────────────────────────────────
    _edge("Statistics", "Machine Learning", "Machine-learning models are trained and evaluated statistically."),
    _edge("Machine Learning", "Deep Learning", "Deep learning is a subfield of machine learning."),
    _edge("Machine Learning", "Natural Language Processing",
          "Modern NLP is built on machine-learning models."),
    _edge("Deep Learning", "PyTorch", "PyTorch is a deep-learning framework."),
    _edge("Deep Learning", "TensorFlow", "TensorFlow is a deep-learning framework."),
    _edge("Pandas", "Data Visualization", "Tabular analysis in Pandas typically precedes plotting results."),

    # ── Databases ────────────────────────────────────────────────────────────
    _edge("SQL", "PostgreSQL", "PostgreSQL is a SQL database; query fundamentals come first."),
    _edge("SQL", "MySQL", "MySQL is a SQL database; query fundamentals come first."),
    _edge("SQL", "SQLite", "SQLite uses SQL; query fundamentals come first."),

    # ── Cloud & DevOps ───────────────────────────────────────────────────────
    _edge("Linux", "Shell / Bash", "Shell scripting is exercised on Unix-like systems."),
    _edge("Linux", "Docker", "Containers are built and run on Linux hosts."),
    _edge("Linux", "AWS", "Cloud instances and CLIs are operated through Linux."),
    _edge("Git", "CI/CD", "Continuous integration pipelines are driven from version control."),
    _edge("Docker", "Kubernetes", "Kubernetes orchestrates containers, so containers come first."),
    _edge("Docker", "Microservices", "Containerisation is the usual deployment model for microservices."),

    # ── Architecture & concepts ──────────────────────────────────────────────
    _edge("REST APIs", "Microservices", "Microservices expose APIs; REST fundamentals come first."),
    _edge("REST APIs", "FastAPI", "FastAPI is used to build REST APIs; REST concepts come first."),
    _edge("REST APIs", "Django", "Django REST Framework builds on REST concepts."),
    _edge("REST APIs", "Express.js", "Express is commonly used to build REST APIs."),
    _edge("Microservices", "System Design", "Designing microservice systems builds on microservice fundamentals."),
    _edge("Object-Oriented Programming", "System Design",
          "Large-system design is commonly expressed through object-oriented models."),

    # ── Security ─────────────────────────────────────────────────────────────
    _edge("Networking", "Penetration Testing", "Testing systems for weaknesses requires understanding networks."),
    _edge("Linux", "Penetration Testing", "Most security tooling runs on Linux."),
    _edge("Shell / Bash", "Penetration Testing", "Security tooling is largely driven from the shell."),
    _edge("Networking", "Cryptography", "Applied cryptography (TLS/SSL) builds on network protocols."),
]


def get_prerequisite_edges() -> List[Dict[str, str]]:
    """Returns a copy of all curated edges (deterministic order)."""
    return [dict(edge) for edge in PREREQUISITE_EDGES]


def get_edges_by_source(source: str) -> List[Dict[str, str]]:
    """Returns edges matching a given source tag (e.g. ``"curated"``)."""
    return [dict(e) for e in PREREQUISITE_EDGES if e.get("source") == source]


def validate_prerequisites() -> List[str]:
    """
    Self-check used by tests. Returns a list of problem strings (empty = valid):
      - prerequisite/dependent must be canonical taxonomy skills
      - no self-loops
      - no duplicate directed edges
      - every edge must carry a rationale and a source tag
    """
    problems: List[str] = []
    seen = set()
    for edge in PREREQUISITE_EDGES:
        pre = edge.get("prerequisite")
        dep = edge.get("dependent")
        for role, value in (("prerequisite", pre), ("dependent", dep)):
            if not is_known_skill(value):
                problems.append(f"{value!r} ({role}) is not a canonical skill")
            elif normalize_skill_name(value) != value:
                problems.append(f"{value!r} ({role}) is not a canonical name")
        if pre == dep:
            problems.append(f"self-loop on {pre!r}")
        pair = (pre, dep)
        if pair in seen:
            problems.append(f"duplicate edge {pre!r} -> {dep!r}")
        seen.add(pair)
        if not edge.get("rationale"):
            problems.append(f"edge {pre!r} -> {dep!r} is missing a rationale")
        if not edge.get("source"):
            problems.append(f"edge {pre!r} -> {dep!r} is missing a source tag")
    return problems
