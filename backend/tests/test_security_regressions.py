"""
Security regression tests (Phase 1–2 hardening).

Covers:
  * missing / malformed / expired tokens return 401 (never 500)
  * a valid signature with a non-numeric ``sub`` claim is rejected as 401
  * deactivated accounts are rejected
  * the require_role dependency enforces role membership
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.utils.security import create_access_token, require_role


def test_protected_route_without_token(client):
    assert client.get("/auth/me").status_code == 401


def test_protected_route_with_garbage_token(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_valid_token_allows_access(client, make_user):
    headers, payload = make_user()
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == payload["email"]


def test_non_numeric_subject_is_rejected_as_401(client):
    """A correctly signed token whose 'sub' is not an int must not 500."""
    token = create_access_token({"sub": "not-a-number", "email": "x@example.com", "role": "student"})
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_missing_subject_is_rejected_as_401(client):
    token = create_access_token({"email": "x@example.com", "role": "student"})
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_expired_token_is_rejected_as_401(client, make_user):
    headers, payload = make_user()
    expired = create_access_token(
        {"sub": str(payload["user_id"]), "email": payload["email"], "role": "student"},
        expires_delta=timedelta(seconds=-30),
    )
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401


def test_deactivated_account_is_rejected(client, make_user, db_session):
    headers, payload = make_user(email="deactivated@example.com")
    user = db_session.query(User).filter(User.id == payload["user_id"]).first()
    user.is_active = False
    db_session.commit()

    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 401


def test_require_role_allows_and_denies():
    student = User(id=1, email="s@example.com", full_name="S", hashed_password="x", role=UserRole.STUDENT)

    # Allowed: student is in the permitted set.
    checker = require_role("student", "admin")
    assert checker(current_user=student) is student

    # Denied: student is not an admin.
    admin_only = require_role("admin")
    with pytest.raises(HTTPException) as exc:
        admin_only(current_user=student)
    assert exc.value.status_code == 403
