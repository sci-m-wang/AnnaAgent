from backbone import get_openai_client, model_name
import json

tools = [
    {
        "type": "function",
        "function": {
            'name': 'is_recognized',
            'description': '根据对话内容和主诉认知变化链，判断患者目前是否很好地认知到了当前阶段的主诉问题。',
            'parameters': {
                "type": "object",
                "properties": {
                    "is_recognized": {
                        "type": "boolean"
                    },
                }
                },
                "required": ["is_recognized"]
        }
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
        print("Transformed chain:", transformed_chain)

        # 提取对话记录
        dialogue_history = "\n".join(
            [f"{conv['role']}: {conv['content']}" for conv in conversation]
        )
        rewrite_prompt = [
            {
                "role": "system",
                "content": (
                    "你是提示词结构优化助手，负责将复杂原始输入信息（如对话历史、主诉变化链）"
                    "重写成清晰、结构化、适合小模型理解的提示词。请避免Markdown和JSON混排，"
                    "明确字段间语义，引导小模型完成任务。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"【任务目标】\n"
                    f"判断患者在当前阶段的主诉问题是否已经得到解决。\n\n"
                    f"【咨询对话历史】\n{dialogue_history}\n\n"
                    f"【主诉认知变化链（所有阶段）】\n{transformed_chain}\n\n"
                    f"【当前阶段内容】\n{transformed_chain[index]}\n\n"
                    f"请重写为一段提示词，便于小模型理解结构与任务，清晰传达："
                    f"对话背景、认知变化链、当前阶段内容、判断任务目标。"
                ),
            },
        ]

        # 用 GPT-4o 调用
        rewrite_response = client.chat.completions.create(
            model=model_name,
            messages=rewrite_prompt,
        )

        # 得到结构优化后的提示词内容
        optimized_prompt = rewrite_response.choices[0].message.content
        response = client.chat.completions.create(
            model=model_name,  # 小模型，如 gpt-3.5 或更轻量模型
            messages=[{"role": "user", "content": optimized_prompt}],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "is_recognized"}},
        )
        if json.loads(response.choices[0].message.tool_calls[0].function.arguments)[
            "is_recognized"
        ]:
            return index + 1
    except Exception as err:
        print("switch_complaint error:", err)
    return index
    