"""CrewAI integration for HydraDB - external memory storage."""

from .client import HydraChunk, HydraDBClient, HydraDBError, HydraQueryResult
from .storage import HydraDBStorage

__all__ = ["HydraDBClient", "HydraChunk", "HydraQueryResult", "HydraDBError", "HydraDBStorage"]

__version__ = "0.1.0"
