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
            "role": "user",
            "content": (
                "请你根据以下量表问题与两次填写的答案，对比分析两次BDI量表在各个维度上的变化。\n\n"
                "【任务目标】\n"
                "识别两个时间点之间的心理状态变化，包括明显改善、恶化或无显著变化的条目。\n\n"
                "【量表问题与选项】\n"
                f"{bdi_scale}\n\n"
                "【第一次填写（前测）答案】\n"
                f"{scales['p_bdi']}\n\n"
                "【第二次填写（后测）答案】\n"
                f"{scales['bdi']}\n\n"
                "请输出总结结果，包括变化趋势和需要重点关注的条目。"
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
            "role": "user",
            "content": (
                "请你根据以下 GHQ-28 心理量表的问题描述与两次填写的答案，对比分析该个体在心理健康方面的变化趋势。\n\n"
                "【任务目标】\n"
                "识别两次评估之间的显著变化，包括症状改善、恶化或保持稳定的维度，并总结出值得关注的方面。\n\n"
                "【量表问题描述】\n"
                f"{ghq_scale}\n\n"
                "【第一次评估（前测）答案】\n"
                f"{scales['p_ghq']}\n\n"
                "【第二次评估（后测）答案】\n"
                f"{scales['ghq']}\n\n"
                "请输出总结结果，包括每个条目的变化趋势与总体心理状态的分析。"
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
            "role": "user",
            "content": (
                "请你根据以下 SASS（社会适应自评量表）的问题和两次评估的答案，对比分析该个体在社会适应能力方面的变化。\n\n"
                "【任务目标】\n"
                "请指出每一项在前测与后测之间的变化趋势，判断是否有改善、恶化或保持不变，并总结整体趋势与值得关注的问题项。\n\n"
                "【量表问题列表】\n"
                f"{sass_scale}\n\n"
                "【第一次评估（前测）答案】\n"
                f"{scales['p_sass']}\n\n"
                "【第二次评估（后测）答案】\n"
                f"{scales['sass']}\n\n"
                "请将输出内容组织为结构化结果（如每项变化+解释），并总结整体趋势。"
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



