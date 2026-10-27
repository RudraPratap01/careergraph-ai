"""
Opt-in PostgreSQL integration checks.

These tests run only when ``POSTGRES_TEST_URL`` points at a disposable test
database that has already had ``alembic upgrade head`` applied. The normal
SQLite-only suite skips them. Nothing is committed: the round-trip test rolls
back its transaction.

CI supplies the URL from a PostgreSQL service container. Local developers can do
the same with Docker Compose, but must never point this at a database containing
data they care about.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.models.profile import StudentProfile
from app.models.user import User, UserRole

POSTGRES_TEST_URL = os.environ.get("POSTGRES_TEST_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason="POSTGRES_TEST_URL is not configured; skipping live PostgreSQL checks",
)


@pytest.fixture(scope="module")
def engine():
    test_engine = create_engine(POSTGRES_TEST_URL, pool_pre_ping=True)
    try:
        with test_engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        yield test_engine
    finally:
        test_engine.dispose()


def test_postgres_migrations_created_the_expected_schema(engine):
    table_names = set(inspect(engine).get_table_names())
    expected = {
        "users",
        "student_profiles",
        "alumni_profiles",
        "resumes",
        "roadmaps",
        "roadmap_step_progress",
        "assessment_attempts",
        "mentorship_requests",
        "github_verifications",
        "alembic_version",
    }
    assert expected.issubset(table_names), sorted(expected - table_names)
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "0004_github_verifications"


def test_postgres_user_and_profile_round_trip(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    email = f"ci-{uuid.uuid4().hex}@example.test"
    try:
        user = User(
            email=email,
            full_name="CI Integration User",
            hashed_password="not-a-real-password-hash",
            role=UserRole.STUDENT,
        )
        session.add(user)
        session.flush()
        session.add(
            StudentProfile(
                user_id=user.id,
                target_role="Backend Developer",
                skills=[{"name": "Python", "level": "advanced"}],
            )
        )
        session.flush()

        loaded = session.query(User).filter(User.email == email).one()
        assert loaded.student_profile is not None
        assert loaded.student_profile.target_role == "Backend Developer"
        assert loaded.student_profile.skills == [{"name": "Python", "level": "advanced"}]
    finally:
        session.rollback()
        session.close()
