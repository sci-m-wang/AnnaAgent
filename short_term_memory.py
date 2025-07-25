from openai import OpenAI
import json
from backbone import api_key, model_name, base_url

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
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    # 导入量表及问题
    bdi_scale = json.load(open("./scales/bdi.json", "r"))
    ghq_scale = json.load(open("./scales/ghq-28.json", "r"))
    sass_scale = json.load(open("./scales/sass.json", "r"))
    messages = [
        {
            "role": "system",
            "content": (
                "你是一位专业的心理量表对比分析专家，擅长分析心理量表在不同时间点填写答案的变化趋势，"
                "你的任务是根据 '量表问题与选项'、'第一次填写答案'、'第二次填写答案'，"
                "对每一道题目的变化进行判断，并明确标出改善、恶化或无变化。"
                "你必须返回一个 JSON 格式结果，其中列出每个条目的变化与解释，并总结总体心理趋势。"
            )
        },
        {
            "role": "user",
            "content": (
                "【分析目标】\n"
                "请你对比患者前测和后测的 BDI（贝克抑郁量表）答案，根据每一题目的选项变化判断：是否存在心理状态改善、恶化或无变化。\n\n"
                "【量表问题与选项】\n"
                f"{bdi_scale}\n\n"
                "【第一次填写答案（前测）】\n"
                f"{scales['p_bdi']}\n\n"
                "【第二次填写答案（后测）】\n"
                f"{scales['bdi']}\n\n"
                "【输出要求】\n"
                "请输出以下结构的 JSON：\n"
                "- changes: 一个包含每个题目变化的数组，每项包含 'item', 'change'（改善/恶化/无变化）, 'explanation' 字段\n"
                "- summary: 一个字符串，概括整体趋势，例如“整体心理状态略有改善”或“症状未见明显变化”。\n"
                "不要输出除 JSON 结构之外的其他内容。"
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
                "你是一位极其严谨、结构化、客观的心理量表分析专家，专门负责评估 GHQ-28 心理健康量表在不同时点的变化，"
                "任务是根据题目描述与两次作答情况，对每一道题的变化进行判断，并输出结构化结果。"
            )
        },
        {
            "role": "user",
            "content": (
                "【任务目标】\n"
                "根据 GHQ-28 量表的题目内容和患者在两个时间点的作答情况，对每一道题进行分析：判断该题目的心理状态是否改善、恶化或无明显变化。\n"
                "你需要输出结构化的 JSON，其中包括：\n"
                "1. 每一道题的变化判断：字段包括 'item'（题目编号或标题）、'change'（改善 / 恶化 / 无变化）、'explanation'（解释变化原因）。\n"
                "2. 整体趋势总结：字段 'summary'，概括该患者整体心理健康状态是否改善、恶化或无变化，并指出值得关注的具体领域。\n\n"
                "【GHQ-28 量表题目与选项】\n"
                f"{ghq_scale}\n\n"
                "【第一次评估（前测）答案】\n"
                f"{scales['p_ghq']}\n\n"
                "【第二次评估（后测）答案】\n"
                f"{scales['ghq']}\n\n"
                "请严格以 JSON 输出结果，仅包含以下两个字段：\n"
                "- `changes`: 列表，每项表示一道题的变化分析\n"
                "- `summary`: 字符串，概述整体趋势\n\n"
                "不要在 JSON 前后添加任何文本，也不要输出 Markdown 语法。"
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
                "你是一位极其严谨、结构化、客观的心理状态评估专家，"
                "任务是基于 SASS（社会适应自评量表）的问题与患者在两个时间点的作答，"
                "识别其社会适应能力方面的变化，并输出标准化结构的评估结果。"
            )
        },
        {
            "role": "user",
            "content": (
                "【核心任务】\n"
                "根据以下输入信息，分析患者在社会适应方面的变化：\n\n"
                "1. 量表问题及选项：定义每一项测量维度\n"
                "2. 前测答案：初次评估结果\n"
                "3. 后测答案：随访评估结果\n\n"
                "你的输出必须满足以下结构：\n"
                "- `changes`: 一个数组，每项表示一题的变化，包括：\n"
                "   - `item`: 题目内容或编号\n"
                "   - `change`: '改善'、'恶化' 或 '无变化'\n"
                "   - `explanation`: 对变化的简要解释\n"
                "- `summary`: 总结整体社会适应能力的变化趋势\n\n"
                "【SASS 量表问题与选项】\n"
                f"{sass_scale}\n\n"
                "【第一次评估（前测）答案】\n"
                f"{scales['p_sass']}\n\n"
                "【第二次评估（后测）答案】\n"
                f"{scales['sass']}\n\n"
                "请严格按要求输出完整 JSON 对象，不要添加除 JSON 外的任何文本、注释或格式符号。"
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
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
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



