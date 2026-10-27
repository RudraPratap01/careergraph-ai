"""
Phase 7 tests - grounded career intelligence.

These tests use deterministic fixtures and a fake LLM. They prove the local
retrieval, source attribution, fallback, privacy, and validation behavior; they
do **not** claim a live OpenRouter call (no API key is present in the test
environment).
"""

import json
from types import SimpleNamespace

import httpx
import pytest

from app.data.career_knowledge import (
    build_knowledge_chunks,
    chunk_text,
    get_knowledge_chunks,
    get_knowledge_stats,
    validate_knowledge_base,
)
from app.main import app
from app.models.user import User
from app.routes.intelligence import get_llm_client_dependency
from app.services.career_intelligence_service import (
    BM25Retriever,
    LLMError,
    OpenRouterClient,
    answer_career_question,
    expand_query_terms,
    validate_llm_answer,
)
from app.services.skill_gap_service import analyze_skill_gap


class FakeLLM:
    """Test double with the same tiny surface the service needs."""

    model = "test/fake-model"

    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        if self.error:
            raise self.error
        return self.answer


@pytest.fixture
def use_llm():
    """Overrides the FastAPI dependency and always restores it."""

    def _use(fake):
        app.dependency_overrides[get_llm_client_dependency] = lambda: fake
        return fake

    yield _use
    app.dependency_overrides.pop(get_llm_client_dependency, None)


def make_student_profile(
    client,
    make_user,
    email="phase7@example.com",
    full_name="Phase Seven Student",
    target_role="Backend Developer",
    skills=None,
):
    headers, payload = make_user(email=email, full_name=full_name)
    response = client.put(
        "/profile/student",
        headers=headers,
        json={
            "target_role": target_role,
            "target_timeline_months": 6,
            "skills": skills
            if skills is not None
            else [
                {"name": "Python", "level": "advanced"},
                {"name": "SQL", "level": "intermediate"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    return headers, payload


# ─── Corpus and retrieval ────────────────────────────────────────────────────
def test_curated_knowledge_base_is_valid_and_has_no_external_links():
    problems = validate_knowledge_base()
    assert problems == []
    stats = get_knowledge_stats()
    assert stats["document_count"] >= 80
    assert stats["chunk_count"] >= stats["document_count"]
    assert stats["retrieval"] == "lexical_bm25"


def test_chunking_is_deterministic_word_safe_and_bounded():
    text = " ".join(f"word{i}" for i in range(400))
    first = chunk_text(text, max_chars=120, overlap=20)
    second = chunk_text(text, max_chars=120, overlap=20)
    assert first == second
    assert first
    assert all(0 < len(chunk) <= 120 for chunk in first)
    assert all(not chunk.startswith("ord") for chunk in first)


def test_query_expansion_uses_curated_aliases_not_semantic_search():
    terms = expand_query_terms("I know js, postgres and k8s")
    assert "javascript" in terms
    assert "postgresql" in terms
    assert "kubernetes" in terms


def test_bm25_retrieves_relevant_guidance_and_is_deterministic():
    retriever = BM25Retriever(get_knowledge_chunks())
    first = retriever.search("How does the readiness metric work?", top_k=3)
    second = retriever.search("How does the readiness metric work?", top_k=3)
    assert [h.chunk.id for h in first.hits] == [h.chunk.id for h in second.hits]
    assert first.hits[0].chunk.title == "How the readiness metric works"
    assert [h.score for h in first.hits] == [h.score for h in second.hits]


def test_bm25_handles_an_empty_corpus_and_empty_query():
    empty = BM25Retriever([])
    assert empty.search("anything").hits == []
    retriever = BM25Retriever(get_knowledge_chunks())
    assert retriever.search("   ").hits == []


def test_retrieval_surfaces_roadmap_and_skill_sources():
    retriever = BM25Retriever(get_knowledge_chunks())
    result = retriever.search("prerequisite order for Docker and Kubernetes", top_k=8)
    titles = [hit.chunk.title for hit in result.hits]
    assert any("roadmap" in title.lower() or "Docker" in title for title in titles)
    assert any("Docker" in hit.chunk.title or "Kubernetes" in hit.chunk.title for hit in result.hits)


# ─── Validation and provider boundary ───────────────────────────────────────
def test_llm_answer_validation_requires_safe_known_citations():
    assert validate_llm_answer("A grounded answer with a source [S1].", ["S1"]) == (
        "A grounded answer with a source [S1]."
    )
    with pytest.raises(Exception):
        validate_llm_answer("No citation at all", ["S1"])
    with pytest.raises(Exception):
        validate_llm_answer("A made-up citation [S9].", ["S1"])
    with pytest.raises(Exception):
        validate_llm_answer("A link https://example.invalid/course [S1].", ["S1"])
    with pytest.raises(Exception):
        validate_llm_answer("Short [S1].", ["S1"])


def test_openrouter_client_sends_backend_key_and_parses_content():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        seen["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Grounded [S1]."}}]},
        )

    client = OpenRouterClient(
        api_key="test-key-not-real",
        model="test/model",
        base_url="https://openrouter.invalid/api/v1",
        transport=httpx.MockTransport(handler),
    )
    assert client.generate("system", "user") == "Grounded [S1]."
    assert seen["auth"] == "Bearer test-key-not-real"
    assert seen["payload"]["model"] == "test/model"
    assert seen["payload"]["messages"][0]["role"] == "system"


