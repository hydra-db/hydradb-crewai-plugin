import json

import responses

from hydradb_crewai import HydraDBClient, HydraDBStorage

BASE = "https://api.hydradb.com"


@responses.activate
def test_unified_search_keeps_storage_contract_and_score_filtering():
    responses.add(responses.POST, BASE + "/query", json={"success": True, "data": {
        "chunks": [
            {"chunk_id": "c", "context_id": "s", "content": "body", "score": 0.7, "enrichment": "facts"},
            {"chunk_id": "low", "context_id": "s", "content": "drop", "score": 0.0},
        ]
    }})
    storage = HydraDBStorage(HydraDBClient("k", "db", layout="unified"))
    result = storage.search("question", score_threshold=0.3)
    assert len(result) == 1
    assert result[0]["content"] == result[0]["context"] == result[0]["memory"] == "body"
    assert result[0]["score"] == 0.7
    assert result[0]["metadata"]["id"] == "c"
    assert result[0]["metadata"]["context_id"] == "s"
    assert result[0]["metadata"]["enrichment"] == "facts"


@responses.activate
def test_unified_save_maps_sanitized_freeform_metadata_to_custom_attributes():
    responses.add(responses.POST, BASE + "/context/ingest",
                  json={"success": True, "data": {"success_count": 1}}, status=202)
    storage = HydraDBStorage(HydraDBClient("k", "db", layout="unified"))
    assert storage.save("task output", {"description": "reserved", "messages": [{"role": "user", "content": "hello"}], "skip": None}) is None
    item = json.loads(responses.calls[0].request.body)["context"][0]
    assert item["custom_attributes"] == {
        "crew_description": "reserved", "messages": json.dumps([{"role": "user", "content": "hello"}]),
    }
    assert "additional_metadata" not in item
    assert item["context_id"]

