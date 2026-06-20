import logging

from .backbone import get_openai_client
from .common.registry import registry
from .common.tool_calls import extract_tool_call_arguments

logger = logging.getLogger(__name__)

tools = [
    {
        "type": "function",
        "function": {
            "name": "is_recognized",
            "description": (
                "根据对话内容和主诉认知变化链，判断患者目前是否很好地认知到了"
                "当前阶段的主诉问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "is_recognized": {"type": "boolean"},
                },
            },
            "required": ["is_recognized"],
        },
    }
]


def transform_chain(chain):
    transformed_chain = {}
    for node in chain:
        transformed_chain[node["stage"]] = node["content"]
        pass
    return transformed_chain


def switch_complaint(chain, index, conversation):
    client = get_openai_client()

    try:
        transformed_chain = transform_chain(chain)
        logger.debug("transformed chain: %s", transformed_chain)

        # 提取对话记录
        dialogue_history = "\n".join(
            [f"{conv['role']}: {conv['content']}" for conv in conversation]
        )
        response = client.chat.completions.create(
            model=registry.get("anna_engine_config").model_name,  
            messages=[
                {
                    "role": "user",
                    "content": (
                        "### 任务\n"
                        "根据患者情况及咨访对话历史记录，判断患者当前阶段的主诉问题是否已经得到解决。"
                        f"\n### 咨访对话历史记录\n{dialogue_history}"
                        f"\n### 主诉认知变化链\n{transformed_chain}"
                        f"\n### 当前阶段\n{transformed_chain[index]}"
                    ),
                }
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "is_recognized"}},
        )
        args = extract_tool_call_arguments(response)
        if args and args.get("is_recognized"):
            return index + 1
    except Exception as err:
        logger.debug("switch_complaint error: %s", err)
    return index
