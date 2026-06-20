import logging

from .backbone import get_counselor_client
from .common.registry import registry
from .common.tool_calls import extract_tool_call_arguments

logger = logging.getLogger(__name__)

tools = [
    {
        "type": "function",
        "function": {
            "name": "is_need",
            "description": "根据对话内容判断是否涉及之前疗程的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_need": {"type": "boolean"},
                },
            },
            "required": ["is_need"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "根据对话内容，从知识库中搜索相关的信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "knowledge": {"type": "string"},
                },
            },
            "required": ["knowledge"],
        },
    },
]


def is_need(utterance):
    client = get_counselor_client()
    messages = [
        {
            "role": "user",
            "content": (
                "下面这句话是心理咨询师说的话，请判断它是否提及了之前疗程的内容。"
                f"\n### 话语\n{utterance}"
            ),
        }
    ]

    logger.debug("memory need messages: %s", messages)
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "is_need"}},
    )

    args = extract_tool_call_arguments(response)
    return bool(args.get("is_need")) if args else False


def query(utterance, conversations, scales):
    # 根据utterance从conversations和scales中检索必要的信息
    cfg = registry.get("anna_engine_config")
    store = registry.get("long_term_memory_store")
    seeker_id = registry.get("long_term_memory_seeker_id")
    if cfg and cfg.memory_enabled and store and seeker_id:
        hits = store.search(utterance, seeker_id=seeker_id, top_k=cfg.memory_top_k)
        formatted_hits = store.format_hits(hits)
        if formatted_hits:
            return formatted_hits

    client = get_counselor_client()
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[
            {
                "role": "user",
                "content": (
                    "### 任务\n根据对话内容，从知识库中搜索相关的信息并总结。"
                    f"\n### 对话内容\n{utterance}"
                    f"\n### 知识库\n{conversations}\n{scales}"
                ),
            }
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "search_knowledge"}}
    )
    logger.debug("knowledge response: %s", response)
    # 提取结构化知识字段
    args = extract_tool_call_arguments(response)
    knowledge = args.get("knowledge") if args else ""

    return knowledge
