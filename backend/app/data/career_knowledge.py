"""
Curated career-learning knowledge base for Phase 7.

What this module *is*
---------------------
A deterministic, in-repo corpus assembled from the same curated data the rest of
CareerGraph uses: the occupation catalog, the skill taxonomy, prerequisite
edges, and the assessment bank. It also contains short hand-authored guidance
notes about how the platform's evidence and scores work.

What this module *is not*
-------------------------
* It is **not** a web crawler and it is **not** an official course catalog.
* It contains **no course URLs** and makes no claim that a resource is
  accredited, complete, or current.
* No embeddings or vector database are used. The retriever in
  ``career_intelligence_service`` performs lexical BM25 scoring over these
  chunks. That is useful for a small curated corpus, but it is not semantic
  search and is described that way in the API and UI.

Documents are normalized and chunked at startup (lazily, then cached). Chunk
IDs are stable, so source citations remain reproducible across requests and
tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from app.data.assessments import ASSESSMENTS
from app.data.occupations import get_occupation, list_occupations
from app.data.skill_prerequisites import get_prerequisite_edges
from app.data.skills_taxonomy import all_canonical_skills, get_skill_category

KNOWLEDGE_SOURCE = "curated"
DEFAULT_CHUNK_CHARS = 700
DEFAULT_CHUNK_OVERLAP = 90


@dataclass(frozen=True)
class KnowledgeChunk:
    """One retrievable, source-attributed unit of text."""

    id: str
    document_id: str
    title: str
    source: str
    source_label: str
    kind: str
    chunk_index: int
    text: str


# ─── Hand-authored guidance ───────────────────────────────────────────────────
# These notes describe the platform honestly and give general, non-certifying
# learning advice. They deliberately contain no external links.
_GUIDANCE: Tuple[Dict[str, str], ...] = (
    {
        "id": "readiness",
        "title": "How the readiness metric works",
        "source": "curated://guidance/readiness",
        "kind": "platform-guide",
        "text": (
            "Career readiness is a deterministic weighted-coverage metric. It compares "
            "the canonical required skills on your profile with the target occupation's "
            "curated required-skill list. Each required skill has an importance weight "
            "from one to five. The score is the matched weight divided by the total "
            "required weight, rounded to a percentage. Presence counts; the level you "
            "state is display-only and does not change the score. Optional bonus skills "
            "never lower the score. The result is not a probability of being hired, not "
            "a prediction, and not a guarantee of employment. Use it to choose what to "
            "learn next, not to compare yourself with other people."
        ),
    },
    {
        "id": "roadmap-order",
        "title": "Why roadmap steps have an order",
        "source": "curated://guidance/roadmap-order",
        "kind": "platform-guide",
        "text": (
            "Roadmaps combine the target occupation's missing required skills with the "
            "curated prerequisite graph. A prerequisite is scheduled before the skill it "
            "supports, using a deterministic topological order. Skills already on your "
            "profile are reported as possessed and are not scheduled. A prerequisite "
            "that is itself missing is added as an earlier step. If the graph is "
            "incomplete, a required skill is not in the taxonomy, or a cycle exists, "
            "the roadmap is marked partial and explains the limitation instead of "
            "guessing. The roadmap is guidance; it does not guarantee a job or a "
            "specific salary."
        ),
    },
    {
        "id": "evidence",
        "title": "Skill evidence and provenance",
        "source": "curated://guidance/evidence",
        "kind": "platform-guide",
        "text": (
            "A skill can enter your profile as self-reported, extracted from a resume "
            "you reviewed, detected from public GitHub metadata, or evidenced by a passed "
            "curated assessment. A resume extraction and a GitHub detection are "
            "suggestions until you confirm them. A LinkedIn link is self-declared and "
            "unverified because LinkedIn does not expose a public profile-reading API. "
            "Assessment passes are evidence from a small curated question bank, not an "
            "official certification. Confirming new evidence never silently downgrades "
            "an existing assessment or GitHub source."
        ),
    },
    {
        "id": "learning-loop",
        "title": "A practical learning loop",
        "source": "curated://guidance/learning-loop",
        "kind": "career-guide",
        "text": (
            "A useful loop is: review the current gap, pick one high-importance missing "
            "skill whose prerequisites you already have, learn a small focused unit, "
            "build something that uses it, write down what you can now explain, and "
            "update the roadmap. Keep the artifact small enough to finish. Prefer one "
            "completed project with a clear explanation over several unfinished "
            "tutorials. Ask a mentor for feedback on a specific decision or artifact, "
            "not for a generic promise about hiring. Re-run the analysis after you add "
            "confirmed skills so the deterministic score reflects the new evidence."
        ),
    },
    {
        "id": "portfolio",
        "title": "Turning skills into portfolio evidence",
        "source": "curated://guidance/portfolio",
        "kind": "career-guide",
        "text": (
            "Choose a project that forces you to use the target role's actual skills. "
            "For a backend role, build a small API with authentication, validation, "
            "persistence, tests, and a short design note. For a frontend role, build an "
            "accessible responsive interface with loading, empty, and error states. For "
            "a data role, show a reproducible analysis with data cleaning, a clear "
            "question, honest charts, and stated limitations. For an ML role, document "
            "the baseline, evaluation, failure cases, and data provenance. The goal is "
            "evidence you can explain, not a collection of links or a copied tutorial. "
            "Do not invent users, results, or metrics for a portfolio project."
        ),
    },
    {
        "id": "interviews",
        "title": "Preparing to explain your work",
        "source": "curated://guidance/interviews",
        "kind": "career-guide",
        "text": (
            "Interview preparation should be role-specific and honest. Practise "
            "explaining a project's problem, constraints, trade-offs, tests, and what "
            "you would change. For engineering roles, rehearse fundamentals, debugging, "
            "and reading unfamiliar code. For data roles, rehearse how you validated "
            "data and avoided misleading charts. For security roles, discuss scope, "
            "authorisation, and responsible disclosure. Use behavioural answers with "
            "real situations and outcomes you can defend. A mentor can run a mock "
            "interview, but no platform can promise interview success or a job offer."
        ),
    },
    {
        "id": "mentors",
        "title": "Getting useful help from a mentor",
        "source": "curated://guidance/mentors",
        "kind": "career-guide",
        "text": (
            "Mentor matches are ranked by a deterministic heuristic: overlap with your "
            "outstanding skills, shared college, experience, availability, and capacity. "
            "The score is an ordering aid, not a probability of a good relationship. "
            "Send a short request that names the skill or decision you need help with, "
            "what you have already tried, and what kind of feedback would help. Respect "
            "the mentor's availability. Accepted mentorship is a conversation, not a "
            "guarantee of referrals, interviews, or employment."
        ),
    },
    {
        "id": "privacy",
        "title": "What the advisor sends to an LLM",
        "source": "curated://guidance/privacy",
        "kind": "platform-guide",
        "text": (
            "Retrieval and the deterministic fallback run locally in the CareerGraph "
            "backend. When an administrator configures an OpenRouter API key, a question "
            "can be sent to that provider together with the target occupation, canonical "
            "skill names and levels, the readiness summary, missing skill names, roadmap "
            "step names, and retrieved curated excerpts. Resume files, resume text, "
            "email addresses, account identifiers, and authentication tokens are never "
            "included. The provider's response is validated for citations and rejected "
            "if it invents a link or malformed source. Without a key, no external LLM "
            "call is made."
        ),
    },
    {
        "id": "resume",
        "title": "Resume extraction boundaries",
        "source": "curated://guidance/resume",
        "kind": "platform-guide",
        "text": (
            "Resume extraction is deterministic regex and taxonomy matching, not an AI "
            "or NLP model. The backend extracts text from an uploaded PDF, DOCX, or TXT "
            "file, matches known skill names and aliases, and returns evidence snippets. "
            "You review the result before anything is saved. Existing profile skills are "
            "carried into the review so a confirmation cannot erase them unnoticed. "
            "Files are processed locally by the app; no external AI provider receives a "
            "resume file."
        ),
    },
    {
        "id": "github",
        "title": "GitHub evidence boundaries",
        "source": "curated://guidance/github",
        "kind": "platform-guide",
        "text": (
            "GitHub verification uses the public unauthenticated GitHub REST API. It "
            "checks that the account exists, reads public profile and repository "
            "metadata, excludes forks, and maps primary languages and topics to the "
            "curated taxonomy. It does not read repository code, private repositories, "
            "or contribution quality. Detected skills are suggestions with the "
            "repositories and stars that support them; you choose what to add. Rate "
            "limits and upstream failures are reported honestly instead of being hidden."
        ),
    },
)


def _slug(value: str) -> str:
    """Stable, readable identifier for a curated source."""
    text = value.strip().lower()
    text = text.replace("c++", "c-plus-plus").replace("c#", "c-sharp")
    text = text.replace(".net", "dotnet")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def _document(
    document_id: str,
    title: str,
    source: str,
    kind: str,
    source_label: str,
    text: str,
) -> Dict[str, str]:
    return {
        "id": document_id,
        "title": title,
        "source": source,
        "kind": kind,
        "source_label": source_label,
        "text": text,
    }


def _occupation_documents() -> Iterable[Dict[str, str]]:
    edges = get_prerequisite_edges()
    edges_by_dependent: Dict[str, List[Dict[str, str]]] = {}
    for edge in edges:
        edges_by_dependent.setdefault(edge["dependent"], []).append(edge)

    for summary in list_occupations():
        occupation = get_occupation(summary["key"])
        if not occupation:
            continue
        required = occupation.get("required_skills", [])
        optional = occupation.get("optional_skills", [])
        required_text = ", ".join(
            f"{item['name']} (importance {item['weight']}/5)" for item in required
        )
        optional_text = ", ".join(
            f"{item['name']} (bonus importance {item['weight']}/5)" for item in optional
        ) or "none listed"
        prerequisite_lines: List[str] = []
        for item in required:
            for edge in edges_by_dependent.get(item["name"], []):
                prerequisite_lines.append(
                    f"{edge['prerequisite']} -> {edge['dependent']}: {edge['rationale']}"
                )
        prerequisites_text = "; ".join(prerequisite_lines) or "no curated prerequisite edges for these skills"
        text = (
            f"{occupation['name']} is in the {occupation['category']} category. "
            f"{occupation['description']} This is a curated CareerGraph occupation "
            f"profile, not an official ESCO or O*NET record. Required skills: "
            f"{required_text}. Optional or bonus skills: {optional_text}. Curated "
            f"prerequisite relationships: {prerequisites_text}."
        )
        yield _document(
            f"occupation:{summary['key']}",
            f"Target role: {occupation['name']}",
            f"curated://occupations/{summary['key']}",
            "occupation",
            f"Curated occupation catalog - {occupation['name']}",
            text,
        )


def _skill_documents() -> Iterable[Dict[str, str]]:
    edges = get_prerequisite_edges()
    prerequisites: Dict[str, List[Dict[str, str]]] = {}
    dependents: Dict[str, List[Dict[str, str]]] = {}
    for edge in edges:
        prerequisites.setdefault(edge["dependent"], []).append(edge)
        dependents.setdefault(edge["prerequisite"], []).append(edge)

    assessment_skills: Dict[str, List[str]] = {}
    for data in ASSESSMENTS.values():
        for skill in data.get("skills", []):
            assessment_skills.setdefault(skill, []).append(data["name"])

    for skill in all_canonical_skills():
        category = get_skill_category(skill) or "Uncategorised"
        pre = "; ".join(
            f"{edge['prerequisite']}: {edge['rationale']}"
            for edge in sorted(prerequisites.get(skill, []), key=lambda e: e["prerequisite"])
        ) or "none listed"
        deps = "; ".join(
            f"{edge['dependent']}: {edge['rationale']}"
            for edge in sorted(dependents.get(skill, []), key=lambda e: e["dependent"])
        ) or "none listed"
        assessments = ", ".join(sorted(assessment_skills.get(skill, []))) or "no curated assessment yet"
        text = (
            f"{skill} belongs to the {category} category in the CareerGraph taxonomy. "
            f"It is a canonical skill identifier used by the occupation catalog and "
            f"roadmap planner. Curated prerequisites: {pre}. Skills that depend on it: "
            f"{deps}. Curated assessment evidence available: {assessments}. A skill "
            f"name alone is not a claim of proficiency; the profile's evidence source "
            f"and your confirmation matter."
        )
        yield _document(
            f"skill:{_slug(skill)}",
            f"Skill: {skill}",
            f"curated://skills/{_slug(skill)}",
            "skill",
            f"Curated skill taxonomy - {skill}",
            text,
        )


def _assessment_documents() -> Iterable[Dict[str, str]]:
    for key, data in ASSESSMENTS.items():
        skills = ", ".join(data.get("skills", []))
        text = (
            f"{data['name']} is a small, curated CareerGraph assessment covering "
            f"{skills}. It contains {len(data.get('questions', []))} multiple-choice "
            f"questions and grades exact answer indices; there is no NLP or semantic "
            f"grading. A pass threshold is a fixed percentage, and each evidenced skill "
            f"needs multiple correct answers. A pass can suggest a skill for your "
            f"profile only after you confirm it. This is not an official certification "
            f"and does not claim psychometric validation."
        )
        yield _document(
            f"assessment:{key}",
            f"Assessment: {data['name']}",
            f"curated://assessments/{key}",
            "assessment",
            f"Curated assessment bank - {data['name']}",
            text,
        )


def _guidance_documents() -> Iterable[Dict[str, str]]:
    for guidance in _GUIDANCE:
        yield _document(
            f"guidance:{guidance['id']}",
            guidance["title"],
            guidance["source"],
            guidance["kind"],
            f"CareerGraph curated guidance - {guidance['title']}",
            guidance["text"],
        )


def normalize_text(text: str) -> str:
    """Collapse whitespace so chunking and citations are stable across platforms."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def chunk_text(
    text: str,
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """
    Splits normalized text into deterministic, word-safe chunks.

    The overlap preserves a little context at chunk boundaries. A single word
    longer than ``max_chars`` is kept whole rather than silently dropped.
    """
    normalized = normalize_text(text)
    if not normalized:
        return []
    max_chars = max(1, int(max_chars))
    overlap = max(0, min(int(overlap), max_chars - 1))

    chunks: List[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            split = normalized.rfind(" ", start, end)
            if split > start:
                end = split
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(normalized):
            break
        next_start = max(start + 1, end - overlap)
        # Starting in the middle of a word would make the next chunk harder to
        # cite and read. Move forward to the next word boundary.
        if next_start > 0 and next_start < len(normalized) and not normalized[next_start - 1].isspace():
            boundary = normalized.find(" ", next_start)
            if boundary == -1:
                break
            next_start = boundary + 1
        while next_start < len(normalized) and normalized[next_start].isspace():
            next_start += 1
        start = next_start
    return chunks


def build_knowledge_documents() -> List[Dict[str, str]]:
    """Builds all curated documents in a deterministic order."""
    documents: List[Dict[str, str]] = []
    documents.extend(_guidance_documents())
    documents.extend(_occupation_documents())
    documents.extend(_skill_documents())
    documents.extend(_assessment_documents())
    documents.sort(key=lambda doc: doc["id"])
    return documents


def build_knowledge_chunks(
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[KnowledgeChunk]:
    """Chunks every curated document and assigns stable citation IDs."""
    chunks: List[KnowledgeChunk] = []
    for document in build_knowledge_documents():
        for index, text in enumerate(chunk_text(document["text"], max_chars, overlap)):
            chunks.append(
                KnowledgeChunk(
                    id=f"{document['id']}::{index}",
                    document_id=document["id"],
                    title=document["title"],
                    source=document["source"],
                    source_label=document["source_label"],
                    kind=document["kind"],
                    chunk_index=index,
                    text=text,
                )
            )
    return chunks


@lru_cache(maxsize=1)
def get_knowledge_chunks() -> Tuple[KnowledgeChunk, ...]:
    """Process-wide cached corpus. The data is static and safe to share."""
    return tuple(build_knowledge_chunks())


def get_knowledge_stats() -> Dict[str, Any]:
    """Small, non-sensitive summary for the advisor status endpoint."""
    chunks = get_knowledge_chunks()
    return {
        "document_count": len({chunk.document_id for chunk in chunks}),
        "chunk_count": len(chunks),
        "source": KNOWLEDGE_SOURCE,
        "retrieval": "lexical_bm25",
    }


def validate_knowledge_base() -> List[str]:
    """
    Self-check used by tests. Returns human-readable problems (empty = valid).

    External links are intentionally forbidden: the corpus must not pretend to
    recommend a course or URL that the project has not verified.
    """
    problems: List[str] = []
    documents = build_knowledge_documents()
    if not documents:
        return ["knowledge base is empty"]

    seen_document_ids = set()
    seen_chunk_ids = set()
    for document in documents:
        doc_id = document.get("id")
        if not doc_id:
            problems.append("a document has no id")
        elif doc_id in seen_document_ids:
            problems.append(f"duplicate document id: {doc_id}")
        else:
            seen_document_ids.add(doc_id)

        for field in ("title", "source", "source_label", "kind", "text"):
            if not str(document.get(field) or "").strip():
                problems.append(f"{doc_id}: missing {field}")
        haystack = " ".join(str(document.get(field) or "") for field in ("title", "text", "source_label"))
        if re.search(r"https?://|www\.", haystack, flags=re.IGNORECASE):
            problems.append(f"{doc_id}: external URL is not allowed in the curated corpus")

    for chunk in build_knowledge_chunks():
        if not chunk.text.strip():
            problems.append(f"{chunk.id}: empty chunk")
        if chunk.id in seen_chunk_ids:
            problems.append(f"duplicate chunk id: {chunk.id}")
        seen_chunk_ids.add(chunk.id)
        if chunk.document_id not in seen_document_ids:
            problems.append(f"{chunk.id}: parent document is missing")

    return problems


def find_document(document_id: Optional[str]) -> Optional[Dict[str, str]]:
    """Test/debug helper: return a document by its stable ID."""
    if not document_id:
        return None
    return next((doc for doc in build_knowledge_documents() if doc["id"] == document_id), None)
