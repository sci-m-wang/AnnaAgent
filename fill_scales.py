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

    # Step 0：原始数据
    task = "根据个人描述和案例报告填写心理量表（BDI）"
    raw_prompt = {
        "task": task,
        "profile": profile,
        "report": report
    }

    # Step 1：提示词优化（用大模型将提示词转换成更适合小模型理解的格式）
    rewrite_prompt = [
        {
            "role": "system",
            "content": "你是提示词重写助手，请根据以下输入，将提示词改写为更清晰、结构更适合小模型处理的自然语言版本。" +
                    "请避免混合 Markdown、JSON 和自然语言，采用标准自然语言表达，清晰划分字段，并增加语义提示。不需要回复其它信息，只完成提示词修改任务"
        },
        {
            "role": "user",
            "content": f"""任务：{raw_prompt['task']}

    【个人描述】
    {raw_prompt['profile']}

    【案例报告】
    {raw_prompt['report']}
    """
        }
    ]

    # 使用强模型优化提示词（建议用 gpt-4-1106-preview 或 gpt-4o）
    rewritten_response = client.chat.completions.create(
        model=model_name,  # 此为你目标小模型
        messages=rewrite_prompt
    )

    # 获取优化后的提示词内容（更结构化、语义清晰）
    optimized_prompt = rewritten_response.choices[0].message.content

    # Step 2：使用目标模型调用工具，填写BDI量表
    response = client.chat.completions.create(
        model=model_name,  # 此为你目标小模型
        messages=[
            {"role": "user", "content": optimized_prompt}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}}
    )
 
    print(response)
    bdi = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]

    # 用户原始输入
    raw_prompt = {
        "task": "根据个人描述和案例报告填写心理量表（GHQ-28）",
        "profile": profile,
        "report": report
    }
    # 第一步：使用较强大模型转换提示词，使其更适合小模型理解
    rewrite_prompt = [
        {
            "role": "system",
            "content": "你是提示词重写助手，请根据以下输入，输出一段更清晰、结构更适合小模型理解的提示词。不需要回复其它信息，只完成提示词修改任务" 
        },
        {
            "role": "user",
            "content": f"请重写以下内容，使其适合用于小语言模型理解与信息抽取：\n\n任务：{raw_prompt['task']}\n\n个人描述：{raw_prompt['profile']}\n\n案例报告：{raw_prompt['report']}"
        }
    ]

    # 使用更强大的模型重写提示词（推荐用 gpt-4-1106-preview 或 gpt-4o）
    rewritten_response = client.chat.completions.create(
        model=model_name,
        messages=rewrite_prompt
    )

    # 获取优化后的提示词内容
    optimized_prompt = rewritten_response.choices[0].message.content

    # 第二步：将优化后的提示词传入目标模型，执行 GHQ 量表工具调用
    messages = [
        {
            "role": "user",
            "content": optimized_prompt
        }
    ]

    print(messages)
    # 填写GHQ-28量表
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}}
    )
    # print(response.choices[0].message.tool_calls[0].function.arguments)
    ghq = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
 
    # Step 0：原始内容结构
    raw_prompt = {
        "task": "根据个人描述和案例报告填写SASS（社会适应自评量表）",
        "profile": profile,
        "report": report
    }

    # Step 1：先用强模型重写提示词，使其适合小模型理解
    rewrite_prompt = [
        {
            "role": "system",
            "content": "你是提示词重写助手，请将以下任务内容优化为更清晰、结构更适合小语言模型理解的自然语言提示词。" +
                    "要求明确字段之间的语义关系，避免使用 Markdown 或 JSON 字符串格式。"
        },
        {
            "role": "user",
            "content": f"""任务：{raw_prompt['task']}

    【个人描述】
    {raw_prompt['profile']}

    【案例报告】
    {raw_prompt['report']}
    """
        }
    ]

    # 使用大模型重写提示词（建议使用 gpt-4o 或 gpt-4-1106-preview）
    optimized_prompt_response = client.chat.completions.create(
        model=model_name,
        messages=rewrite_prompt
    )

    # 获取优化后的提示词内容
    optimized_prompt = optimized_prompt_response.choices[0].message.content
    print(optimized_prompt)
    # Step 2：将优化后的提示词交给小模型执行工具调用（填写 SASS 量表）
    response = client.chat.completions.create(
        model=model_name,  # 小模型
        messages=[
            {"role": "user", "content": optimized_prompt}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "fill_sass"}}
    )

    # Step 3：提取量表答案
    sass = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
 
    return bdi, ghq, sass

# 根据prompt填写量表
def fill_scales(prompt):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    print(prompt)
    # 填写BDI量表
    task_prompt = """# 根据心理咨询对话内容，引导用户完成量表填写任务，并将其答案结构化为指定格式，以调用相应的函数工具
 
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": task_prompt}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}},
        temperature=0
    )
    print(response)
    bdi = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
    # 填写GHQ-28量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"### 任务\n请根据你的情况填写量表。"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}}
    )

    print(response)
    ghq = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
    # 填写SASS量表
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"### 任务\n请根据你的情况填写量表。"}
        ],
        tools = tools,
        tool_choice={"type": "function","function": {"name": "fill_sass"}}
    )
    

    print(1111)
    print(response)
    sass = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
    return bdi, ghq, sass