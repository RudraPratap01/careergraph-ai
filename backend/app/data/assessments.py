"""
Assessment bank (curated, internal).

Phase 8: assessments & alumni matching.

This module holds a small, hand-authored bank of multiple-choice questions used
to let a student *demonstrate* a skill rather than only self-report it.

Source
------
``DATA_SOURCE_CURATED`` ("curated") — written by the CareerGraph AI team for this
project. These questions are **not** psychometrically validated, are not drawn
from any official certification body, and carry no official identifiers. They are
a lightweight, deterministic way to evidence a skill; nothing here claims to
certify competence.

Design
------
* An assessment groups questions by theme and declares which canonical skills
  (see ``skills_taxonomy.py``) it can evidence.
* Every question is tagged with exactly one canonical skill so that grading can
  produce a per-skill breakdown.
* Each evidential skill has at least ``MIN_QUESTIONS_PER_SKILL`` questions, so a
  single lucky answer is never enough to evidence a skill.
* Grading is deterministic (see ``app/services/assessment_service.py``). No LLM
  and no randomness are involved.
"""

import copy
from typing import Any, Dict, List, Optional

from app.data import DATA_SOURCE_CURATED
from app.data.skills_taxonomy import is_known_skill, normalize_skill_name

ASSESSMENT_SOURCE = DATA_SOURCE_CURATED

#: Minimum score (percent) required to pass an assessment.
PASS_THRESHOLD = 70

#: Minimum questions a skill needs before a pass can count as evidence.
MIN_QUESTIONS_PER_SKILL = 2


def _q(
    qid: str,
    skill: str,
    difficulty: str,
    prompt: str,
    options: List[str],
    answer_index: int,
    explanation: str,
) -> Dict[str, Any]:
    return {
        "id": qid,
        "skill": skill,
        "difficulty": difficulty,
        "prompt": prompt,
        "options": options,
        "answer_index": answer_index,
        "explanation": explanation,
    }


