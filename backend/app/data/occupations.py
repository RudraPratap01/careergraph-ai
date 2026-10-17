"""
Occupation catalog (curated, internal).

Phase 4: Skill gaps & career readiness.

Each occupation declares the canonical skills (see ``skills_taxonomy.py``) that
the role requires, each with an importance weight. The readiness score is a
deterministic, weighted coverage of those required skills — see
``app/services/skill_gap_service.py`` for the exact formula and rationale.

Source
------
``DATA_SOURCE_CURATED`` ("curated") — hand-authored by the CareerGraph AI team
for this project. These are **not** official ESCO/O*NET occupation records and
carry no official occupation codes.

Weight scale (importance)
-------------------------
    5 — essential / core to the role
    4 — strongly expected
    3 — expected
    2 — helpful
    1 — nice to have

Only ``required_skills`` contribute to the readiness score.
``optional_skills`` are surfaced as "bonus" suggestions and never lower the
score when missing.
"""

from typing import Any, Dict, List, Optional

from app.data import DATA_SOURCE_CURATED
from app.data.skills_taxonomy import is_known_skill, normalize_skill_name

OCCUPATION_SOURCE = DATA_SOURCE_CURATED


def _req(name: str, weight: int) -> Dict[str, Any]:
    return {"name": name, "weight": weight}


def _opt(name: str, weight: int) -> Dict[str, Any]:
    return {"name": name, "weight": weight}


OCCUPATIONS: Dict[str, Dict[str, Any]] = {
    "backend-developer": {
        "name": "Backend Developer",
        "category": "Software Engineering",
        "description": "Builds and maintains server-side services, APIs, and data access layers.",
        "aliases": ["backend", "backend developer", "back end developer", "backend engineer", "server side developer"],
        "required_skills": [
            _req("Python", 5),
            _req("REST APIs", 5),
            _req("SQL", 5),
            _req("PostgreSQL", 4),
            _req("Object-Oriented Programming", 4),
            _req("Unit Testing", 4),
            _req("Git", 4),
            _req("Data Structures & Algorithms", 3),
            _req("Docker", 3),
            _req("Linux", 3),
        ],
        "optional_skills": [
            _opt("FastAPI", 4),
            _opt("Django", 3),
            _opt("Microservices", 4),
            _opt("Redis", 3),
            _opt("System Design", 4),
            _opt("CI/CD", 3),
        ],
    },
    "frontend-developer": {
        "name": "Frontend Developer",
        "category": "Software Engineering",
        "description": "Builds responsive, accessible user interfaces for web applications.",
        "aliases": ["frontend", "frontend developer", "front end developer", "frontend engineer", "ui developer"],
        "required_skills": [
            _req("JavaScript", 5),
            _req("HTML", 5),
            _req("CSS", 5),
            _req("React", 5),
            _req("REST APIs", 3),
            _req("TypeScript", 3),
            _req("Git", 3),
            _req("Data Structures & Algorithms", 2),
        ],
        "optional_skills": [
            _opt("Next.js", 3),
            _opt("Tailwind CSS", 2),
            _opt("Vue.js", 2),
            _opt("Angular", 2),
            _opt("Unit Testing", 3),
            _opt("System Design", 2),
        ],
    },
    "full-stack-developer": {
        "name": "Full Stack Developer",
        "category": "Software Engineering",
        "description": "Works across both client and server layers of a web application.",
        "aliases": ["full stack", "full stack developer", "fullstack developer", "full-stack", "fullstack"],
        "required_skills": [
            _req("JavaScript", 5),
            _req("React", 4),
            _req("Node.js", 4),
            _req("HTML", 4),
            _req("CSS", 4),
            _req("SQL", 4),
            _req("REST APIs", 4),
            _req("TypeScript", 3),
            _req("Git", 3),
        ],
        "optional_skills": [
            _opt("PostgreSQL", 3),
            _opt("MongoDB", 3),
            _opt("Docker", 3),
            _opt("Next.js", 3),
            _opt("Express.js", 3),
            _opt("Unit Testing", 3),
        ],
    },
    "data-analyst": {
        "name": "Data Analyst",
        "category": "Data & AI",
        "description": "Turns raw data into insight using SQL, Python, and visual reporting.",
        "aliases": ["data analyst", "analyst", "business analyst", "data analytics"],
        "required_skills": [
            _req("SQL", 5),
            _req("Pandas", 5),
            _req("Python", 4),
            _req("Data Visualization", 4),
            _req("Statistics", 4),
            _req("NumPy", 3),
            _req("PostgreSQL", 3),
        ],
        "optional_skills": [
            _opt("R", 2),
            _opt("Machine Learning", 2),
            _opt("Git", 2),
            _opt("Data Structures & Algorithms", 2),
        ],
    },
    "ml-engineer": {
        "name": "ML Engineer",
        "category": "Data & AI",
        "description": "Designs, trains, and deploys machine-learning models and pipelines.",
        "aliases": ["ml engineer", "machine learning engineer", "ml", "ai engineer", "machine learning"],
        "required_skills": [
            _req("Python", 5),
            _req("NumPy", 5),
            _req("Scikit-learn", 5),
            _req("Machine Learning", 5),
            _req("Pandas", 4),
            _req("Statistics", 4),
            _req("SQL", 3),
            _req("Git", 3),
            _req("Linux", 3),
        ],
        "optional_skills": [
            _opt("Deep Learning", 4),
            _opt("TensorFlow", 4),
            _opt("PyTorch", 4),
            _opt("Natural Language Processing", 3),
            _opt("Docker", 3),
            _opt("Data Visualization", 2),
        ],
    },
    "cybersecurity-analyst": {
        "name": "Cybersecurity Analyst",
        "category": "Security",
        "description": "Protects systems and data by finding, analysing, and mitigating security weaknesses.",
        "aliases": ["cybersecurity", "cybersecurity analyst", "security analyst", "cyber security", "infosec"],
        "required_skills": [
            _req("Networking", 5),
            _req("Linux", 5),
            _req("Shell / Bash", 4),
            _req("Cryptography", 4),
            _req("Penetration Testing", 4),
            _req("Python", 3),
            _req("Git", 2),
        ],
        "optional_skills": [
            _opt("Nginx", 2),
            _opt("Docker", 2),
            _opt("SQL", 2),
            _opt("AWS", 3),
        ],
    },
    "cloud-devops-engineer": {
        "name": "Cloud / DevOps Engineer",
        "category": "Cloud & DevOps",
        "description": "Automates build, deployment, and infrastructure for reliable systems.",
        "aliases": ["cloud engineer", "devops", "devops engineer", "cloud devops", "sre", "cloud / devops engineer"],
        "required_skills": [
            _req("Linux", 5),
            _req("Docker", 5),
            _req("Kubernetes", 5),
            _req("CI/CD", 5),
            _req("AWS", 4),
            _req("Shell / Bash", 4),
            _req("Git", 4),
        ],
        "optional_skills": [
            _opt("Terraform", 4),
            _opt("Nginx", 3),
            _opt("Python", 3),
            _opt("Azure", 3),
            _opt("Google Cloud (GCP)", 3),
            _opt("Networking", 3),
        ],
    },
}

