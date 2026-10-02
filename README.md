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

## Test

```bash
pip install -e ".[test]"
pytest
```

## License

Apache-2.0 - Copyright (c) 2026 HydraDB
