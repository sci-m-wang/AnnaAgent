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
    task_prompt1 = (
        "你是一位极其严谨、结构化、格式敏感的心理评估助手，任务是根据用户在咨询对话中表达的心理状态，"
        "判断其在 BDI 抑郁量表中各题目的最贴切选项，并将答案输出为结构化格式。\n\n"

        "**核心任务：**\n"
        "根据用户表达的心理状态与情绪描述，完成 BDI 抑郁自评量表共 21 题的答案选择。每题选项为 A/B/C/D 四选一，"
        "请你根据症状严重程度，从轻到重选出最贴合用户状态的选项。\n\n"

        "**输入信息：**\n"
        "1. 咨询师与来访者的对话文本（系统提供）\n"
        "2. BDI 量表 21 个题目的描述（系统内置）\n\n"

        "**输出格式要求（严格遵守）：**\n"
        "- 输出内容必须是一个 JSON 对象，包含字段：\n"
        "  - `answers`: 一个字符串数组，长度为 21，每项为 'A'、'B'、'C' 或 'D'，分别对应每一道题的选项。\n"
        "- 不允许在 JSON 前后添加任何额外注释、说明或 Markdown 标记（如 ```json）\n"
        "- 保证答案格式完全符合函数调用接口的要求，否则工具无法执行。\n\n"

        "**示例 JSON 输出：**\n"
        "{\n"
        '  "answers": ["A", "B", "A", "C", "D", "B", "A", "C", "B", "A", "D", "C", "B", "A", "B", "C", "B", "A", "D", "C", "B"]\n'
        "}\n\n"

        "**行为守则：**\n"
        "- 严格基于对话内容进行推理，不主观臆测、不胡乱填充。\n"
        "- 若对某题无法确定，请选择最接近的较轻选项（如 B > C）。\n"
        "- 所有题目必须回答，长度必须为 21。\n"
        "- 只返回 JSON，不添加其他语言文字。"
    )


    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": task_prompt1},
            {"role": "user", "content": prompt}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_bdi"}},
        temperature=0
    )
    print(response)
    bdi = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
    # 填写GHQ-28量表
    task_prompt2 =  (
        "你是一位极其严谨、格式敏感、执行精确的心理量表填写助手，专门负责引导用户完成 GHQ-28（一般健康问卷）自评任务。"
        "你的目标是根据用户的心理状况，准确选择每一题的作答选项，并以结构化 JSON 形式输出。"
    
        "**核心任务：**\n"
        "请你根据用户的心理健康状况填写 GHQ-28 量表的所有题目，每道题选择一个最贴近实际感受的选项，选项值为 'A'、'B'、'C' 或 'D'。\n\n"

        "**输入信息：**\n"
        "- 你已知用户的整体心理状态（来源于上文或对话上下文）。\n"
        "- GHQ-28 量表包括 28 道题，涵盖情绪、焦虑、睡眠、人际、躯体等维度。\n\n"

        "**输出格式要求（严格）：**\n"
        "- 输出一个 JSON 对象，包含字段：`answers`。\n"
        "- `answers` 是一个字符串数组，长度必须为 28，数组中的每个元素是一个大写字母：'A'、'B'、'C' 或 'D'。\n"
        "- 严格保持顺序，与题目一致。\n"
        "- **绝不**在 JSON 前后添加任何说明性文字、注释、Markdown 标记或非结构字段。\n\n"

        "**示例输出：**\n"
        "{\n"
        '  "answers": ["B", "B", "C", "A", "D", "C", "B", "B", "B", "A", "B", "C", "A", "D", "C", "A", "B", "B", "C", "A", "B", "C", "B", "D", "A", "B", "C", "B"]\n'
        "}\n\n"

        "**行为要求：**\n"
        "- 严格生成 28 项答案，不可多或少。\n"
        "- 若无足够信息判断，请默认选择 'B'（即中性偏正常）作为保守选项。\n"
        "- 不得输出与 JSON 无关的任何内容。"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": task_prompt2},
            {"role": "user", "content": prompt}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "fill_ghq"}}
    )

    print(response)
    ghq = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
    # 填写SASS量表
    task_prompt3 = (
        "你是一位极其严谨、格式敏感、任务导向的心理健康评估助理，"
        "专门负责根据用户当前的心理与社会行为状况，完成 SASS（社会适应自评量表）的作答任务。\n\n"
        "**你的任务目标如下：**\n"
        "1. 基于系统或对话中已知信息，合理推测用户每一道题目的回答；\n"
        "2. 按照指定格式输出完整答案；\n"
        "3. 遵守格式、长度和选项规则，确保输出能直接被函数工具使用。\n\n"
        "**行为约束（必须严格遵守）：**\n"
        "- 答案必须为长度为 21 的字符串数组；\n"
        "- 每一项答案为 'A'、'B'、'C' 或 'D'，不允许其他值；\n"
        "- 输出格式为纯 JSON，不包含注释、说明或 Markdown；\n"
        "- 不得输出除 `answers` 字段以外的任何内容。\n"
        "- 若某题缺乏判断依据，选择 'B'（中性保守选项）。\n\n"
        "**标准输出示例（禁止包含其他文本）：**\n"
        "{\n"
        '  "answers": ["B", "C", "B", "A", "B", "D", "B", "A", "C", "B", "D", "B", "A", "B", "C", "B", "A", "B", "C", "B", "B"]\n'
        "}\n\n"
        "你必须确保生成的结构完全符合调用要求，否则视为失败执行。"
        "请你根据用户的心理与生活适应状态，填写 SASS（社会适应自评量表）。\n\n"
        "**说明：**\n"
        "SASS 共 21 项，每题选项为 A（无问题）至 D（严重问题）。\n"
        "请根据你的理解，为每题选择最符合用户情况的答案。\n"
        "最终输出一个 JSON 对象，格式如下：\n"
        '{ "answers": ["A", ..., "D"] } （共21项）\n\n'
        "如无充分信息判断某项，请选择 B 作为默认。\n"
        "**禁止输出除 JSON 结构外的任何内容。**"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": task_prompt3},
            {"role": "user", "content": prompt}
        ],
        tools = tools,
        tool_choice={"type": "function","function": {"name": "fill_sass"}}
    )
    
 
    print(response)
    sass = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["answers"]
    return bdi, ghq, sass