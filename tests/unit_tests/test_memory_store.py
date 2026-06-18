import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from anna_agent.memory import LanceMemoryStore, MemoryChunk


class FakeEmbeddingService:
    def embed_texts(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]


def test_lance_memory_store_skips_duplicate_chunks(tmp_path):
    store = LanceMemoryStore(
        db_path=tmp_path / "lancedb",
        table_name="chunks",
        embedding_service=FakeEmbeddingService(),
    )
    chunk = MemoryChunk(
        id="chunk-1",
        seeker_id="seeker-1",
        case_id="case-1",
        session_id="session-1",
        session_index=1,
        source_type="conversation",
        memory_type="conversation_turn",
        text="Seeker: 最近压力很大",
        text_for_embedding="Seeker: 最近压力很大",
        source_hash="hash-1",
    )

    assert store.add_chunks([chunk]) == 1
    assert store.add_chunks([chunk]) == 0
