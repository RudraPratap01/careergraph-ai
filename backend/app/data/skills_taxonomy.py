"""
Canonical skill taxonomy (curated, internal).

Phase 3: Resume Intelligence — skill matching / normalization source of truth.
Phase 4: Skill gaps & career readiness — required-skill references point here.

Source
------
``DATA_SOURCE_CURATED`` ("curated") — authored by the CareerGraph AI team.
These are not official ESCO/O*NET identifiers and must never be presented as
such. See ``app/data/__init__.py`` for the data-source policy.

Structure
---------
``TAXONOMY`` maps a canonical skill name to a configuration dict:

    category                 human-readable grouping (used by the UI)
    aliases                  case-insensitive surface forms
    case_sensitive_aliases   surface forms that must match exact case (e.g. "C")
    negative_lookahead       regex appended to prevent false sub-matches
"""

from typing import Any, Dict, List, Optional

from app.data import DATA_SOURCE_CURATED

SKILL_SOURCE = DATA_SOURCE_CURATED

# ─── Canonical Skills Taxonomy ────────────────────────────────────────────────
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
        "aliases": ["c++", "cpp"],
    },
    "C#": {
        "category": "Languages",
        "aliases": ["c#", "csharp", "c-sharp"],
    },
    "C": {
        "category": "Languages",
        "aliases": ["c language", "ansi c", "c programming"],
        "case_sensitive_aliases": ["C"],
        "negative_lookahead": r"(?![+#])",
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

    # ── Data & AI ─────────────────────────────────────────────────────────────
    "Machine Learning": {
        "category": "Data & AI",
        "aliases": ["machine learning", "ml models", "supervised learning", "unsupervised learning"],
    },
    "Deep Learning": {
        "category": "Data & AI",
        "aliases": ["deep learning", "neural networks", "neural network", "cnn", "rnn"],
    },
    "Natural Language Processing": {
        "category": "Data & AI",
        "aliases": ["natural language processing", "nlp", "transformers", "text mining"],
    },
    "Data Visualization": {
        "category": "Data & AI",
        "aliases": ["data visualization", "matplotlib", "seaborn", "plotly", "tableau", "power bi"],
    },
    "Statistics": {
        "category": "Data & AI",
        "aliases": ["statistics", "statistical analysis", "probability", "hypothesis testing"],
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
    "Terraform": {
        "category": "Cloud & DevOps",
        "aliases": ["terraform", "infrastructure as code", "iac"],
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

    # ── Security ──────────────────────────────────────────────────────────────
    "Networking": {
        "category": "Security",
        "aliases": ["networking", "tcp/ip", "network security", "dns", "firewalls"],
    },
    "Cryptography": {
        "category": "Security",
        "aliases": ["cryptography", "encryption", "tls", "ssl"],
    },
    "Penetration Testing": {
        "category": "Security",
        "aliases": ["penetration testing", "pen testing", "pentest", "ethical hacking", "burp suite", "metasploit"],
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


def _build_alias_index() -> Dict[str, str]:
    """
    Builds a lookup of lower-cased surface form -> canonical skill name.

    Uses ``setdefault`` so the first canonical entry to claim a surface form
    wins and no alias silently re-points an existing skill.
    ``tests/test_phase4_skill_gap.py::test_alias_index_has_no_collisions``
    asserts the index is collision-free so any accidental overlap is caught.
    """
    index: Dict[str, str] = {}
    for canonical, config in TAXONOMY.items():
        index.setdefault(canonical.strip().lower(), canonical)
        for alias in config.get("aliases", []):
            index.setdefault(alias.strip().lower(), canonical)
        for alias in config.get("case_sensitive_aliases", []):
            index.setdefault(alias.strip().lower(), canonical)
    return index


ALIAS_TO_CANONICAL: Dict[str, str] = _build_alias_index()


def normalize_skill_name(name: Optional[str]) -> Optional[str]:
    """
    Maps a free-text skill name (or alias) to its canonical taxonomy name.

    Returns ``None`` when the name is empty or not present in the taxonomy.
    Lookup is case-insensitive and whitespace-trimmed.
    """
    if not name:
        return None
    return ALIAS_TO_CANONICAL.get(str(name).strip().lower())


def get_skill_category(canonical_name: Optional[str]) -> Optional[str]:
    """Returns the category for a canonical skill name, or ``None``."""
    if not canonical_name:
        return None
    entry = TAXONOMY.get(canonical_name)
    if entry:
        return entry.get("category")
    resolved = normalize_skill_name(canonical_name)
    if resolved:
        return TAXONOMY.get(resolved, {}).get("category")
    return None


def is_known_skill(name: Optional[str]) -> bool:
    """True when the name resolves to a canonical taxonomy skill."""
    return normalize_skill_name(name) is not None


def all_canonical_skills() -> List[str]:
    """Returns every canonical skill name (taxonomy order)."""
    return list(TAXONOMY.keys())