ASSESSMENTS: Dict[str, Dict[str, Any]] = {
    "python-fundamentals": {
        "name": "Python Fundamentals",
        "description": "Core Python syntax, idioms and common correctness pitfalls.",
        "skills": ["Python"],
        "questions": [
            _q(
                "py-1", "Python", "basic",
                "Which of these builds a new list containing every element of nums multiplied by 2?",
                [
                    "nums.map(lambda n: n * 2)",
                    "[n * 2 for n in nums]",
                    "nums.each { |n| n * 2 }",
                    "map(nums, lambda n: n * 2)",
                ],
                1,
                "A list comprehension, [n * 2 for n in nums], is the Python idiom for this.",
            ),
            _q(
                "py-2", "Python", "intermediate",
                "What is the problem with def f(value, items=[]): ?",
                [
                    "Nothing — items is created fresh on every call",
                    "The default list is created once and shared across calls; use items=None and build a list inside",
                    "It is a syntax error in Python 3",
                    "It makes items a tuple",
                ],
                1,
                "Mutable default arguments are evaluated once at function definition time and shared.",
            ),
        ],
    },
    "databases-and-sql": {
        "name": "Databases & SQL",
        "description": "Querying relational data and PostgreSQL storage basics.",
        "skills": ["SQL", "PostgreSQL"],
        "questions": [
            _q(
                "sql-1", "SQL", "basic",
                "In a SELECT with GROUP BY, which clause filters rows *before* aggregation?",
                ["HAVING", "WHERE", "ORDER BY", "LIMIT"],
                1,
                "WHERE filters rows before grouping; HAVING filters the aggregated groups.",
            ),
            _q(
                "sql-2", "SQL", "intermediate",
                "Given a table t with a nullable column x, what does SELECT COUNT(*) FROM t WHERE x IS NULL return?",
                [
                    "The number of rows where x is NULL",
                    "The number of rows where x is not NULL",
                    "Always 0",
                    "A database error",
                ],
                0,
                "COUNT(*) counts matching rows; COUNT(x) is what ignores NULLs.",
            ),
            _q(
                "pg-1", "PostgreSQL", "intermediate",
                "Which PostgreSQL type stores exact decimal values with arbitrary precision?",
                ["DOUBLE PRECISION", "REAL", "NUMERIC", "FLOAT8"],
                2,
                "NUMERIC (a.k.a. DECIMAL) is exact; the float types are binary approximations.",
            ),
            _q(
                "pg-2", "PostgreSQL", "basic",
                "What is the main effect of adding an index to a PostgreSQL column?",
                [
                    "It guarantees the column is unique",
                    "It speeds up lookups at the cost of extra storage and slower writes",
                    "It compresses the whole table",
                    "It enforces a foreign key",
                ],
                1,
                "Indexes trade write cost and storage for faster reads. Uniqueness needs a constraint.",
            ),
        ],
    },
    "web-fundamentals": {
        "name": "Web Fundamentals",
        "description": "Semantic HTML and CSS layout basics.",
        "skills": ["HTML", "CSS"],
        "questions": [
            _q(
                "html-1", "HTML", "basic",
                "Which element is the correct semantic choice for a page's main set of navigation links?",
                ["<div>", "<nav>", "<section>", "<aside>"],
                1,
                "<nav> marks a navigation region and is exposed as such to assistive technology.",
            ),
            _q(
                "html-2", "HTML", "basic",
                "How do you correctly associate a visible <label> with a text input for screen readers?",
                [
                    "Add a placeholder to the input",
                    "Add a name attribute to the input",
                    "Give the input an id and point the label's for attribute at it",
                    "Add a title attribute to the input",
                ],
                2,
                "The label's for attribute must match the input's id.",
            ),
            _q(
                "css-1", "CSS", "intermediate",
                "With box-sizing: border-box, what does an element's declared width include?",
                [
                    "Content only",
                    "Content plus padding and border",
                    "Content plus margin",
                    "Margin plus border only",
                ],
                1,
                "border-box makes padding and border part of the declared width, not extra.",
            ),
            _q(
                "css-2", "CSS", "basic",
                "What does display: flex do to an element's direct children by default?",
                [
                    "Stacks them vertically",
                    "Lays them out in a row and makes them flex items",
                    "Absolutely positions them",
                    "Removes them from the document",
                ],
                1,
                "A flex container defaults to flex-direction: row with its children as flex items.",
            ),
        ],
    },
    "javascript-and-typescript": {
        "name": "JavaScript & TypeScript",
        "description": "Core JavaScript semantics and TypeScript's type system.",
        "skills": ["JavaScript", "TypeScript"],
        "questions": [
            _q(
                "js-1", "JavaScript", "intermediate",
                "What does typeof null evaluate to in JavaScript?",
                ['"null"', '"object"', '"undefined"', '"boolean"'],
                1,
                "typeof null is \"object\" — a long-standing quirk kept for backward compatibility.",
            ),
            _q(
                "js-2", "JavaScript", "basic",
                "Which statement about == and === is correct?",
                [
                    "== compares without any type coercion",
                    "=== compares value and type without coercing types",
                    "They behave identically in all cases",
                    "=== only works on numbers",
                ],
                1,
                "=== is the strict comparison: no type coercion is performed.",
            ),
            _q(
                "ts-1", "TypeScript", "basic",
                "What is the main benefit of TypeScript over plain JavaScript?",
                [
                    "It runs faster in the browser",
                    "It adds static type checking at compile time",
                    "It replaces HTML and CSS",
                    "It removes the need for tests",
                ],
                1,
                "TypeScript's value is compile-time type checking, not runtime speed.",
            ),
            _q(
                "ts-2", "TypeScript", "intermediate",
                "In TypeScript, what does the annotation let x: string | null express?",
                [
                    "x may only ever be null",
                    "x may be a string or null, and must be narrowed before string operations",
                    "x is always a string at runtime",
                    "x is optional and may be undefined",
                ],
                1,
                "A union type means either branch is allowed; the compiler forces a null check.",
            ),
        ],
    },
    "react-fundamentals": {
        "name": "React Fundamentals",
        "description": "Component rendering, lists and side effects.",
        "skills": ["React"],
        "questions": [
            _q(
                "react-1", "React", "basic",
                "Why does React ask for a stable key prop when rendering a list?",
                [
                    "It styles each list item",
                    "It lets React identify which items changed, were added or were removed",
                    "It sets the HTML id of each element",
                    "It is required for passing props to children",
                ],
                1,
                "Keys let React match elements between renders; unstable keys cause wrong reuse of state.",
            ),
            _q(
                "react-2", "React", "basic",
                "Which hook runs a side effect after render?",
                ["useState", "useEffect", "useMemo", "useRef"],
                1,
                "useEffect is the hook for synchronising with external systems after render.",
            ),
        ],
    },
    "backend-engineering": {
        "name": "Backend Engineering",
        "description": "HTTP API design, object-oriented design and unit testing.",
        "skills": ["REST APIs", "Object-Oriented Programming", "Unit Testing"],
        "questions": [
            _q(
                "rest-1", "REST APIs", "basic",
                "Which HTTP method is defined as both safe and idempotent for reading a resource?",
                ["POST", "GET", "PATCH", "DELETE"],
                1,
                "GET is safe (no intended side effects) and idempotent; DELETE is idempotent but not safe.",
            ),
            _q(
                "rest-2", "REST APIs", "basic",
                "Which status code best expresses 'the request was understood but the resource does not exist'?",
                ["200", "201", "404", "500"],
                2,
                "404 Not Found. 201 means created and 500 means a server-side failure.",
            ),
            _q(
                "oop-1", "Object-Oriented Programming", "basic",
                "What does encapsulation mean in object-oriented design?",
                [
                    "Hiding an object's internal state behind a controlled interface",
                    "Creating as many subclasses as possible",
                    "Writing everything as global functions",
                    "Avoiding classes entirely",
                ],
                0,
                "Encapsulation keeps invariants inside the object and exposes a narrow public surface.",
            ),
            _q(
                "oop-2", "Object-Oriented Programming", "basic",
                "If Dog inherits from Animal and overrides speak(), what runs when speak() is called on a Dog instance?",
                [
                    "Animal's implementation",
                    "Dog's overriding implementation",
                    "Both, in an undefined order",
                    "A compile-time error",
                ],
                1,
                "Overriding replaces the inherited behaviour for that subclass.",
            ),
            _q(
                "unit-1", "Unit Testing", "basic",
                "Which property makes a good unit test?",
                [
                    "It depends on the network and a live database",
                    "It is fast, isolated and deterministically checks one behaviour",
                    "It always passes",
                    "It exercises the whole system end to end",
                ],
                1,
                "Unit tests isolate one unit and their result must not depend on external systems.",
            ),
            _q(
                "unit-2", "Unit Testing", "intermediate",
                "In a unit test, what does a test double (a mock or stub) replace?",
                [
                    "The test runner",
                    "A dependency that the unit under test relies on",
                    "The assertion library",
                    "The file under test",
                ],
                1,
                "Doubles stand in for collaborators so the unit can be tested in isolation.",
            ),
        ],
    },
    "algorithms-and-data-structures": {
        "name": "Algorithms & Data Structures",
        "description": "Choosing structures and reasoning about complexity.",
        "skills": ["Data Structures & Algorithms"],
        "questions": [
            _q(
                "dsa-1", "Data Structures & Algorithms", "basic",
                "Which structure offers average O(1) lookup by key?",
                ["Sorted array", "Hash table (e.g. dict)", "Singly linked list", "Binary heap"],
                1,
                "A hash table maps keys to buckets for average constant-time lookup.",
            ),
            _q(
                "dsa-2", "Data Structures & Algorithms", "basic",
                "What is the average time complexity of binary search on a sorted array of n elements?",
                ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                1,
                "Each comparison halves the search space, giving logarithmic time.",
            ),
        ],
    },
    "devops-and-tooling": {
        "name": "DevOps & Tooling",
        "description": "Version control, containers and the Linux command line.",
        "skills": ["Git", "Docker", "Linux"],
        "questions": [
            _q(
                "git-1", "Git", "basic",
                "What does git commit do?",
                [
                    "Uploads your changes to a remote like GitHub",
                    "Records the staged changes as a new commit in local history",
                    "Creates a new branch",
                    "Merges two branches together",
                ],
                1,
                "Commit records locally; uploading is done by push.",
            ),
            _q(
                "git-2", "Git", "basic",
                "What is a Git merge conflict?",
                [
                    "Two people edited two different files",
                    "The same part of a file changed on both branches and Git cannot merge it automatically",
                    "A commit message that is too short",
                    "A missing remote branch",
                ],
                1,
                "Conflicts are reported when overlapping edits cannot be resolved automatically.",
            ),
            _q(
                "docker-1", "Docker", "basic",
                "What is a Docker image?",
                [
                    "A running process",
                    "A read-only template used to create containers",
                    "A full virtual machine",
                    "A network driver",
                ],
                1,
                "An image is the immutable template; a container is a running instance of it.",
            ),
            _q(
                "docker-2", "Docker", "intermediate",
                "Which statement about containers versus virtual machines is correct?",
                [
                    "Every container runs its own full guest operating system",
                    "Containers share the host kernel, making them lighter than VMs",
                    "Virtual machines are always lighter than containers",
                    "Containers and virtual machines are the same thing",
                ],
                1,
                "Sharing the host kernel is why containers start fast and use less memory than VMs.",
            ),
            _q(
                "linux-1", "Linux", "basic",
                "Which command lists directory contents including hidden files?",
                ["ls -l", "ls -a", "cd", "pwd"],
                1,
                "-a includes entries starting with a dot; -l only changes the format.",
            ),
            _q(
                "linux-2", "Linux", "basic",
                "In a Linux shell, what does the pipe operator | do?",
                [
                    "Writes output to a file",
                    "Feeds the standard output of one command into the standard input of the next",
                    "Runs both commands in parallel",
                    "Deletes the specified file",
                ],
                1,
                "Pipes connect a producer's stdout to a consumer's stdin.",
            ),
        ],
    },
    "data-analysis-with-python": {
        "name": "Data Analysis with Python",
        "description": "Tabular manipulation with pandas and numeric work with NumPy.",
        "skills": ["Pandas", "NumPy"],
        "questions": [
            _q(
                "pd-1", "Pandas", "basic",
                "What does df.groupby('city')['sales'].sum() return?",
                [
                    "The total of every sale in the DataFrame",
                    "Total sales per city as a Series",
                    "The number of rows per city",
                    "An unmodified copy of df",
                ],
                1,
                "groupby splits the rows by city and sum aggregates each group.",
            ),
            _q(
                "pd-2", "Pandas", "basic",
                "Which call reads a CSV file into a pandas DataFrame?",
                ["pd.read_csv('file.csv')", "pd.open_csv('file.csv')", "DataFrame.load_csv('file.csv')", "pd.csv('file.csv')"],
                0,
                "pd.read_csv is the reader for comma-separated files.",
            ),
            _q(
                "np-1", "NumPy", "basic",
                "What is the main advantage of a NumPy array over a Python list of numbers?",
                [
                    "It can store mixed types in one array",
                    "Vectorised operations that are faster and use less memory",
                    "It sorts itself automatically",
                    "It can hold any Python object as elements",
                ],
                1,
                "Fixed dtypes plus contiguous storage enable fast vectorised operations.",
            ),
            _q(
                "np-2", "NumPy", "basic",
                "What does arr.shape describe for a NumPy array?",
                [
                    "The element data type",
                    "The size of the array along each dimension",
                    "Only the number of rows",
                    "The memory address of the buffer",
                ],
                1,
                "shape is a tuple giving the length of each axis, e.g. (3, 4).",
            ),
        ],
    },
    "statistics-and-visualization": {
        "name": "Statistics & Visualisation",
        "description": "Descriptive statistics and choosing honest charts.",
        "skills": ["Statistics", "Data Visualization"],
        "questions": [
            _q(
                "stat-1", "Statistics", "basic",
                "What does the median of a data set represent?",
                [
                    "The most frequently occurring value",
                    "The middle value once the data is ordered",
                    "The arithmetic average",
                    "The difference between the largest and smallest values",
                ],
                1,
                "The median splits an ordered data set in half and is robust to outliers.",
            ),
            _q(
                "stat-2", "Statistics", "intermediate",
                "In a hypothesis test, a p-value below the chosen significance level (e.g. 0.05) means:",
                [
                    "The null hypothesis is proven true",
                    "The observed result would be unusual if the null hypothesis were true, so we reject it",
                    "The effect size must be large",
                    "The data must be incorrect",
                ],
                1,
                "A small p-value indicates the data is unlikely under the null; it says nothing about effect size.",
            ),
            _q(
                "viz-1", "Data Visualization", "basic",
                "Which chart best shows how a single numeric variable is distributed across its range?",
                ["A histogram", "A pie chart", "A 100% stacked bar chart", "A single bar"],
                0,
                "A histogram bins the values and shows the frequency of each bin.",
            ),
            _q(
                "viz-2", "Data Visualization", "basic",
                "Why is a pie chart usually a poor choice for more than about 5-6 categories?",
                [
                    "Pie charts cannot be coloured",
                    "Small slices become hard to distinguish, so values are hard to compare accurately",
                    "A pie chart can only ever show percentages",
                    "There is nothing wrong with it — it is ideal for many categories",
                ],
                1,
                "People compare angles poorly; a bar chart encodes magnitude by length instead.",
            ),
        ],
    },
}


