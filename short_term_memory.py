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
    # 总结bdi的变化
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据量表的问题和答案，总结出两份量表之间的变化。\n### 量表及问题\{bdi_scale} ### 第一份量表的答案\n{scales['p_bdi']}\n### 第二份量表的答案\n{scales['bdi']}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}}
    )
    bdi_changes = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["changes"]
    # 总结ghq的变化
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据量表的问题和答案，总结出两份量表之间的变化。\n### 量表及问题\{ghq_scale} ### 第一份量表的答案\n{scales['p_ghq']}\n### 第二份量表的答案\n{scales['ghq']}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_scale"}}
    )
    ghq_changes = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["changes"]
    # 总结sass的变化
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据量表的问题和答案，总结出两份量表之间的变化。\n### 量表及问题\{sass_scale} ### 第一份量表的答案\n{scales['p_sass']}\n### 第二份量表的答案\n{scales['sass']}"}
        ],
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
    # 总结量表变化
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据量表的变化，总结患者的身体和心理状态变化。\n### 量表变化\n{bdi_changes}\n{ghq_changes}\n{sass_changes}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "summarizing_changes"}}
    )
    # print(response)
    status = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["status"]
    return status



