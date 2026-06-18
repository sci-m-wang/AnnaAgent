import hashlib
import json
from typing import Any

from .models import MemoryChunk


def _hash_source(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _chunk_id(source_hash: str) -> str:
    return source_hash[:24]


def _report_values(report: dict[str, Any]) -> str:
    values = []
    for key, value in report.items():
        if isinstance(value, list):
            values.append(f"{key}: {' '.join(str(item) for item in value)}")
        else:
            values.append(f"{key}: {value}")
    return "\n".join(values)


def _metadata(portrait: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    return {
        "age": portrait.get("age", ""),
        "gender": portrait.get("gender", ""),
        "occupation": portrait.get("occupation", ""),
        "marital_status": portrait.get("martial_status")
        or portrait.get("marital_status", ""),
        "symptoms": portrait.get("symptoms", ""),
        "case_title": report.get("案例标题", ""),
        "case_categories": report.get("案例类别", []),
        "techniques": report.get("运用的技术", []),
    }


def build_memory_chunks(
    *,
    seeker_id: str,
    case_id: str,
    portrait: dict[str, Any],
    report: dict[str, Any],
    conversations: list[dict[str, str]],
    session_id: str = "session-001",
    session_index: int = 1,
    window_size: int = 4,
    window_stride: int = 2,
) -> list[MemoryChunk]:
    metadata = _metadata(portrait, report)
    chunks: list[MemoryChunk] = []

    for index, utterance in enumerate(conversations):
        role = utterance.get("role", "")
        content = utterance.get("content", "")
        text = f"{role}: {content}"
        text_for_embedding = (
            "[conversation_turn]\n"
            f"seeker_id: {seeker_id}\n"
            f"session_id: {session_id}\n"
            f"turn: {index}\n"
            f"{text}"
        )
        source_hash = _hash_source(case_id, session_id, "turn", index, text)
        chunks.append(
            MemoryChunk(
                id=_chunk_id(source_hash),
                seeker_id=seeker_id,
                case_id=case_id,
                session_id=session_id,
                session_index=session_index,
                source_type="conversation",
                memory_type="conversation_turn",
                role=role,
                turn_start=index,
                turn_end=index,
                text=text,
                text_for_embedding=text_for_embedding,
                source_hash=source_hash,
                metadata=metadata,
            )
        )

    stride = max(1, window_stride)
    size = max(1, window_size)
    for start in range(0, len(conversations), stride):
        window = conversations[start : start + size]
        if len(window) < 2:
            continue
        end = start + len(window) - 1
        text = "\n".join(
            f"{item.get('role', '')}: {item.get('content', '')}" for item in window
        )
        text_for_embedding = (
            "[conversation_window]\n"
            f"seeker_id: {seeker_id}\n"
            f"session_id: {session_id}\n"
            f"turns: {start}-{end}\n"
            f"case_title: {metadata['case_title']}\n"
            f"symptoms: {metadata['symptoms']}\n"
            f"{text}"
        )
        source_hash = _hash_source(case_id, session_id, "window", start, end, text)
        chunks.append(
            MemoryChunk(
                id=_chunk_id(source_hash),
                seeker_id=seeker_id,
                case_id=case_id,
                session_id=session_id,
                session_index=session_index,
                source_type="conversation",
                memory_type="conversation_window",
                turn_start=start,
                turn_end=end,
                text=text,
                text_for_embedding=text_for_embedding,
                source_hash=source_hash,
                metadata=metadata,
            )
        )

    seeker_lines = [
        item.get("content", "")
        for item in conversations
        if item.get("role") == "Seeker"
    ]
    session_summary = (
        f"来访者画像：{metadata['age']}岁{metadata['gender']}，"
        f"{metadata['occupation']}，症状包括{metadata['symptoms']}。"
        f"本疗程主题：{metadata['case_title']}。"
        f"关键表达：{' '.join(seeker_lines[:5])}"
    )
    source_hash = _hash_source(case_id, session_id, "session_summary", session_summary)
    chunks.append(
        MemoryChunk(
            id=_chunk_id(source_hash),
            seeker_id=seeker_id,
            case_id=case_id,
            session_id=session_id,
            session_index=session_index,
            source_type="conversation",
            memory_type="session_summary",
            text=session_summary,
            text_for_embedding=f"[session_summary]\n{session_summary}",
            source_hash=source_hash,
            metadata=metadata,
        )
    )

    for section, value in report.items():
        values = value if isinstance(value, list) else [value]
        for item_index, item in enumerate(values):
            text = str(item)
            text_for_embedding = (
                "[report_section]\n"
                f"seeker_id: {seeker_id}\n"
                f"case_title: {metadata['case_title']}\n"
                f"section: {section}\n"
                f"content: {text}"
            )
            source_hash = _hash_source(case_id, "report", section, item_index, text)
            chunks.append(
                MemoryChunk(
                    id=_chunk_id(source_hash),
                    seeker_id=seeker_id,
                    case_id=case_id,
                    session_id=session_id,
                    session_index=session_index,
                    source_type="report",
                    memory_type="report_section",
                    section=section,
                    text=text,
                    text_for_embedding=text_for_embedding,
                    source_hash=source_hash,
                    metadata=metadata,
                )
            )

    report_summary = _report_values(report)
    source_hash = _hash_source(case_id, "report_summary", report_summary)
    chunks.append(
        MemoryChunk(
            id=_chunk_id(source_hash),
            seeker_id=seeker_id,
            case_id=case_id,
            session_id=session_id,
            session_index=session_index,
            source_type="report",
            memory_type="report_summary",
            text=report_summary,
            text_for_embedding=f"[report_summary]\n{report_summary}",
            source_hash=source_hash,
            metadata=metadata,
        )
    )

    return chunks
