"""
GitHub verification service — Phase 6: GitHub verification & LinkedIn link.

What is genuinely verified, and what is not
-------------------------------------------

* **The GitHub account itself** is verified: login, name, bio, repository list,
  primary languages and topics are fetched live from GitHub's public REST API
  (``https://api.github.com``) at the moment of the request.
* **The inferred skills are not "verified" in the competence sense.** They are a
  deterministic heuristic over repository metadata: a repository's primary
  language and its topics. Each suggestion carries a confidence score and the
  repositories that evidence it, and it only reaches the student profile after
  the student explicitly confirms it.
* **LinkedIn is not verified at all.** LinkedIn has no public API for reading a
  member's profile, so a LinkedIn URL is stored as a self-declared link and is
  always returned with ``verified=False``.

Scope and limits
----------------

* Public repositories only, owned by the account (``type=owner``). Forks are
  excluded because the code is not necessarily the student's own.
* At most ``MAX_REPOS`` (100) most recently pushed repositories are analysed;
  ``repos_truncated`` reports when that cap was hit.
* Unauthenticated requests are limited by GitHub to 60 requests/hour/IP. When
  the limit is exhausted the API returns 503 with an explicit message instead of
  pretending the verification succeeded.
* No OAuth, no tokens, no private repository contents, no code is downloaded.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data.occupations import get_occupation
from app.data.skills_taxonomy import get_skill_category, normalize_skill_name
from app.models.github_verification import GitHubVerification
from app.models.profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.verification import (
    GitHubAccount,
    GitHubConfirmRequest,
    GitHubConfirmResponse,
    GitHubDisconnectResponse,
    GitHubLanguage,
    GitHubSkillEvidence,
    GitHubVerificationResponse,
    LinkedInLinkRequest,
    LinkedInLinkResponse,
    VerificationStatusResponse,
)

GITHUB_API = "https://api.github.com"
GITHUB_SOURCE = "github"

MAX_REPOS = 100
MAX_REPOS_SHOWN_PER_SKILL = 10
REQUEST_TIMEOUT_SECONDS = 10.0
USER_AGENT = "CareerGraph-AI/0.6"

_LINKEDIN_NOTE = (
    "LinkedIn does not provide a public API for reading a member's profile, "
    "so this link is self-declared and not verified."
)

# GitHub username rules: 1-39 chars, alphanumeric or single hyphens, and it may
# not start or end with a hyphen.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")

LINKEDIN_HOSTS = {"linkedin.com", "www.linkedin.com"}

# ── Curated mappings ─────────────────────────────────────────────────────────
#
# GitHub reports a single "primary language" per repository using linguist's
# naming (e.g. "C++", "C#", "Shell", "Vue"). This table maps only names that
# unambiguously correspond to a canonical skill in our taxonomy. Anything not
# listed (Jupyter Notebook, HCL, Objective-C, Dart, ...) is deliberately skipped
# rather than guessed at.
LANGUAGE_TO_SKILL: Dict[str, str] = {
    "Python": "Python",
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Java": "Java",
    "C++": "C++",
    "C#": "C#",
    "C": "C",
    "Go": "Go",
    "Rust": "Rust",
    "Ruby": "Ruby",
    "PHP": "PHP",
    "Swift": "Swift",
    "Kotlin": "Kotlin",
    "SQL": "SQL",
    "HTML": "HTML",
    "CSS": "CSS",
    # SCSS/Sass/Less are CSS dialects; claiming CSS from them is a fair,
    # explainable family mapping.
    "SCSS": "CSS",
    "Sass": "CSS",
    "Less": "CSS",
    "R": "R",
    "Shell": "Shell / Bash",
    "PowerShell": "Shell / Bash",
    "Dockerfile": "Docker",
    "Vue": "Vue.js",
}

# Repo topics that do not resolve through the taxonomy's own alias index.
TOPIC_EXTRA_MAP: Dict[str, str] = {
    "ci-cd": "CI/CD",
    "ml": "Machine Learning",
    "aspnet": "ASP.NET",
    "shell": "Shell / Bash",
}


# ── Small helpers ────────────────────────────────────────────────────────────

def _require_student(user: User, action: str) -> None:
    if user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{action} is only available for student accounts.",
        )


def _get_or_create_profile(user: User, db: Session) -> StudentProfile:
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.id)
        .first()
    )
    if profile is None:
        profile = StudentProfile(user_id=user.id, skills=[])
        db.add(profile)
        db.flush()
    return profile


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _clean_str(value: Any, limit: int) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:limit]


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


# ── Username / URL handling ──────────────────────────────────────────────────

def normalize_github_username(raw: str) -> str:
    """
    Accepts a bare username, ``@username`` or a pasted profile URL and returns a
    validated login. Raises 400 for anything that cannot be a GitHub login.
    """
    username = (raw or "").strip()
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A GitHub username is required.",
        )

    if "://" in username:
        parsed = urlparse(username)
        if (parsed.netloc or "").lower() not in ("github.com", "www.github.com"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only github.com profile URLs are accepted.",
            )
        parts = [part for part in (parsed.path or "").split("/") if part]
        if not parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That GitHub URL does not contain a username.",
            )
        username = parts[0]

    username = username.lstrip("@").strip()
    if not _USERNAME_RE.match(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "That is not a valid GitHub username. Usernames are 1-39 letters, "
                "digits or single hyphens, and cannot start or end with a hyphen."
            ),
        )
    return username


# ── GitHub transport ─────────────────────────────────────────────────────────

def _github_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    not_found_detail: str = "GitHub resource not found.",
) -> Any:
    """
    Performs one unauthenticated GitHub API call, translating every failure mode
    into an honest HTTP error instead of a fabricated success.
    """
    url = f"{GITHUB_API}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    try:
        response = httpx.get(
            url,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub did not respond in time. Please try again shortly.",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not reach GitHub ({type(exc).__name__}). Please try again shortly.",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_detail,
        )

    if response.status_code in (403, 429):
        remaining = (response.headers.get("x-ratelimit-remaining") or "").strip()
        if response.status_code == 429 or remaining == "0":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "GitHub's public API rate limit has been reached (60 requests "
                    "per hour per IP for unauthenticated calls). Please try again later."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub refused the request (HTTP 403).",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub returned an unexpected status (HTTP {response.status_code}).",
        )

    try:
        return response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub returned a response that could not be parsed.",
        )


# ── Skill inference (deterministic) ──────────────────────────────────────────

def topic_to_skill(topic: Any) -> Optional[str]:
    """
    Maps a repository topic (e.g. ``machine-learning``, ``nextjs``) to a
    canonical skill, or ``None`` when the topic has no honest mapping.
    """
    raw = str(topic or "").strip().lower()
    if not raw:
        return None
    candidates = (
        raw,
        raw.replace("-", " "),
        raw.replace("_", " "),
        raw.replace("-", "").replace("_", ""),
    )
    for candidate in candidates:
        resolved = normalize_skill_name(candidate)
        if resolved:
            return resolved
    return TOPIC_EXTRA_MAP.get(raw)


def confidence_for(repo_count: int, stars: int) -> float:
    """
    Deterministic confidence in ``[0.60, 0.95]``.

    More independent repositories using a skill means stronger evidence. Stars
    add a small bonus because they suggest other people found the work useful.
    """
    if repo_count >= 5:
        base = 0.90
    elif repo_count >= 3:
        base = 0.80
    elif repo_count == 2:
        base = 0.70
    else:
        base = 0.60
    if stars >= 5:
        base += 0.05
    return round(min(base, 0.95), 2)


def proficiency_for(repo_count: int, stars: int) -> str:
    if repo_count >= 4 or stars >= 10:
        return "advanced"
    if repo_count >= 2 or stars >= 1:
        return "intermediate"
    return "beginner"


def _build_evidence(
    skill: str,
    repos: List[str],
    stars: int,
    sources: List[str],
) -> str:
    repo_count = len(repos)
    shown = ", ".join(repos[:3])
    if repo_count > 3:
        shown += f" and {repo_count - 3} more"

    if sources == ["language"]:
        where = "primary language"
    elif sources == ["topic"]:
        where = "repository topic"
    else:
        where = "primary language or repository topic"

    plural = "repository" if repo_count == 1 else "repositories"
    star_text = "1 star" if stars == 1 else f"{stars} stars"
    return (
        f"{skill} appears as a {where} in {repo_count} non-forked {plural} "
        f"({shown}); {star_text} across those repositories."
    )


def analyze_repositories(repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Turns a GitHub repository list into evidence-backed skill suggestions.

    Purely deterministic: the same repositories always produce the same output
    (skills sorted by confidence, then repository count, then name; repository
    names sorted alphabetically). Forks are counted as analysed but excluded from
    all evidence, because their code is not necessarily the student's own.
    """
    # skill -> {repo_name: stars}; a repo is counted once per skill even when it
    # matches through both its language and a topic.
    skill_repo_stars: Dict[str, Dict[str, int]] = {}
    skill_sources: Dict[str, set] = {}
    language_counts: Dict[str, int] = {}
    total_stars = 0
    analysed = 0
    forks_excluded = 0

    def record(skill: str, repo_name: str, source: str, stars: int) -> None:
        skill_repo_stars.setdefault(skill, {})[repo_name] = stars
        skill_sources.setdefault(skill, set()).add(source)

    for repo in repositories:
        if not isinstance(repo, dict):
            continue
        analysed += 1
        if repo.get("fork"):
            forks_excluded += 1
            continue

        name = str(repo.get("name") or repo.get("full_name") or f"repo-{analysed}")
        stars = _as_int(repo.get("stargazers_count"))
        total_stars += stars

        language = repo.get("language")
        if isinstance(language, str) and language.strip():
            language = language.strip()
            language_counts[language] = language_counts.get(language, 0) + 1
            mapped = LANGUAGE_TO_SKILL.get(language)
            if mapped:
                record(mapped, name, "language", stars)

        topics = repo.get("topics")
        if isinstance(topics, list):
            for topic in topics[:30]:
                mapped = topic_to_skill(topic)
                if mapped:
                    record(mapped, name, "topic", stars)

    skills: List[GitHubSkillEvidence] = []
    for skill, repo_stars in skill_repo_stars.items():
        repos = sorted(repo_stars.keys())
        stars = sum(repo_stars.values())
        repo_count = len(repos)
        sources = sorted(skill_sources.get(skill, set()))
        skills.append(
            GitHubSkillEvidence(
                name=skill,
                category=get_skill_category(skill) or "Other",
                confidence=confidence_for(repo_count, stars),
                repo_count=repo_count,
                repos=repos[:MAX_REPOS_SHOWN_PER_SKILL],
                stars=stars,
                sources=sources,
                proficiency=proficiency_for(repo_count, stars),
                evidence=_build_evidence(skill, repos, stars, sources),
            )
        )

    skills.sort(key=lambda item: (-item.confidence, -item.repo_count, item.name))

    languages = [
        GitHubLanguage(name=name, count=count)
        for name, count in sorted(
            language_counts.items(), key=lambda pair: (-pair[1], pair[0])
        )
    ]

    return {
        "skills": skills,
        "languages": languages,
        "repos_analyzed": analysed,
        "forks_excluded": forks_excluded,
        "total_stars": total_stars,
    }