@pytest.mark.parametrize(
    "status_code,error_code",
    [(401, "authentication_failed"), (429, "rate_limited"), (503, "provider_error")],
)
def test_openrouter_client_maps_provider_failures(status_code, error_code):
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code, json={}))
    client = OpenRouterClient(
        api_key="test-key-not-real",
        model="test/model",
        transport=transport,
    )
    with pytest.raises(LLMError) as exc:
        client.generate("system", "user")
    assert exc.value.code == error_code


def test_openrouter_client_rejects_missing_key_and_malformed_payload():
    with pytest.raises(LLMError) as exc:
        OpenRouterClient(api_key="", model="test/model").generate("s", "u")
    assert exc.value.code == "missing_api_key"

    malformed = httpx.MockTransport(lambda request: httpx.Response(200, content=b"not json"))
    client = OpenRouterClient(api_key="test-key-not-real", model="test/model", transport=malformed)
    with pytest.raises(LLMError) as exc:
        client.generate("s", "u")
    assert exc.value.code == "malformed_response"


# ─── API behavior ───────────────────────────────────────────────────────────
def test_advisor_requires_authentication(client):
    assert client.get("/intelligence/status").status_code == 401
    assert client.post("/intelligence/ask", json={"question": "What next?"}).status_code == 401


def test_advisor_rejects_alumni_accounts(client, make_user):
    headers, _ = make_user(email="phase7-alumni@example.com", role="alumni")
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What should I learn next?"},
    )
    assert response.status_code == 403


def test_status_describes_mode_without_exposing_a_key(client, make_user):
    headers, _ = make_user(email="phase7-status@example.com")
    response = client.get("/intelligence/status", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["retrieval"] == "lexical_bm25"
    assert body["knowledge"]["document_count"] >= 80
    assert "api_key" not in json.dumps(body).lower()
    assert "test-key" not in json.dumps(body)


def test_offline_advisor_returns_grounded_answer_and_sources(client, make_user):
    headers, _ = make_student_profile(client, make_user)
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What should I learn first for this backend role?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "grounded_extractive"
    assert body["llm_configured"] is False
    assert body["llm_used"] is False
    assert body["provider"] == "local"
    assert body["context"]["occupation_key"] == "backend-developer"
    assert body["context"]["readiness_score"] == 25
    assert body["context"]["readiness_band"] == "Emerging"
    assert body["sources"]
    assert all(source["id"].startswith("S") for source in body["sources"])
    assert "25%" in body["answer"]
    assert "not a probability" in body["disclaimer"].lower()
    assert body["privacy_note"]
    assert body["limitations"]


def test_explicit_occupation_is_resolved_and_unknown_is_404(client, make_user):
    headers, _ = make_student_profile(
        client,
        make_user,
        target_role="Frontend Developer",
        skills=[{"name": "JavaScript", "level": "intermediate"}],
    )
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What should I learn?", "occupation": "ml-engineer"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["context"]["occupation_key"] == "ml-engineer"

    missing = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What should I learn?", "occupation": "astronaut"},
    )
    assert missing.status_code == 404


