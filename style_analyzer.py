from backbone import get_openai_client, model_name
import json

tools = [
    {
        "type": "function",
        "function": {
            'name': 'analyze_style',
            'description': '根据患者的对话记录，分析患者的说话风格。',
            'parameters': {
                "type": "object",
                "properties": {
                    "style": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1,
                        "maxItems": 5
                    }
                },
                "required": ["style"]
            },
        }
    }
]


def analyze_style(profile, conversations):
    client = get_openai_client()
    # 提取患者信息
    patient_info = f"### 患者信息\n年龄：{profile['age']}\n性别：{profile['gender']}\n职业：{profile['occupation']}\n婚姻状况：{profile['martial_status']}\n症状：{profile['symptoms']}"
    # 提取对话记录
    dialogue_history = "\n".join([f"{conv['role']}: {conv['content']}" for conv in conversations])

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据患者情况及咨访对话历史记录分析患者的说话风格。\n{patient_info}\n### 对话记录\n{dialogue_history}"}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "analyze_style"}}
    )
    print(response)
    style = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["style"]
    return style