# ── Surface-form → key index (case-insensitive, collision-guarded) ────────────
def _build_occupation_index() -> Dict[str, str]:
    index: Dict[str, str] = {}
    for key, data in OCCUPATIONS.items():
        index.setdefault(key.strip().lower(), key)
        index.setdefault(data["name"].strip().lower(), key)
        for alias in data.get("aliases", []):
            index.setdefault(alias.strip().lower(), key)
    return index


OCCUPATION_ALIAS_TO_KEY: Dict[str, str] = _build_occupation_index()


def resolve_occupation_key(name: Optional[str]) -> Optional[str]:
    """Resolves a free-text occupation name/alias to a catalog key, or ``None``."""
    if not name:
        return None
    return OCCUPATION_ALIAS_TO_KEY.get(str(name).strip().lower())


def get_occupation(name_or_key: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Returns the full occupation record for a key, name, or alias.

    The returned dict is a shallow copy augmented with its ``key`` so callers
    cannot mutate the shared catalog entry.
    """
    key = resolve_occupation_key(name_or_key)
    if not key:
        return None
    record = dict(OCCUPATIONS[key])
    record["key"] = key
    return record


def list_occupations() -> List[Dict[str, Any]]:
    """Returns lightweight summaries of every occupation (deterministic order)."""
    summaries = []
    for key, data in OCCUPATIONS.items():
        summaries.append({
            "key": key,
            "name": data["name"],
            "category": data["category"],
            "description": data["description"],
            "required_skill_count": len(data.get("required_skills", [])),
            "source": OCCUPATION_SOURCE,
        })
    summaries.sort(key=lambda o: (o["category"], o["name"]))
    return summaries


def validate_catalog() -> List[str]:
    """
    Self-check used by tests: every referenced skill must be a canonical skill
    in the taxonomy, and no occupation may have an empty required list.
    Returns a list of human-readable problems (empty means valid).
    """
    problems: List[str] = []
    for key, data in OCCUPATIONS.items():
        if not data.get("required_skills"):
            problems.append(f"{key}: no required skills")
        for group in ("required_skills", "optional_skills"):
            for entry in data.get(group, []):
                if not is_known_skill(entry["name"]):
                    problems.append(f"{key}.{group}: unknown skill '{entry['name']}'")
                if normalize_skill_name(entry["name"]) != entry["name"]:
                    problems.append(f"{key}.{group}: '{entry['name']}' is not a canonical name")
                w = entry.get("weight")
                if not isinstance(w, int) or not (1 <= w <= 5):
                    problems.append(f"{key}.{group}: bad weight for '{entry['name']}'")
    return problems
