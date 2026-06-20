import logging

from .backbone import get_counselor_client
from .common.registry import registry
from .common.tool_calls import extract_tool_call_arguments

logger = logging.getLogger(__name__)


def _extract_answers(response, expected_length, default="B"):
    args = extract_tool_call_arguments(response)
    answers = args.get("answers") if args else None
    if isinstance(answers, list) and len(answers) == expected_length:
        return answers
    return [default] * expected_length

tools = [
    {
        "type": "function",
        "function": {
            "name": "fill_bdi",
            "description": "填写BDI量表",
            "parameters": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["A", "B", "C", "D"]},
                        "minItems": 21,
                        "maxItems": 21,
                    },
                },
            },
            "required": ["answers"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_ghq",
            "description": "填写GHQ-28量表",
            "parameters": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["A", "B", "C", "D"]},
                        "minItems": 28,
                        "maxItems": 28,
                    }
                },
            },
            "required": ["answers"],
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_sass",
            "description": "填写SASS量表",
            "parameters": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["A", "B", "C", "D"]},
                        "minItems": 21,
                        "maxItems": 21,
                    }
                },
            },
            "required": ["answers"],
        },
    },
]


# 根据profile和report填写之前的量表
def fill_scales_previous(profile, report):
    """
    结构化信息转换成非结构化文本数据，免去模型对语义解析的理解错误
    """
    client = get_counselor_client()
    prompt = (
        "### 任务\n根据个人描述和报告，填写量表。"
        f"\n### 个人描述\n{profile}"
        f"\n### 报告\n{report}"
    )

    # 填写BDI量表
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}},
    )

    logger.debug("BDI response: %s", response)
    bdi = _extract_answers(response, 21)

    # 填写GHQ-28量表
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}},
    )
    # print(response.choices[0].message.tool_calls[0].function.arguments)
    ghq = _extract_answers(response, 28)

    # 填写SASS量表
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_sass"}},
    )

    # Step 3：提取量表答案
    sass = _extract_answers(response, 21)

    return bdi, ghq, sass


# 根据prompt填写量表
def fill_scales(prompt):
    client = get_counselor_client()
    logger.debug("scale prompt: %s", prompt)
    task_prompt = "### 任务\n请根据你的情况填写量表。"

    # 填写BDI量表
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": task_prompt},
        ],
        tools=tools,
        temperature=0.1,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}},
    )
    logger.debug("BDI response: %s", response)
    bdi = _extract_answers(response, 21)
    # 填写GHQ-28量表
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": task_prompt},
        ],
        temperature=0.1,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}},
    )

    logger.debug("GHQ response: %s", response)
    ghq = _extract_answers(response, 28)
    # 填写SASS量表
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": task_prompt},
        ],
        temperature=0.1,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_sass"}},
    )

    logger.debug("SASS response: %s", response)
    sass = _extract_answers(response, 21)
    return bdi, ghq, sass
