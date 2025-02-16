from openai import OpenAI
import json
from backbone import api_key, model_name, base_url

tools = [
    {
        "type": "function",
        "function": {
            'name': 'fill_bdi',
            'description': '填写BDI量表',
            'parameters': {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D"]
                        },
                        "minItems": 21,
                        "maxItems": 21
                    },
                }
            },
            "required": ["answers"]
        }
    },
    {
        "type": "function",
        "function": {
            'name': 'fill_ghq',
            'description': '填写GHQ-28量表',
            'parameters': {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D"]
                        },
                        "minItems": 28,
                        "maxItems": 28
                    }
                }
            },
            "required": ["answers"]
        }
    },
    {
        "type": "function",
        "function": {
            'name': 'fill_sass',
            'description': '填写SASS量表',
            'parameters': {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum":["A", "B", "C", "D"]
                        },
                        "minItems": 21,
                        "maxItems": 21
                    }
                }
            },
            "required": ["answers"]
        }
    }
]

# 根据profile和report填写之前的量表
def fill_scales_previous(profile, report):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    # 填写BDI量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据个人描述和报告，填写量表。\n### 个人描述\n{profile}\n### 报告\n{report}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}}
    )
    bdi = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    # 填写GHQ-28量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据个人描述和报告，填写量表。\n### 个人描述\n{profile}\n### 报告\n{report}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}}
    )
    ghq = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    # 填写SASS量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据个人描述和报告，填写量表。\n### 个人描述\n{profile}\n### 报告\n{report}"}
        ],
        tools = tools,
        tool_choice={"type": "function","function": {"name": "fill_sass"}}
    )
    sass = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    return bdi, ghq, sass

# 根据prompt填写量表
def fill_scales(prompt):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    # 填写BDI量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"### 任务\n填写量表。"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}}
    )
    bdi = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    # 填写GHQ-28量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"### 任务\n填写量表。"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}}
    )
    ghq = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    # 填写SASS量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"### 任务\n填写量表。"}
        ],
        tools = tools,
        tool_choice={"type": "function","function": {"name": "fill_sass"}}
    )
    sass = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    return bdi, ghq, sass