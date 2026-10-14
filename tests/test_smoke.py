"""Offline tests for the HydraDB CrewAI storage (no crewai/network needed)."""

import responses

from hydradb_crewai import HydraDBClient, HydraDBStorage

BASE = "https://api.hydradb.com"


def _storage():
    client = HydraDBClient(api_key="k", tenant_id="test_beam", sub_tenant_id="")
    return HydraDBStorage(client)


@responses.activate
def test_search_maps_chunks_and_filters_by_score():
    responses.add(
        responses.POST,
        f"{BASE}/query",
        json={
            "success": True,
            "data": {
                "chunks": [
                    {"chunk_content": "keep me", "score": 0.9, "chunk_uuid": "a"},
                    {"chunk_content": "drop me", "score": 0.1, "chunk_uuid": "b"},
                ]
            },
            "error": None,
        },
        status=200,
    )
    results = _storage().search("q", limit=5, score_threshold=0.35)
    assert len(results) == 1
    assert results[0]["content"] == "keep me"
    assert results[0]["context"] == "keep me"
    assert results[0]["metadata"]["id"] == "a"


@responses.activate
def test_save_ingests_as_knowledge():
    responses.add(
        responses.POST,
        f"{BASE}/context/ingest",
        json={"success": True, "data": {"success_count": 1}, "error": None},
        status=200,
    )
    _storage().save("task output", metadata={"agent": "researcher"})
    body = responses.calls[0].request.body
    assert b"app_knowledge" in body
    assert b"memories" not in body
    assert b"test_beam" in body


@responses.activate
def test_save_sanitizes_reserved_and_nested_metadata():
    """A CrewAI save carrying a reserved key and nested value must not be rejected."""
    responses.add(
        responses.POST,
        f"{BASE}/context/ingest",
        json={"success": True, "data": {"success_count": 1}, "error": None},
        status=200,
    )
    _storage().save(
        "task output",
        metadata={
            "description": "a reserved key",
            "messages": [{"role": "user", "content": "hi"}],
            "quality": 0.9,
            "skip": None,
        },
    )
    body = responses.calls[0].request.body
    # free-form fields go to additional_metadata, reserved key is renamed, and
    # the nested value is flattened to a JSON string rather than sent raw.
    assert b"additional_metadata" in body
    assert b"crew_description" in body
    assert b'\\"role\\": \\"user\\"' in body or b'role' in body
    assert b'"description"' not in body


def test_extract_text_unwraps_envelope_with_trailing_context():
    """Recall text may be an envelope JSON plus trailing 'Extra context'."""
    from hydradb_crewai.client import _extract_text

    raw = (
        '{"content": {"text": "Ship Friday."}, "document_metadata": {"a": "b"}}'
        "\n\nExtra context: The beta ships Friday."
    )
    out = _extract_text(raw)
    assert out.startswith("Ship Friday.")
    assert "Extra context:" in out
    assert "document_metadata" not in out
