<p align="center">
  <img src="https://raw.githubusercontent.com/hydra-db/hydradb-crewai-plugin/main/assets/icon.png" width="96" alt="HydraDB" />
</p>

# crewai-hydradb

HydraDB as external memory for [CrewAI](https://crewai.com) agents. Your crews
recall relevant history on each task and persist their outputs into
[HydraDB](https://hydradb.com), so memory survives across runs.

## Install

```bash
pip install crewai-hydradb   # once published; for local dev: pip install -e .
```

## Prerequisites

- Python >= 3.10
- A HydraDB account: API key + tenant ID ([hydradb.com](https://hydradb.com))
- `crewai >= 1.0, < 1.11`

## CrewAI version compatibility

This integration implements CrewAI's `Storage` interface
(`crewai.memory.storage.interface.Storage`) wired via `ExternalMemory`, which
exists in CrewAI **1.0-1.10** (verified present in 1.5, removed in 1.11).
CrewAI **1.11+** restructured memory around a new embedding-based
`StorageBackend` protocol that expects the backend to store and search raw
embedding vectors - a poor fit for HydraDB's text-query recall. On 1.11+, use
HydraDB over MCP instead (`hydra-db/hydradb-mcp`), which exposes HydraDB's own
retrieval without a vector-store contract.

## Quick start

```python
from crewai import Crew
from crewai.memory.external.external_memory import ExternalMemory
from hydradb_crewai import HydraDBClient, HydraDBStorage

client = HydraDBClient(api_key="sk_live_...", tenant_id="your-tenant")

crew = Crew(
    agents=[...],
    tasks=[...],
    external_memory=ExternalMemory(storage=HydraDBStorage(client)),
)
crew.kickoff()
```

## Notes

- **Public API only.** `save` writes via the public knowledge path
  (`app_knowledge` → `/context/ingest`); `search` uses `POST /query`. The
  memory-family write route is not publicly exposed, so outputs are stored as
  knowledge (default `kind="knowledge"`).

## How it works

CrewAI's `ExternalMemory` delegates to a `Storage` implementation:

| CrewAI call | HydraDB |
|---|---|
| `save(value, metadata)` - after a task completes | ingest as HydraDB knowledge (`app_knowledge`) |
| `search(query, limit, score_threshold)` - before a task | hybrid recall from HydraDB |

This mirrors the pattern used by Mem0, Honcho, and Hindsight.

## Unified rollout preparation

Unified support is not enabled in production. Keep the default split layout
until your database's production rollout is confirmed. Then construct the client
with `HydraDBClient(..., layout="unified")`. Only `split` and `unified` are
accepted; failures never trigger a layout retry.

Unified saves send JSON `context[]`, with stable generated context IDs and
`infer` mapped to `enrich`. CrewAI's sanitized free-form metadata maps to
`custom_attributes`, while raw text-item `metadata` maps to `attributes`.
Raw `additional_metadata` also maps to `custom_attributes`.
The raw `add_knowledge` adapter supports text-only items with `id`, `title`,
`content.text`, `infer`, `metadata` and `additional_metadata`; unsupported
fields are rejected rather than dropped. Split writes remain unchanged.

Storage search keeps its content/context/memory/score/metadata dictionaries and
score filtering. Unified results retain separate chunk `id` and `context_id`,
`enrichment` and `received_at`, without invented source metadata.
`query()` still returns chunks; `query_result()` retains complete response
`.data` and envelope `.meta`, including root `graph[]`,
`forceful_relations[]`, `llm_prompt`, and `tabular_data`. This does not change
the supported CrewAI version range.

## Test

```bash
pip install -e ".[test]"
pytest
```

## License

Apache-2.0 - Copyright (c) 2026 HydraDB
