import json
from dataclasses import asdict
from pathlib import Path

from .chunking import build_memory_chunks
from .embeddings import EmbeddingService
from .models import MemoryChunk, MemoryHit, MemorySession


class LanceMemoryStore:
    def __init__(self, db_path: str | Path, table_name: str, embedding_service):
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.embedding_service = embedding_service
        self._db = None

    @classmethod
    def from_config(cls, config, workspace: str | Path | None = None):
        db_path = Path(config.memory_db_path)
        if not db_path.is_absolute() and workspace is not None:
            db_path = Path(workspace) / db_path
        return cls(
            db_path=db_path,
            table_name=config.memory_table_name,
            embedding_service=EmbeddingService(config),
        )

    def index_case(
        self,
        *,
        seeker_id: str,
        case_id: str,
        portrait: dict,
        report: dict,
        conversations: list[dict[str, str]],
        session_id: str = "session-001",
        session_index: int = 1,
        window_size: int = 4,
        window_stride: int = 2,
    ) -> int:
        chunks = build_memory_chunks(
            seeker_id=seeker_id,
            case_id=case_id,
            portrait=portrait,
            report=report,
            conversations=conversations,
            session_id=session_id,
            session_index=session_index,
            window_size=window_size,
            window_stride=window_stride,
        )
        count = self.add_chunks(chunks)
        self.upsert_session(
            MemorySession(
                seeker_id=seeker_id,
                case_id=case_id,
                session_id=session_id,
                session_index=session_index,
                summary=_session_summary_from_chunks(chunks),
                metadata=chunks[0].metadata if chunks else {},
            )
        )
        return count

    def upsert_session(self, session: MemorySession) -> None:
        path = self._sessions_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        sessions = []
        if path.exists():
            try:
                sessions = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                sessions = []
        session_key = (session.seeker_id, session.session_id)
        sessions = [
            item
            for item in sessions
            if (item.get("seeker_id"), item.get("session_id")) != session_key
        ]
        sessions.append(asdict(session))
        sessions.sort(
            key=lambda item: (item.get("seeker_id", ""), item.get("session_index", 0))
        )
        path.write_text(
            json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_chunks(self, chunks: list[MemoryChunk]) -> int:
        records = self._records_from_chunks(chunks)
        if not records:
            return 0
        existing_hashes = self._existing_hashes()
        records = [
            record for record in records if record["source_hash"] not in existing_hashes
        ]
        if not records:
            return 0
        table = self._open_table()
        if table is None:
            self._create_table(records)
        else:
            table.add(records)
        return len(records)

    def search(
        self,
        query_text: str,
        *,
        seeker_id: str,
        top_k: int = 8,
    ) -> list[MemoryHit]:
        table = self._open_table()
        if table is None:
            return []
        vector = self.embedding_service.embed_query(query_text)
        where = f"seeker_id = '{_escape_sql(seeker_id)}'"
        rows = table.search(vector).where(where).limit(top_k).to_list()
        return [_row_to_hit(row) for row in rows]

    def format_hits(self, hits: list[MemoryHit]) -> str:
        if not hits:
            return ""
        lines = ["【长期记忆检索结果】"]
        for index, hit in enumerate(hits, start=1):
            label = f"{hit.source_type}/{hit.memory_type}"
            if hit.section:
                label = f"{label}/{hit.section}"
            if hit.turn_start >= 0:
                label = f"{label}/turns:{hit.turn_start}-{hit.turn_end}"
            lines.append(f"{index}. {label}\n{hit.text}")
        return "\n\n".join(lines)

    def _records_from_chunks(self, chunks: list[MemoryChunk]) -> list[dict]:
        vectors = self.embedding_service.embed_texts(
            [chunk.text_for_embedding for chunk in chunks]
        )
        records = []
        for chunk, vector in zip(chunks, vectors):
            record = asdict(chunk)
            record["metadata_json"] = json.dumps(
                record.pop("metadata"), ensure_ascii=False, sort_keys=True
            )
            record["vector"] = vector
            records.append(record)
        return records

    def _connect(self):
        if self._db is None:
            import lancedb

            self.db_path.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(self.db_path))
        return self._db

    def _sessions_path(self) -> Path:
        return self.db_path.parent / "sessions.json"

    def _open_table(self):
        db = self._connect()
        if self.table_name not in db.table_names():
            return None
        return db.open_table(self.table_name)

    def _create_table(self, records: list[dict]):
        db = self._connect()
        return db.create_table(self.table_name, data=records)

    def _existing_hashes(self) -> set[str]:
        table = self._open_table()
        if table is None:
            return set()
        try:
            if hasattr(table, "to_list"):
                data = table.to_list()
            else:
                data = table.to_arrow().to_pylist()
        except Exception:
            return set()
        return {row.get("source_hash", "") for row in data}


def _escape_sql(value: str) -> str:
    return value.replace("'", "''")


def _row_to_hit(row: dict) -> MemoryHit:
    metadata_raw = row.get("metadata_json") or "{}"
    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError:
        metadata = {}
    return MemoryHit(
        id=row.get("id", ""),
        seeker_id=row.get("seeker_id", ""),
        case_id=row.get("case_id", ""),
        session_id=row.get("session_id", ""),
        source_type=row.get("source_type", ""),
        memory_type=row.get("memory_type", ""),
        role=row.get("role", ""),
        turn_start=int(row.get("turn_start", -1)),
        turn_end=int(row.get("turn_end", -1)),
        section=row.get("section", ""),
        text=row.get("text", ""),
        score=float(row.get("_distance", 0.0)),
        metadata=metadata,
    )


def _session_summary_from_chunks(chunks: list[MemoryChunk]) -> str:
    for chunk in chunks:
        if chunk.memory_type == "session_summary":
            return chunk.text
    return ""