def list_assessments() -> List[Dict[str, Any]]:
    """Returns lightweight summaries of every assessment (deterministic order)."""
    summaries = []
    for key, data in ASSESSMENTS.items():
        summaries.append({
            "key": key,
            "name": data["name"],
            "description": data["description"],
            "skills": list(data["skills"]),
            "question_count": len(data["questions"]),
            "pass_threshold": PASS_THRESHOLD,
            "source": ASSESSMENT_SOURCE,
        })
    summaries.sort(key=lambda a: a["name"])
    return summaries


def get_assessment(key: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Returns a deep copy of one assessment so callers cannot mutate the shared
    bank. ``key`` is matched case-insensitively against the assessment key.
    """
    if not key:
        return None
    record = ASSESSMENTS.get(str(key).strip().lower())
    if not record:
        return None
    result = copy.deepcopy(record)
    result["key"] = str(key).strip().lower()
    result["pass_threshold"] = PASS_THRESHOLD
    result["source"] = ASSESSMENT_SOURCE
    return result


def all_assessment_keys() -> List[str]:
    return list(ASSESSMENTS.keys())


def skills_covered_by_assessments() -> List[str]:
    """Every canonical skill that at least one assessment can evidence."""
    covered = {skill for data in ASSESSMENTS.values() for skill in data["skills"]}
    return sorted(covered, key=lambda s: s.lower())


def questions_for_skill(skill: str) -> List[Dict[str, Any]]:
    """Every question, across the bank, that is tagged with ``skill``."""
    canonical = normalize_skill_name(skill) or skill
    return [
        q
        for data in ASSESSMENTS.values()
        for q in data["questions"]
        if q["skill"] == canonical
    ]


def validate_assessment_bank() -> List[str]:
    """
    Self-check used by tests. Returns a list of human-readable problems
    (empty means the bank is valid).
    """
    problems: List[str] = []
    seen_ids: Dict[str, str] = {}

    if not ASSESSMENTS:
        problems.append("assessment bank is empty")

    for key, data in ASSESSMENTS.items():
        if not data.get("name"):
            problems.append(f"{key}: missing name")
        if not data.get("description"):
            problems.append(f"{key}: missing description")

        questions = data.get("questions") or []
        if not questions:
            problems.append(f"{key}: no questions")

        declared = set(data.get("skills") or [])
        if not declared:
            problems.append(f"{key}: no declared skills")

        for skill in declared:
            if not is_known_skill(skill):
                problems.append(f"{key}: unknown skill '{skill}'")
            elif normalize_skill_name(skill) != skill:
                problems.append(f"{key}: '{skill}' is not a canonical skill name")

        tagged: Dict[str, int] = {}
        for q in questions:
            qid = q.get("id")
            if not qid:
                problems.append(f"{key}: a question has no id")
            elif qid in seen_ids:
                problems.append(f"{key}: duplicate question id '{qid}' (also in {seen_ids[qid]})")
            else:
                seen_ids[qid] = key

            skill = q.get("skill")
            if not is_known_skill(skill):
                problems.append(f"{key}.{qid}: unknown skill '{skill}'")
            elif normalize_skill_name(skill) != skill:
                problems.append(f"{key}.{qid}: '{skill}' is not a canonical skill name")

            if skill not in declared:
                problems.append(f"{key}.{qid}: skill '{skill}' is not declared by the assessment")

            options = q.get("options") or []
            if len(options) < 2:
                problems.append(f"{key}.{qid}: needs at least 2 options")
            if len(set(options)) != len(options):
                problems.append(f"{key}.{qid}: duplicate options")
            answer = q.get("answer_index")
            if not isinstance(answer, int) or not (0 <= answer < len(options)):
                problems.append(f"{key}.{qid}: answer_index {answer!r} is out of range")
            if not q.get("prompt"):
                problems.append(f"{key}.{qid}: missing prompt")
            if not q.get("explanation"):
                problems.append(f"{key}.{qid}: missing explanation")

            tagged[skill] = tagged.get(skill, 0) + 1

        for skill in declared:
            count = tagged.get(skill, 0)
            if count < MIN_QUESTIONS_PER_SKILL:
                problems.append(
                    f"{key}: skill '{skill}' has only {count} question(s); "
                    f"{MIN_QUESTIONS_PER_SKILL} required to evidence a skill"
                )

    return problems
