import json
from backbone import get_openai_client, model_name

tools = [
    {
        "type": "function",
        "function": {
            'name': 'summarizing_scale',
            'description': '根据量表内容和选项，总结两个量表之间的变化。',
            'parameters': {
                "type": "object",
                "properties": {
                    "changes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        }
                    }
                }
            },
            "required": ["changes"]
        }
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
                }
            },
            "required": ["status"]
        }
    }
]

def analyzing_changes(scales):
    client = get_openai_client()
    # 导入量表及问题
    bdi_scale = json.load(open("./scales/bdi.json", "r"))
    ghq_scale = json.load(open("./scales/ghq-28.json", "r"))
    sass_scale = json.load(open("./scales/sass.json", "r"))
    messages = [
        {
            "role": "system",
            "content": (
                "你是一位极其严谨、结构清晰、判断客观的心理量表对比分析专家，"
                "配备专业工具以精确分析心理状态在不同时点的演变趋势。"
                "你当前的任务是根据贝克抑郁量表（BDI）的问题内容与患者两次作答情况，评估其心理状态是否出现改善、恶化或无变化，"
                "并以标准结构返回 JSON 格式的分析结果。"
            )
        },
        {
            "role": "user",
            "content": (
                "**核心任务描述：**\n"
                "1. **逐项分析**：对比患者前测与后测在每一题的作答结果，判断该题对应的心理状态是否改善、恶化或无明显变化。\n"
                "2. **变化解释**：对每个判断结果，提供清晰、简要的解释，说明为什么该题属于某种变化。\n"
                "3. **趋势总结**：综合所有题目的变化情况，判断整体心理状态的趋势（如整体改善、整体恶化或无显著变化）。\n\n"
                "**输入信息：**\n"
                "- **量表问题与选项（bdi_scale）**：每一题的内容与作答选项。\n"
                "- **第一次填写答案（p_bdi）**：初测作答结果。\n"
                "- **第二次填写答案（bdi）**：随访作答结果。\n\n"
                "**输出格式（务必严格遵守）：**\n"
                "你必须输出一个**完整、结构化且有效的 JSON 对象**，其包含以下字段：\n"
                "- `changes`: 一个数组，表示每一题的变化结果，每项结构为：\n"
                "  - `item`: (String) 题目内容或编号\n"
                "  - `change`: (String) 取值为 `改善`、`恶化` 或 `无变化` 三选一\n"
                "  - `explanation`: (String) 简要说明判断依据，如：“评分从3降为1，情绪困扰明显缓解”\n"
                "- `summary`: (String) 综合描述整体心理状态变化，例如“整体症状改善明显，尤其在情绪调节方面”或“未观察到显著变化”。\n\n"
                "**输出要求：**\n"
                "- **禁止**添加任何非 JSON 内容，如 Markdown 标记、注释、额外文字。\n"
                "- 字段名称、值、结构必须完整、准确、统一。\n\n"
                "**输入数据如下：**\n"
                "【量表问题与选项】\n"
                f"{bdi_scale}\n\n"
                "【第一次填写答案（前测）】\n"
                f"{scales['p_bdi']}\n\n"
                "【第二次填写答案（后测）】\n"
                f"{scales['bdi']}\n\n"
                "请现在开始任务，并只输出符合要求的 JSON 格式结果。"
            )
        }
    ]

    print(messages)
    # 总结bdi的变化
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}}
    )
    bdi_changes = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["changes"]
    messages = [
        {
            "role": "system",
            "content": (
                "你是一位极其严谨、格式敏感、判断客观的心理健康评估专家，"
                "任务是根据 GHQ-28 心理健康量表中各个题目的内容与患者在两个时间点的作答，"
                "分析每一项心理状态是否存在显著变化，并生成结构化输出。"
            )
        },
        {
            "role": "user",
            "content": (
                "**核心任务说明：**\n"
                "1. 逐项对比：根据 GHQ-28 的每一道题，对比第一次与第二次作答的分数变化，判断是否发生“改善”、“恶化”或“无变化”。\n"
                "2. 提供解释：对每一项变化给出简洁合理的解释。\n"
                "3. 总结趋势：基于全部题目变化，判断整体心理健康趋势，并指出是否有值得关注的领域。\n\n"
                "**输出结构格式：**\n"
                "```json\n"
                "{\n"
                "  \"changes\": [\n"
                "    {\n"
                "      \"item\": \"第1题：是否容易紧张？\",\n"
                "      \"change\": \"改善\",\n"
                "      \"explanation\": \"评分从2降为1，表明紧张程度下降\"\n"
                "    },\n"
                "    ...\n"
                "  ],\n"
                "  \"summary\": \"整体心理健康状态有轻微改善，情绪反应相关项改善较明显，但社交功能部分无变化。\"\n"
                "}\n"
                "```\n"
                "**输出要求：**\n"
                "- 结果必须为纯 JSON 对象，不能添加任何额外文字、注释、Markdown 符号等格式信息。\n"
                "- 字段 `change` 的取值仅限：`改善`、`恶化`、`无变化`。\n"
                "- 字段 `summary` 必须用一句话完整描述整体心理变化趋势。\n\n"
                "**输入数据：**\n"
                "【GHQ-28 量表题目与选项】\n"
                f"{ghq_scale}\n\n"
                "【第一次评估（前测）答案】\n"
                f"{scales['p_ghq']}\n\n"
                "【第二次评估（后测）答案】\n"
                f"{scales['ghq']}\n\n"
                "请严格按照上述格式输出，结构不完整将视为任务失败。"
            )
        }
    ]


    print(messages)
    # 总结ghq的变化
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}}
    )
    ghq_changes = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["changes"]
    messages = [
        {
            "role": "system",
            "content": (
                "你是一位极其严谨、结构化、格式敏感的心理评估分析专家，"
                "任务是基于患者在两个时间点填写的 SASS（社会适应自评量表）答案，"
                "评估其社会适应能力是否发生变化，并按照结构化标准输出评估结果。\n\n"
                "你配备有结构化输出工具，只能以指定字段格式返回结果。"
            )
        },
        {
            "role": "user",
            "content": (
                "**任务目标：**\n"
                "根据以下输入内容，对 21 项 SASS 问题进行逐项比较，判断每项状态是否存在显著变化，并对每一项输出如下信息：\n"
                "- `item`: 问题编号或简要题目；\n"
                "- `change`: 必须是 '改善'、'恶化' 或 '无变化' 三个中的一个；\n"
                "- `explanation`: 简要说明变化趋势的推理理由。\n\n"
                "**整体输出格式：**\n"
                "```json\n"
                "{\n"
                "  \"changes\": [...],\n"
                "  \"summary\": \"(整体变化趋势总结，语言简洁明确)\"\n"
                "}\n"
                "```\n"
                "**绝对禁止输出除 JSON 外的任何文本、注释或 Markdown 符号。**\n\n"
                "**输入信息：**\n"
                "1. 【SASS 量表问题与选项】：\n"
                f"{sass_scale}\n\n"
                "2. 【第一次评估（前测）答案】：\n"
                f"{scales['p_sass']}\n\n"
                "3. 【第二次评估（后测）答案】：\n"
                f"{scales['sass']}\n\n"
                "**请严格按照指定格式输出结果，否则将视为任务失败。**"
            )
        }
    ]

    # 总结sass的变化
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}}
    )
    sass_changes = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["changes"]
    return bdi_changes, ghq_changes, sass_changes

