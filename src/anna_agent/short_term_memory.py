import importlib.resources
import json
import logging

from .backbone import get_counselor_client
from .common.registry import registry
from .common.tool_calls import extract_tool_call_arguments

logger = logging.getLogger(__name__)


def _fallback_scale_changes(scale_name, previous_answers, current_answers):
    return [
        {
            "item": f"{scale_name}-{index}",
            "change": "无变化",
            "explanation": "模型未返回结构化工具调用，使用保守默认结果。",
        }
        for index, _ in enumerate(zip(previous_answers, current_answers), start=1)
    ]

tools = [
    {
        "type": "function",
        "function": {
            "name": "summarizing_scale",
            "description": "根据量表内容和选项，总结两个量表之间的变化。",
            "parameters": {
                "type": "object",
                "properties": {
                    "changes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    }
                },
            },
            "required": ["changes"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarizing_changes",
            "description": "将量表内容总结为患者的身体心理状态变化。",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                    }
                },
            },
            "required": ["status"],
        },
    },
]


def analyzing_changes(scales):
    client = get_counselor_client()
    # 导入量表及问题
    with importlib.resources.files("anna_agent.scales").joinpath("bdi.json").open(
        "r", encoding="utf-8"
    ) as f:
        bdi_scale = json.load(f)
    with importlib.resources.files("anna_agent.scales").joinpath("ghq-28.json").open(
        "r", encoding="utf-8"
    ) as f:
        ghq_scale = json.load(f)
    with importlib.resources.files("anna_agent.scales").joinpath("sass.json").open(
        "r", encoding="utf-8"
    ) as f:
        sass_scale = json.load(f)
    messages = [
        {
            "role": "user",
            "content": (
                "### 任务\n根据量表的问题和答案，总结出两份量表之间的变化。"
                f"\n### 量表及问题\n{bdi_scale}"
                f"\n### 第一份量表的答案\n{scales['p_bdi']}"
                f"\n### 第二份量表的答案\n{scales['bdi']}"
            ),
        },
    ]

    logger.debug("BDI change messages: %s", messages)
    # 总结bdi的变化
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}},
    )
    args = extract_tool_call_arguments(response)
    bdi_changes = (
        args.get("changes")
        if args and isinstance(args.get("changes"), list)
        else _fallback_scale_changes("BDI", scales["p_bdi"], scales["bdi"])
    )
    messages = [
        {
            "role": "user",
            "content": (
                "### 任务\n根据量表的问题和答案，总结出两份量表之间的变化。"
                f"\n### 量表及问题\n{ghq_scale}"
                f"\n### 第一份量表的答案\n{scales['p_ghq']}"
                f"\n### 第二份量表的答案\n{scales['ghq']}"
            ),
        },
    ]

    logger.debug("GHQ change messages: %s", messages)
    # 总结ghq的变化
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}},
    )
    args = extract_tool_call_arguments(response)
    ghq_changes = (
        args.get("changes")
        if args and isinstance(args.get("changes"), list)
        else _fallback_scale_changes("GHQ", scales["p_ghq"], scales["ghq"])
    )
    messages = [
        {
            "role": "user",
            "content": (
                "### 任务\n根据量表的问题和答案，总结出两份量表之间的变化。"
                f"\n### 量表及问题\n{sass_scale}"
                f"\n### 第一份量表的答案\n{scales['p_sass']}"
                f"\n### 第二份量表的答案\n{scales['sass']}"
            ),
        },
    ]

    # 总结sass的变化
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}},
    )
    args = extract_tool_call_arguments(response)
    sass_changes = (
        args.get("changes")
        if args and isinstance(args.get("changes"), list)
        else _fallback_scale_changes("SASS", scales["p_sass"], scales["sass"])
    )
    return bdi_changes, ghq_changes, sass_changes


def summarize_scale_changes(scales):
    client = get_counselor_client()
    # 获取量表变化
    bdi_changes, ghq_changes, sass_changes = analyzing_changes(scales)
    messages = [
        {
            "role": "user",
            "content": (
                "### 任务\n根据量表的变化，总结患者的身体和心理状态变化。"
                f"\n### 量表变化\n{bdi_changes}\n{ghq_changes}\n{sass_changes}"
            ),
        }
    ]

    logger.debug("scale summary messages: %s", messages)
    # 总结量表变化
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_changes"}},
    )
    logger.debug("scale summary response: %s", response)
    args = extract_tool_call_arguments(response)
    status = (
        args.get("status")
        if args and isinstance(args.get("status"), str)
        else "模型未返回结构化状态总结，暂按量表结果保守记录为状态稳定。"
    )
    return status