# ── Verification ─────────────────────────────────────────────────────────────

def _find_claim(
    db: Session,
    username: str,
    *,
    exclude_user_id: Optional[int] = None,
) -> Optional[GitHubVerification]:
    """Case-insensitive lookup, because GitHub logins are case-insensitive."""
    query = db.query(GitHubVerification).filter(
        func.lower(GitHubVerification.username) == username.lower()
    )
    if exclude_user_id is not None:
        query = query.filter(GitHubVerification.user_id != exclude_user_id)
    return query.first()


def _claim_error(username: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"The GitHub account '{username}' is already linked to another "
            "CareerGraph account. Each GitHub account can evidence one student profile."
        ),
    )


def verify_github_account(
    user: User,
    username: str,
    db: Session,
) -> GitHubVerificationResponse:
    """Fetches the public GitHub account, stores the analysis and returns it."""
    _require_student(user, "GitHub verification")
    login = normalize_github_username(username)

    if _find_claim(db, login, exclude_user_id=user.id) is not None:
        raise _claim_error(login)

    account = _github_get(
        f"/users/{quote(login)}",
        not_found_detail=(
            f"GitHub user '{login}' was not found. Check the username and try again."
        ),
    )
    if not isinstance(account, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub returned an unexpected account payload.",
        )

    # GitHub may canonicalise the casing of the login.
    canonical_login = str(account.get("login") or login)
    if canonical_login.lower() != login.lower():
        if _find_claim(db, canonical_login, exclude_user_id=user.id) is not None:
            raise _claim_error(canonical_login)

    repositories = _github_get(
        f"/users/{quote(canonical_login)}/repos",
        params={"per_page": MAX_REPOS, "sort": "pushed", "type": "owner"},
        not_found_detail=(
            f"GitHub user '{canonical_login}' was not found. Check the username and try again."
        ),
    )
    if not isinstance(repositories, list):
        repositories = []

    analysis = analyze_repositories(repositories)
    truncated = len(repositories) >= MAX_REPOS

    record = (
        db.query(GitHubVerification)
        .filter(GitHubVerification.user_id == user.id)
        .first()
    )
    if record is None:
        record = GitHubVerification(user_id=user.id)
        db.add(record)

    record.username = canonical_login[:100]
    record.name = _clean_str(account.get("name"), 255)
    record.avatar_url = _clean_str(account.get("avatar_url"), 500)
    record.profile_url = _clean_str(account.get("html_url"), 500)
    record.bio = _clean_str(account.get("bio"), 2000)
    record.public_repos = _as_int(account.get("public_repos"))
    record.followers = _as_int(account.get("followers"))
    record.following = _as_int(account.get("following"))
    record.account_created_at = _parse_datetime(account.get("created_at"))
    record.repos_analyzed = analysis["repos_analyzed"]
    record.repos_truncated = truncated
    record.forks_excluded = analysis["forks_excluded"]
    record.total_stars = analysis["total_stars"]
    record.languages = [language.model_dump() for language in analysis["languages"]]
    record.detected_skills = [skill.model_dump() for skill in analysis["skills"]]
    record.fetched_at = datetime.now(timezone.utc)

    # Mirror the login onto the profile so it shows up in the normal profile view
    # and counts towards profile completeness. The verification row remains the
    # source of truth: a full profile PUT that omits github_username clears only
    # this mirror, never the verification.
    profile = _get_or_create_profile(user, db)
    profile.github_username = canonical_login[:100]

    try:
        db.commit()
    except IntegrityError:
        # The pre-checks above cover normal use; this guards a concurrent claim
        # racing on the unique username index.
        db.rollback()
        raise _claim_error(canonical_login)
    db.refresh(record)
    return serialize_verification(record, db, user)


