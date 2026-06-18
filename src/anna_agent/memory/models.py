from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1


@dataclass
class MemoryChunk:
    id: str
    seeker_id: str
    case_id: str
    session_id: str
    session_index: int
    source_type: str
    memory_type: str
    text: str
    text_for_embedding: str
    role: str = ""
    turn_start: int = -1
    turn_end: int = -1
    section: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_hash: str = ""
    schema_version: int = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryHit:
    id: str
    seeker_id: str
    case_id: str
    session_id: str
    source_type: str
    memory_type: str
    text: str
    score: float
    role: str = ""
    turn_start: int = -1
    turn_end: int = -1
    section: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySession:
    seeker_id: str
    case_id: str
    session_id: str
    session_index: int
    summary: str
    source_file: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)
