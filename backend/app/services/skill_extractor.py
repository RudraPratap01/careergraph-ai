"""
Skill extraction and normalization engine.

Phase 3: Resume Intelligence
Matches canonical skills against extracted resume text, determines confidence,
extracts contextual evidence, and normalizes synonyms into standard nomenclature.
"""

import re
from typing import List, Dict, Any, Optional
from app.schemas.resume import ExtractedSkill

# ─── Canonical Skills Taxonomy ────────────────────────────────────────────────
# Maps canonical skill name -> { category, aliases, case_sensitive }
TAXONOMY: Dict[str, Dict[str, Any]] = {
    # ── Languages ─────────────────────────────────────────────────────────────
    "Python": {
        "category": "Languages",
        "aliases": ["python", "python3", "python 3", "py"],
    },
    "JavaScript": {
        "category": "Languages",
        "aliases": ["javascript", "js", "ecmascript"],
    },
    "TypeScript": {
        "category": "Languages",
        "aliases": ["typescript", "ts"],
    },
    "Java": {
        "category": "Languages",
        "aliases": ["java", "core java", "j2ee"],
        "negative_lookahead": r"(?!script)",  # avoid matching javascript
    },
    "C++": {
        "category": "Languages",
        "aliases": ["c\\+\\+", "cpp"],
    },
    "C#": {
        "category": "Languages",
        "aliases": ["c#", "csharp", "c-sharp"],
    },
    "C": {
        "category": "Languages",
        "aliases": ["c language", "ansi c", "c programming"],
        "case_sensitive_aliases": ["C"],
    },
    "Go": {
        "category": "Languages",
        "aliases": ["golang", "go language"],
    },
    "Rust": {
        "category": "Languages",
        "aliases": ["rust", "rustlang"],
    },
    "Ruby": {
        "category": "Languages",
        "aliases": ["ruby"],
    },
    "PHP": {
        "category": "Languages",
        "aliases": ["php", "php7", "php8"],
    },
    "Swift": {
        "category": "Languages",
        "aliases": ["swift", "swiftui"],
    },
    "Kotlin": {
        "category": "Languages",
        "aliases": ["kotlin"],
    },
    "SQL": {
        "category": "Languages",
        "aliases": ["sql", "structured query language", "transact-sql", "t-sql", "pl/sql"],
    },
    "HTML": {
        "category": "Languages",
        "aliases": ["html", "html5"],
    },
    "CSS": {
        "category": "Languages",
        "aliases": ["css", "css3"],
    },
    "R": {
        "category": "Languages",
        "aliases": ["r language", "r programming"],
    },
    "Shell / Bash": {
        "category": "Languages",
        "aliases": ["bash", "shell scripting", "bash scripting", "powershell", "zsh"],
    },

    # ── Frameworks & Libraries ────────────────────────────────────────────────
    "React": {
        "category": "Frameworks & Libraries",
        "aliases": ["react", "react.js", "reactjs", "react native"],
    },
    "Node.js": {
        "category": "Frameworks & Libraries",
        "aliases": ["node.js", "nodejs", "node js"],
    },
    "FastAPI": {
        "category": "Frameworks & Libraries",
        "aliases": ["fastapi", "fast-api", "fast api"],
    },
    "Django": {
        "category": "Frameworks & Libraries",
        "aliases": ["django", "django rest framework", "drf"],
    },
    "Flask": {
        "category": "Frameworks & Libraries",
        "aliases": ["flask"],
    },
    "Express.js": {
        "category": "Frameworks & Libraries",
        "aliases": ["express", "express.js", "expressjs"],
    },
    "Next.js": {
        "category": "Frameworks & Libraries",
        "aliases": ["next.js", "nextjs", "next js"],
    },
    "Vue.js": {
        "category": "Frameworks & Libraries",
        "aliases": ["vue", "vue.js", "vuejs"],
    },
    "Angular": {
        "category": "Frameworks & Libraries",
        "aliases": ["angular", "angularjs", "angular 2+"],
    },
    "Spring Boot": {
        "category": "Frameworks & Libraries",
        "aliases": ["spring boot", "springboot", "spring framework"],
    },
    "ASP.NET": {
        "category": "Frameworks & Libraries",
        "aliases": ["asp.net", "dotnet", ".net core", "asp.net core"],
    },
    "Tailwind CSS": {
        "category": "Frameworks & Libraries",
        "aliases": ["tailwind", "tailwindcss", "tailwind css"],
    },
    "PyTorch": {
        "category": "Frameworks & Libraries",
        "aliases": ["pytorch", "torch"],
    },
    "TensorFlow": {
        "category": "Frameworks & Libraries",
        "aliases": ["tensorflow", "tf", "keras"],
    },
    "Scikit-learn": {
        "category": "Frameworks & Libraries",
        "aliases": ["scikit-learn", "sklearn", "scikit learn"],
    },
    "Pandas": {
        "category": "Frameworks & Libraries",
        "aliases": ["pandas"],
    },
    "NumPy": {
        "category": "Frameworks & Libraries",
        "aliases": ["numpy"],
    },

    # ── Databases & Storage ───────────────────────────────────────────────────
    "PostgreSQL": {
        "category": "Databases",
        "aliases": ["postgresql", "postgres", "psql"],
    },
    "MySQL": {
        "category": "Databases",
        "aliases": ["mysql"],
    },
    "MongoDB": {
        "category": "Databases",
        "aliases": ["mongodb", "mongo"],
    },
    "Redis": {
        "category": "Databases",
        "aliases": ["redis"],
    },
    "SQLite": {
        "category": "Databases",
        "aliases": ["sqlite", "sqlite3"],
    },
    "Elasticsearch": {
        "category": "Databases",
        "aliases": ["elasticsearch", "elastic search"],
    },
    "Firebase": {
        "category": "Databases",
        "aliases": ["firebase", "firestore"],
    },

    # ── Cloud & DevOps ────────────────────────────────────────────────────────
    "Docker": {
        "category": "Cloud & DevOps",
        "aliases": ["docker", "docker containers", "dockerfile", "docker-compose"],
    },
    "Kubernetes": {
        "category": "Cloud & DevOps",
        "aliases": ["kubernetes", "k8s"],
    },
    "AWS": {
        "category": "Cloud & DevOps",
        "aliases": ["aws", "amazon web services", "ec2", "s3", "lambda", "aws lambda"],
    },
    "Azure": {
        "category": "Cloud & DevOps",
        "aliases": ["azure", "microsoft azure"],
    },
    "Google Cloud (GCP)": {
        "category": "Cloud & DevOps",
        "aliases": ["gcp", "google cloud", "google cloud platform"],
    },
    "Git": {
        "category": "Cloud & DevOps",
        "aliases": ["git", "github", "gitlab", "version control"],
    },
    "Linux": {
        "category": "Cloud & DevOps",
        "aliases": ["linux", "ubuntu", "debian", "redhat", "centos", "unix"],
    },
    "CI/CD": {
        "category": "Cloud & DevOps",
        "aliases": ["ci/cd", "cicd", "continuous integration", "github actions", "jenkins"],
    },
    "Nginx": {
        "category": "Cloud & DevOps",
        "aliases": ["nginx"],
    },

    # ── Concepts & Architecture ───────────────────────────────────────────────
    "REST APIs": {
        "category": "Concepts & Architecture",
        "aliases": ["rest api", "rest apis", "restful", "restful api", "restful apis", "rest architecture"],
    },
    "GraphQL": {
        "category": "Concepts & Architecture",
        "aliases": ["graphql", "graph ql"],
    },
    "Microservices": {
        "category": "Concepts & Architecture",
        "aliases": ["microservices", "microservice architecture", "micro-services"],
    },
    "System Design": {
        "category": "Concepts & Architecture",
        "aliases": ["system design", "distributed systems", "high availability", "scalability"],
    },
    "Data Structures & Algorithms": {
        "category": "Concepts & Architecture",
        "aliases": ["data structures", "algorithms", "dsa", "leetcode"],
    },
    "Object-Oriented Programming": {
        "category": "Concepts & Architecture",
        "aliases": ["oop", "object oriented", "object-oriented programming"],
    },
    "Unit Testing": {
        "category": "Concepts & Architecture",
        "aliases": ["unit testing", "pytest", "jest", "junit", "tdd", "test driven development"],
    },
}

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
            pattern = rf"\b{escaped}\b{negative_lookahead}"
            for item in items:
                if re.search(pattern, item["text"], re.IGNORECASE):
                    matches.append(item)

        # 2. Check case-sensitive aliases (e.g., 'C')
        for cs_alias in case_sensitive_aliases:
            pattern = rf"\b{re.escape(cs_alias)}\b"
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
