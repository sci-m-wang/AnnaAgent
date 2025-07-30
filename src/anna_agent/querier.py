import json
from .backbone import get_counselor_client
from .common.registry import registry

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
                "请判断下面这句咨询师的发言是否包含了对之前疗程或历史对话的提及。\n\n"
                "【任务说明】\n"
                "判断标准包括但不限于：是否提到了过去的咨询记录、曾讨论过的话题、上次谈话的内容，或者使用了‘你上次说过’、‘我们之前谈到’等引用性表达。\n\n"
                "【咨询师发言】\n"
                f"{utterance}\n\n"
                "请返回判断结果（是 / 否）以及判断依据。"
            ),
        }
    ]

    print(messages)
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "is_need"}},
    )

    return json.loads(response.choices[0].message.tool_calls[0].function.arguments)[
        "is_need"
    ]


def query(utterance, conversations, scales):
    # 根据utterance从conversations和scales中检索必要的信息
    client = get_counselor_client()
    # 原始输入结构
    raw_prompt = {
        "task": "根据对话内容，从知识库中搜索相关的信息并总结",
        "utterance": utterance,
        "conversations": conversations,
        "scales": scales
    }

    # 用强模型进行提示词结构优化
    rewrite_prompt = [
        {
            "role": "system",
            "content": (
                "你是一个提示词结构优化专家，擅长将任务信息重写成适合小模型理解、结构清晰的自然语言提示词。"
                "请根据以下内容，重写一段清晰、结构化的指令，以引导小模型从知识库中提取与用户发言密切相关的内容，"
                "并组织成 JSON 字段 `knowledge`。"
                "输出只需为优化后的提示词内容本身，不需要解释、注释或任何其他输出。"
            )
        },
        {
            "role": "user",
            "content": f"""任务描述：{raw_prompt['task']}

    【对话内容】
    {raw_prompt['utterance']}

    【知识库：历史会话】
    {raw_prompt['conversations']}

    【知识库：量表结果】
    {raw_prompt['scales']}
    """
        }
    ]

    # 用强模型（如 GPT-4o）生成优化提示词
    rewritten_prompt_response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,  # 推荐用强模型
        messages=rewrite_prompt
    )

    # 获取结构化优化后的提示词内容
    optimized_prompt = rewritten_prompt_response.choices[0].message.content
    # 用小模型调用工具
    response = client.chat.completions.create(
        model=registry.get("anna_engine_config").counselor_model_name,  # 小模型名称
        messages=[
            {
                "role": "user",
                "content": optimized_prompt
            }
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "search_knowledge"}}
    )
    print(response)
    # 提取结构化知识字段
    knowledge = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["knowledge"]

    return knowledge