def _target_requirements(user: User, db: Session) -> Tuple[Optional[str], List[str]]:
    """
    Returns the student's target occupation name and its required skills in
    catalog (weight) order, or ``(target_role, [])`` when it cannot be resolved.
    """
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.id)
        .first()
    )
    target_role = profile.target_role if profile else None
    occupation = get_occupation(target_role)
    if not occupation:
        return target_role, []
    required = [
        item["name"]
        for item in occupation.get("required_skills", [])
        if isinstance(item, dict) and item.get("name")
    ]
    return occupation["name"], required


def serialize_verification(
    record: GitHubVerification,
    db: Session,
    user: User,
) -> GitHubVerificationResponse:
    skills = [
        GitHubSkillEvidence(**item)
        for item in (record.detected_skills or [])
        if isinstance(item, dict) and item.get("name")
    ]
    languages = [
        GitHubLanguage(**item)
        for item in (record.languages or [])
        if isinstance(item, dict) and item.get("name")
    ]

    created_at = record.account_created_at
    account_age_days: Optional[int] = None
    if created_at is not None:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        account_age_days = max(0, (datetime.now(timezone.utc) - created_at).days)

    target_role, required = _target_requirements(user, db)
    detected_names = {skill.name for skill in skills}
    relevant = [name for name in required if name in detected_names]

    explanation = (
        f"Fetched {record.repos_analyzed} public repositories from "
        f"github.com/{record.username} (forks excluded) and matched "
        f"{len(skills)} skills from their primary languages and topics."
    )
    if record.repos_truncated:
        explanation += (
            f" Only the {MAX_REPOS} most recently pushed repositories were analysed."
        )

    return GitHubVerificationResponse(
        account=GitHubAccount(
            username=record.username,
            name=record.name,
            avatar_url=record.avatar_url,
            profile_url=record.profile_url,
            bio=record.bio,
            public_repos=record.public_repos,
            followers=record.followers,
            following=record.following,
            account_created_at=record.account_created_at,
            account_age_days=account_age_days,
        ),
        languages=languages,
        skills=skills,
        repos_analyzed=record.repos_analyzed,
        repos_truncated=record.repos_truncated,
        forks_excluded=record.forks_excluded,
        total_stars=record.total_stars,
        target_role=target_role,
        relevant_to_target=relevant,
        explanation=explanation,
        disclaimer=(
            "Account data was fetched live from GitHub's public API. Detected "
            "skills are inferred from repository languages and topics - they say "
            "what you have worked with, not how well - and stay suggestions until "
            "you confirm them."
        ),
        verified_at=record.fetched_at,
        source=GITHUB_SOURCE,
    )


