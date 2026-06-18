import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from anna_agent.memory import build_memory_chunks
from anna_agent.memory.embeddings import HashEmbeddingProvider


def test_build_memory_chunks_complete_schema():
    chunks = build_memory_chunks(
        seeker_id="seeker-1",
        case_id="case-1",
        portrait={
            "age": "30",
            "gender": "女",
            "occupation": "家庭主妇",
            "marital_status": "已婚",
            "symptoms": "胸闷;睡眠差",
        },
        report={
            "案例标题": "家庭压力导致的心理困扰",
            "案例类别": ["个人成长", "情感关系"],
            "咨询经过": ["来访者讨论了家庭压力。"],
        },
        conversations=[
            {"role": "Seeker", "content": "我觉得胸闷。"},
            {"role": "Counselor", "content": "这种感觉什么时候更明显？"},
            {"role": "Seeker", "content": "和丈夫争吵后。"},
        ],
        window_size=2,
        window_stride=1,
    )

    memory_types = {chunk.memory_type for chunk in chunks}
    assert "conversation_turn" in memory_types
    assert "conversation_window" in memory_types
    assert "session_summary" in memory_types
    assert "report_section" in memory_types
    assert "report_summary" in memory_types
    assert all(chunk.seeker_id == "seeker-1" for chunk in chunks)
    assert all(chunk.source_hash for chunk in chunks)


def test_hash_embedding_provider_is_deterministic():
    provider = HashEmbeddingProvider(dimension=16)
    first = provider.embed_texts(["家庭压力和胸闷"])[0]
    second = provider.embed_texts(["家庭压力和胸闷"])[0]
    assert first == second
    assert len(first) == 16
