from openai import OpenAI
import json
from event_trigger import event_trigger

tools = [
    {
        "type": "function",
        "function": {
            'name': 'generate_complaint_chain',
            'description': '根据角色信息和近期遭遇的事件，生成一个患者的主诉请求认知变化链',
            'parameters': {
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "stage": {
                                    "type": "integer"
                                },
                                "content": {
                                    "type": "string"
                                }
                            },
                            "additionalProperties": False,
                            "required": [
                                "stage",
                                "content"
                            ]
                        },
                        "minItems": 3,
                        "maxItems": 7
                        }
                },
                "required": ["chain"]
            },
        }
    }
]

model_name = "complaint"

# 根据profile和event生成主诉启发链
def gen_complaint_chain(profile):
    # 提取患者信息
    patient_info = f"### 患者信息\n年龄：{profile['age']}\n性别：{profile['gender']}\n职业：{profile['occupation']}\n婚姻状况：{profile['martial_status']}\n症状：{profile['symptoms']}"

    event = event_trigger(profile)

    client = OpenAI(
        api_key="complaint_chain",
        base_url="http://0.0.0.0:8001/v1/"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据患者情况及近期遭遇事件生成患者的主诉认知变化链。请注意，事件可能与患者信息冲突，如果发生这种情况，以患者的信息为准。\n{patient_info}\n### 近期遭遇事件\n{event}"}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "generate_complaint_chain"}}
    )

    chain = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["chain"]

    return chain