def get_stored_verification(user: User, db: Session) -> GitHubVerificationResponse:
    _require_student(user, "GitHub verification")
    record = (
        db.query(GitHubVerification)
        .filter(GitHubVerification.user_id == user.id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No GitHub account has been verified yet.",
        )
    return serialize_verification(record, db, user)


def get_verification_status(
    user: User,
    db: Session,
) -> VerificationStatusResponse:
    _require_student(user, "Verification status")
    record = (
        db.query(GitHubVerification)
        .filter(GitHubVerification.user_id == user.id)
        .first()
    )
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.id)
        .first()
    )

    linkedin = None
    if profile is not None and (profile.linkedin_url or "").strip():
        linkedin = LinkedInLinkResponse(
            linkedin_url=profile.linkedin_url.strip(),
            verified=False,
            note=_LINKEDIN_NOTE,
        )

    return VerificationStatusResponse(
        github=serialize_verification(record, db, user) if record else None,
        linkedin=linkedin,
    )


# ── Confirming inferred skills ───────────────────────────────────────────────

def confirm_github_skills(
    user: User,
    request: GitHubConfirmRequest,
    db: Session,
) -> GitHubConfirmResponse:
    """
    Adds selected detected skills to the student profile with ``source="github"``.

    Only skills detected by the most recent verification can be confirmed, so a
    client cannot use this endpoint to assert arbitrary skills as evidence.
    Existing assessment evidence is never downgraded; self-reported or
    resume-derived entries are upgraded to evidence while keeping their level.
    """
    _require_student(user, "GitHub skill confirmation")

    record = (
        db.query(GitHubVerification)
        .filter(GitHubVerification.user_id == user.id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verify a GitHub account before confirming skills from it.",
        )

    detected = {
        item["name"]: item
        for item in (record.detected_skills or [])
        if isinstance(item, dict) and item.get("name")
    }

    requested: List[str] = []
    for raw in request.skills:
        name = normalize_skill_name(raw) or str(raw or "").strip()
        if not name:
            continue
        if name not in detected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"'{raw}' was not detected in your verified GitHub repositories. "
                    "Only detected skills can be confirmed from GitHub."
                ),
            )
        if name not in requested:
            requested.append(name)

    if not requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select at least one detected skill to confirm.",
        )

    profile = _get_or_create_profile(user, db)
    existing: Dict[str, Dict[str, Any]] = {}
    for entry in profile.skills or []:
        if isinstance(entry, dict) and entry.get("name"):
            existing[str(entry["name"]).strip().lower()] = dict(entry)

    added: List[str] = []
    upgraded: List[str] = []
    already_present: List[str] = []

    for name in requested:
        key = name.lower()
        current = existing.get(key)
        if current is None:
            existing[key] = {
                "name": name,
                "level": detected[name].get("proficiency", "beginner"),
                "source": GITHUB_SOURCE,
            }
            added.append(name)
        elif current.get("source") == GITHUB_SOURCE:
            already_present.append(name)
        elif current.get("source") == "assessment":
            # A passed assessment is stronger evidence than repository metadata.
            already_present.append(name)
        else:
            current["source"] = GITHUB_SOURCE
            existing[key] = current
            upgraded.append(name)

    profile.skills = list(existing.values())
    db.commit()

    parts = []
    if added:
        parts.append(f"{len(added)} added")
    if upgraded:
        parts.append(f"{len(upgraded)} upgraded to GitHub evidence")
    if already_present:
        parts.append(f"{len(already_present)} already on your profile")
    message = "GitHub skills updated: " + ", ".join(parts) + "." if parts else "No changes were needed."

    return GitHubConfirmResponse(
        added=added,
        upgraded=upgraded,
        already_present=already_present,
        skills=profile.skills,
        message=message,
    )