def test_question_validation_rejects_short_and_oversized_text(client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-validation@example.com")
    short = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "  x  "},
    )
    assert short.status_code == 422
    long = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "x" * 501},
    )
    assert long.status_code == 422


def test_llm_mode_uses_validated_citation_and_never_sends_identity(use_llm, client, make_user):
    headers, _ = make_student_profile(
        client,
        make_user,
        email="private-person@example.com",
        full_name="Private Person",
    )
    fake = use_llm(
        FakeLLM(
            answer=(
                "Start with the highest-importance missing skill and follow the prerequisite-aware "
                "roadmap order [S1]. Confirm the skill before relying on it [S1]."
            )
        )
    )
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "How should I prioritise my next steps?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "llm"
    assert body["llm_configured"] is True
    assert body["llm_used"] is True
    assert body["provider"] == "openrouter"
    assert body["model"] == "test/fake-model"
    assert body["answer"].startswith("Start with")
    assert fake.calls
    prompt = fake.calls[0][0] + fake.calls[0][1]
    assert "private-person@example.com" not in prompt
    assert "Private Person" not in prompt
    assert "Python" in prompt
    assert "STUDENT QUESTION" in prompt


def test_llm_output_with_invented_link_falls_back(use_llm, client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-link@example.com")
    use_llm(FakeLLM(answer="Take this course: https://example.invalid/course [S1]."))
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What course should I take?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "grounded_extractive"
    assert body["llm_used"] is False
    assert "could not be safely cited" in body["notice"]


def test_llm_output_without_citation_falls_back(use_llm, client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-citation@example.com")
    use_llm(FakeLLM(answer="Just study harder and everything will work out."))
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "How should I study?"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["mode"] == "grounded_extractive"
    assert response.json()["llm_used"] is False


def test_llm_provider_failure_falls_back_without_faking_success(use_llm, client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-failure@example.com")
    use_llm(FakeLLM(error=LLMError("timeout")))
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What should I learn next?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "grounded_extractive"
    assert body["llm_used"] is False
    assert "unavailable" in body["notice"]


def test_no_relevant_source_prevents_llm_call_and_invents_nothing(use_llm, client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-unsupported@example.com")
    fake = use_llm(FakeLLM(answer="This should never be used [S1]."))
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "Who won the 1998 football World Cup?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert fake.calls == []
    assert body["mode"] == "grounded_extractive"
    assert body["llm_used"] is False
    assert body["sources"] == []
    assert "do not have enough relevant" in body["answer"].lower()


def test_empty_knowledge_corpus_returns_a_limitation_not_a_fabrication(
    client, make_user, db_session
):
    headers, payload = make_student_profile(
        client, make_user, email="phase7-empty-corpus@example.com"
    )
    user = db_session.query(User).filter(User.id == payload["user_id"]).one()
    fake = FakeLLM(answer="This should not be called [S1].")
    result = answer_career_question(
        db_session,
        user,
        "What should I learn next?",
        llm_client=fake,
        chunks=[],
    )
    assert result.mode == "grounded_extractive"
    assert result.sources == []
    assert result.llm_configured is True
    assert result.llm_used is False
    assert fake.calls == []
    assert "do not have enough relevant" in result.answer.lower()


def test_readiness_context_matches_the_deterministic_gap_service(client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-score@example.com")
    response = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "How do I close my biggest gap?"},
    )
    assert response.status_code == 200, response.text
    context = response.json()["context"]
    expected = analyze_skill_gap(
        [
            {"name": "Python", "level": "advanced"},
            {"name": "SQL", "level": "intermediate"},
        ],
        "backend-developer",
    )
    assert context["readiness_score"] == expected.readiness_score
    assert context["required_count"] == expected.required_count
    assert context["missing_skills"] == [skill.name for skill in expected.missing_skills]


def test_advisor_does_not_create_or_modify_a_roadmap(client, make_user):
    headers, _ = make_student_profile(client, make_user, email="phase7-no-write@example.com")
    before = client.get("/roadmap", headers=headers)
    assert before.status_code == 404
    answer = client.post(
        "/intelligence/ask",
        headers=headers,
        json={"question": "What are my next roadway steps?"},
    )
    assert answer.status_code == 200
    after = client.get("/roadmap", headers=headers)
    assert after.status_code == 404
