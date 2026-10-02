"""CrewAI external-memory storage backed by HydraDB.

CrewAI's ``ExternalMemory`` delegates to a ``Storage`` implementation with two
core operations: ``save`` (persist a task output) and ``search`` (recall
relevant history). This maps ``save`` → HydraDB ingest and ``search`` → HydraDB
recall, so a crew's memory lives in HydraDB and persists across runs.
"""

from __future__ import annotations

from typing import Any

from .client import HydraDBClient

try:
    from crewai.memory.storage.interface import Storage as _BaseStorage
except Exception:  # pragma: no cover

    class _BaseStorage:
        def save(self, value: Any, metadata: dict[str, Any]) -> None: ...

        def search(
            self, query: str, limit: int = 3, score_threshold: float = 0.35
        ) -> list[Any]: ...

        def reset(self) -> None: ...


class HydraDBStorage(_BaseStorage):
    """A CrewAI ``Storage`` that reads and writes HydraDB memory.

    Example::

        from crewai import Crew
        from crewai.memory.external.external_memory import ExternalMemory
        from hydradb_crewai import HydraDBStorage

        crew = Crew(
            agents=[...],
            tasks=[...],
            external_memory=ExternalMemory(
                storage=HydraDBStorage(
                    HydraDBClient(api_key="sk_live_...", tenant_id="your-tenant")
                )
            ),
        )
    """

    def __init__(
        self,
        client: HydraDBClient,
        kind: str = "knowledge",
        infer: bool = True,
    ) -> None:
        self.client = client
        self.kind = kind
        self.infer = infer

    def save(self, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Persist a task output into HydraDB."""
        text = value if isinstance(value, str) else str(value)
        self.client.add_text(text, infer=self.infer, metadata=metadata or {})

    def search(
        self,
        query: str,
        limit: int = 3,
        score_threshold: float = 0.35,
    ) -> list[dict[str, Any]]:
        """Recall relevant history for the current task."""
        chunks = self.client.query(query, kind=self.kind, max_results=limit)
        results: list[dict[str, Any]] = []
        for chunk in chunks:
            if chunk.score is not None and chunk.score < score_threshold:
                continue
            results.append(
                {
                    "content": chunk.text,
                    "context": chunk.text,
                    "memory": chunk.text,
                    "score": chunk.score,
                    "metadata": {
                        "source_title": chunk.source_title,
                        "id": chunk.id,
                        **chunk.metadata,
                    },
                }
            )
        return results

    def reset(self) -> None:
        """No bulk reset over the public API; delete by id via the client."""
        return None
