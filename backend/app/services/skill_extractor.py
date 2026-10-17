"""
Skill extraction and normalization engine.

Phase 3: Resume Intelligence
Matches canonical skills against extracted resume text, determines confidence,
extracts contextual evidence, and normalizes synonyms into standard nomenclature.

The canonical taxonomy lives in ``app/data/skills_taxonomy.py`` (curated,
internal data) so Phase 4 (skill gaps) and Phase 5 (dependency graph) share a
single source of truth. ``TAXONOMY`` is re-exported here for backwards
compatibility with existing imports/tests.
"""

import re
from typing import List, Dict, Any
from app.schemas.resume import ExtractedSkill
from app.data.skills_taxonomy import TAXONOMY  # noqa: F401  (re-exported)

# Regex to detect section boundaries
SECTION_HEADER_REGEX = re.compile(
    r"^(?:[A-Z\s]{3,30}|(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))\s*[:\-\u2013\u2014]?$",
    re.MULTILINE,
)

ACTION_VERBS = [
    "built", "developed", "implemented", "designed", "created", "architected",
    "engineered", "integrated", "deployed", "optimized", "maintained", "utilized",
    "proficient in", "experience with", "hands-on with",
]


def extract_sentences_and_sections(text: str) -> List[Dict[str, Any]]:
    """Splits resume text into lines/sentences and tracks section context."""
    lines = text.split("\n")
    current_section = "GENERAL"
    items = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        upper_line = stripped.upper()
        # Detect section switches when the line looks like a header (short and not an inline list)
        if len(stripped) < 45 and not (":" in stripped and len(stripped.split(":", 1)[1].strip()) > 5):
            if re.search(r"\b(?:SKILLS?|TECHNICAL\s+SKILLS?|TECHNOLOGIES|TECH\s+STACK|COMPETENCIES|TOOLS)\b", upper_line):
                current_section = "SKILLS"
            elif re.search(r"\b(?:PROJECTS?|ACADEMIC\s+PROJECTS?|PERSONAL\s+PROJECTS?)\b", upper_line):
                current_section = "PROJECTS"
            elif re.search(r"\b(?:WORK\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT|INTERNSHIPS?|WORK\s+HISTORY)\b", upper_line):
                current_section = "EXPERIENCE"
            elif re.search(r"\b(?:EDUCATION|ACADEMICS?|QUALIFICATIONS?)\b", upper_line):
                current_section = "EDUCATION"

        # Split line into sentences if separated by periods/semicolons
        parts = re.split(r"(?<=[.;•|])\s+", stripped)
        for part in parts:
            part_clean = part.strip(" •|-,;\t")
            if part_clean:
                items.append({
                    "text": part_clean,
                    "section": current_section,
                })

    return items


def find_best_evidence_sentence(occurrences: List[Dict[str, Any]]) -> str:
    """Selects the cleanest, most descriptive evidence sentence for a skill."""
    # Prioritize sentences with action verbs
    for occ in occurrences:
        txt = occ["text"]
        lower_txt = txt.lower()
        if any(v in lower_txt for v in ACTION_VERBS) and len(txt) > 25:
            return txt[:140]

    # Otherwise choose a reasonably descriptive sentence
    for occ in occurrences:
        txt = occ["text"]
        if 20 <= len(txt) <= 140:
            return txt

    # Fallback to first occurrence
    return occurrences[0]["text"][:140]


def extract_skills_from_text(text: str) -> List[ExtractedSkill]:
    """
    Scans clean resume text against canonical skills taxonomy.
    Extracts skills with normalization, confidence score (0.0 - 1.0), and evidence.
    """
    items = extract_sentences_and_sections(text)
    extracted: List[ExtractedSkill] = []

    for canonical_name, config in TAXONOMY.items():
        category = config["category"]
        aliases = config.get("aliases", [])
        case_sensitive_aliases = config.get("case_sensitive_aliases", [])
        negative_lookahead = config.get("negative_lookahead", "")

        matches: List[Dict[str, Any]] = []

        # 1. Check case-insensitive aliases
        for alias in aliases:
            escaped = re.escape(alias)
            start_b = r"\b" if re.match(r"^\w", alias) else r"(?<!\S)"
            end_b = r"\b" if re.search(r"\w$", alias) else r"(?!\w)"
            pattern = rf"{start_b}{escaped}{end_b}{negative_lookahead}"
            for item in items:
                if re.search(pattern, item["text"], re.IGNORECASE):
                    matches.append(item)

        # 2. Check case-sensitive aliases (e.g., 'C')
        for cs_alias in case_sensitive_aliases:
            escaped = re.escape(cs_alias)
            start_b = r"\b" if re.match(r"^\w", cs_alias) else r"(?<!\S)"
            end_b = r"\b" if re.search(r"\w$", cs_alias) else r"(?!\w)"
            pattern = rf"{start_b}{escaped}{end_b}{negative_lookahead}"
            for item in items:
                if re.search(pattern, item["text"]):
                    matches.append(item)


        if not matches:
            continue

        # ── Compute Confidence Score ──────────────────────────────────────────
        has_skills_section = any(m["section"] == "SKILLS" for m in matches)
        has_project_or_exp = any(m["section"] in ["PROJECTS", "EXPERIENCE"] for m in matches)
        has_action_verb = any(
            any(v in m["text"].lower() for v in ACTION_VERBS)
            for m in matches
        )
        occurrence_count = len(matches)

        if has_skills_section and (has_project_or_exp or has_action_verb):
            confidence = 0.96
        elif has_skills_section:
            confidence = 0.90
        elif has_project_or_exp and has_action_verb:
            confidence = 0.88
        elif has_project_or_exp or occurrence_count >= 2:
            confidence = 0.82
        else:
            confidence = 0.74

        # ── Compute Suggested Proficiency ─────────────────────────────────────
        if occurrence_count >= 3 and has_action_verb:
            proficiency = "advanced"
        elif occurrence_count >= 2 or has_skills_section:
            proficiency = "intermediate"
        else:
            proficiency = "beginner"

        # ── Evidence Snippet ──────────────────────────────────────────────────
        evidence = find_best_evidence_sentence(matches)

        extracted.append(
            ExtractedSkill(
                name=canonical_name,
                normalized_name=canonical_name,
                category=category,
                confidence=round(confidence, 2),
                evidence=evidence,
                proficiency=proficiency,
            )
        )

    # Sort skills by confidence descending, then by name
    extracted.sort(key=lambda s: (-s.confidence, s.category, s.name))
    return extracted
