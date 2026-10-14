"""
Verification tests for Swagger HTTP Bearer configuration and /auth/login JSON behavior.

Requirements:
1. /auth/login with the existing JSON body still returns 200.
2. Swagger Authorize accepts the JWT bearer token (OpenAPI security scheme is HTTPBearer).
3. GET /auth/me returns 200 when authorized with Bearer token.
4. GET /auth/me returns 401 without authorization.
"""

from app.main import app


def test_swagger_openapi_security_scheme():
    """Verify Swagger OpenAPI definition has HTTP Bearer security scheme."""
    openapi = app.openapi()
    security_schemes = openapi.get("components", {}).get("securitySchemes", {})
    assert "HTTPBearer" in security_schemes
    scheme_def = security_schemes["HTTPBearer"]
    assert scheme_def["type"] == "http"
    assert scheme_def["scheme"] == "bearer"

    # Verify protected route /auth/me uses HTTPBearer
    me_security = openapi["paths"]["/auth/me"]["get"].get("security")
    assert me_security == [{"HTTPBearer": []}]


def test_auth_login_json_and_auth_me_flow(client):
    """
    Verify:
    1. Register user
    2. /auth/login with JSON body returns 200 and access_token
    3. GET /auth/me returns 401 without authorization
    4. GET /auth/me returns 200 when authorized with Bearer token
    """
    # 1. Register user
    reg_res = client.post(
        "/auth/register",
        json={
            "email": "teststudent01@example.com",
            "full_name": "Test Student",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert reg_res.status_code == 201

    # Requirement 1: /auth/login with existing JSON body returns 200
    login_res = client.post(
        "/auth/login",
        json={
            "email": "teststudent01@example.com",
            "password": "Password123!",
        },
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    access_token = data["access_token"]

    # Requirement 4: GET /auth/me returns 401 without authorization
    unauth_res = client.get("/auth/me")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["detail"] == "Not authenticated"

    # Requirement 3: GET /auth/me returns 200 when authorized
    auth_res = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert auth_res.status_code == 200
    user_data = auth_res.json()
    assert user_data["email"] == "teststudent01@example.com"
    assert user_data["full_name"] == "Test Student"