def disconnect_github(user: User, db: Session) -> GitHubDisconnectResponse:
    """
    Removes the stored verification. Skills previously confirmed from GitHub stay
    on the profile but are downgraded to self-reported, because the evidence that
    justified them is gone.
    """
    _require_student(user, "GitHub disconnection")

    record = (
        db.query(GitHubVerification)
        .filter(GitHubVerification.user_id == user.id)
        .first()
    )
    if record is not None:
        db.delete(record)

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.id)
        .first()
    )
    if profile is not None:
        profile.github_username = None
        skills = []
        for entry in profile.skills or []:
            if isinstance(entry, dict):
                entry = dict(entry)
                if entry.get("source") == GITHUB_SOURCE:
                    entry["source"] = "self"
            skills.append(entry)
        profile.skills = skills

    db.commit()
    return GitHubDisconnectResponse(
        disconnected=True,
        message=(
            "GitHub account unlinked. Skills you confirmed from GitHub remain on "
            "your profile, but are now marked as self-reported."
        ),
    )


# ── LinkedIn (explicitly unverified) ─────────────────────────────────────────

def link_linkedin(
    user: User,
    request: LinkedInLinkRequest,
    db: Session,
) -> LinkedInLinkResponse:
    """
    Stores a LinkedIn profile URL as a self-declared link.

    This is intentionally *not* called verification: LinkedIn exposes no public
    API that would let us read or confirm a member's profile. The response always
    carries ``verified=False`` and a note explaining why.
    """
    _require_student(user, "LinkedIn linking")

    raw = (request.url or "").strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A LinkedIn profile URL is required.",
        )

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The LinkedIn URL must start with https://.",
        )

    host = (parsed.netloc or "").lower().split(":")[0]
    if host not in LINKEDIN_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only linkedin.com profile URLs are accepted.",
        )

    path = (parsed.path or "").rstrip("/")
    if not path.startswith("/in/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That is not a LinkedIn personal profile URL (expected linkedin.com/in/<name>).",
        )
    slug = path[len("/in/"):].strip("/")
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The LinkedIn URL is missing the profile name.",
        )

    # Drop query strings and tracking parameters; keep a canonical form.
    normalized = f"https://www.linkedin.com/in/{slug}"

    profile = _get_or_create_profile(user, db)
    profile.linkedin_url = normalized
    db.commit()

    return LinkedInLinkResponse(
        linkedin_url=normalized,
        verified=False,
        note=_LINKEDIN_NOTE,
    )


def get_linkedin(user: User, db: Session) -> LinkedInLinkResponse:
    _require_student(user, "LinkedIn link")
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.id)
        .first()
    )
    if profile is None or not (profile.linkedin_url or "").strip():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No LinkedIn profile has been added yet.",
        )
    return LinkedInLinkResponse(
        linkedin_url=profile.linkedin_url.strip(),
        verified=False,
        note=_LINKEDIN_NOTE,
    )