def summarize_scale_changes(scales):
    client = get_openai_client()
    # 获取量表变化
    bdi_changes, ghq_changes, sass_changes = analyzing_changes(scales)
    messages = [
        {
            "role": "user",
            "content": (
                "请根据以下三个心理量表的变化信息，综合分析患者在心理、情绪、身体、社会适应等方面的状态变化。\n\n"
                "【任务目标】\n"
                "1. 识别患者在三类量表中分别反映的主要问题变化；\n"
                "2. 总结患者当前整体的心理健康趋势（例如改善、恶化或稳定）；\n"
                "3. 对显著变化的维度给出解释（如可能的应激源、改善机制）。\n\n"
                "【BDI 抑郁量表变化】（反映情绪与认知问题）\n"
                f"{bdi_changes}\n\n"
                "【GHQ 心理健康变化】（反映心理压力和功能）\n"
                f"{ghq_changes}\n\n"
                "【SASS 社会适应变化】（反映社会行为与适应能力）\n"
                f"{sass_changes}\n\n"
                "请输出结构化总结，包括：心理状态变化、身体状态变化、社交适应变化、总体趋势评估。"
            )
        }
    ]

    print(messages)
    # 总结量表变化
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_changes"}}
    )
    print(response)
    status = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["status"]
    return status



